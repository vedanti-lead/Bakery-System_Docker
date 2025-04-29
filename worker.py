import os
import json
import time
import random
import pika
import psycopg2
from datetime import datetime

# Database connection
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'postgres'),
        database=os.environ.get('DB_NAME', 'bakery'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres')
    )
    conn.autocommit = True
    return conn

# Update order status in database
def update_order_status(order_id, status):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'UPDATE orders SET status = %s WHERE id = %s',
            (status, order_id)
        )
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating order status: {e}")
        return False

# Process the order
def process_order(order_data):
    print(f"Processing order ID: {order_data['order_id']}")
    
    # Simulate order processing time
    processing_time = random.randint(2, 5)
    print(f"Order processing will take {processing_time} seconds...")
    time.sleep(processing_time)
    
    # Update order status to 'processing'
    update_order_status(order_data['order_id'], 'processing')
    
    # Simulate preparation time
    preparation_time = random.randint(3, 8)
    print(f"Order preparation will take {preparation_time} seconds...")
    time.sleep(preparation_time)
    
    # Update order status to 'ready'
    update_order_status(order_data['order_id'], 'ready')
    
    print(f"Order {order_data['order_id']} is now ready for pickup!")
    
    # Here you could add additional logic like sending an email notification

# Message consumer
def start_consuming():
    retry_count = 0
    connection = None
    
    # Keep trying to connect to RabbitMQ
    while retry_count < 10:
        try:
            # Connect to RabbitMQ
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
                    port=5672,
                    credentials=pika.PlainCredentials(
                        os.environ.get('RABBITMQ_USER', 'guest'),
                        os.environ.get('RABBITMQ_PASSWORD', 'guest')
                    )
                )
            )
            break
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            print(f"Failed to connect to RabbitMQ. Retrying in 5 seconds... ({retry_count}/10)")
            time.sleep(5)
    
    if not connection:
        print("Could not connect to RabbitMQ after multiple attempts. Exiting.")
        return
    
    channel = connection.channel()
    
    # Declare the queue
    channel.queue_declare(queue='orders', durable=True)
    
    # Limit to process one message at a time
    channel.basic_qos(prefetch_count=1)
    
    def callback(ch, method, properties, body):
        try:
            order_data = json.loads(body)
            process_order(order_data)
            # Acknowledge the message
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            print(f"Error processing message: {e}")
            # Nack the message so it gets requeued
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    # Start consuming messages
    channel.basic_consume(queue='orders', on_message_callback=callback)
    
    print("Worker started. Waiting for orders...")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    
    connection.close()

if __name__ == '__main__':
    # Wait for RabbitMQ and PostgreSQL to be ready
    time.sleep(10)
    start_consuming()