import os
import json
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import pika
import redis
import json

app = Flask(__name__)
CORS(app)

# Redis connection
def get_redis_connection():
    return redis.Redis(
        host=os.environ.get('REDIS_HOST', 'redis'),
        port=6379,
        db=0,
        decode_responses=True
    )

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

# RabbitMQ connection
def get_rabbitmq_connection():
    retry_count = 0
    while retry_count < 5:
        try:
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
            return connection
        except pika.exceptions.AMQPConnectionError:
            retry_count += 1
            print(f"Failed to connect to RabbitMQ. Retrying ({retry_count}/5)...")
            time.sleep(5)
    
    print("Could not connect to RabbitMQ after 5 attempts")
    return None

# Send message to queue
def send_to_queue(message):
    connection = get_rabbitmq_connection()
    if connection:
        channel = connection.channel()
        channel.queue_declare(queue='orders', durable=True)
        channel.basic_publish(
            exchange='',
            routing_key='orders',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            )
        )
        connection.close()
        return True
    return False

# API Endpoints
@app.route('/api/products', methods=['GET'])
def get_products():
    # Try to get products from Redis cache first
    redis_client = get_redis_connection()
    cached_products = redis_client.get('products')
    
    if cached_products:
        print("Returning products from cache")
        return jsonify(json.loads(cached_products))
    
    # If not in cache, get from database
    print("Cache miss! Fetching products from database")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name, description, price, image_url FROM products')
    products = []
    for row in cur.fetchall():
        products.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'price': float(row[3]),
            'image_url': row[4]
        })
    cur.close()
    conn.close()
    
    # Store in cache with expiration (5 minutes)
    redis_client.setex('products', 300, json.dumps(products))
    
    return jsonify(products)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    
    if not data or 'customer_name' not in data or 'customer_email' not in data or 'items' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create the order
    cur.execute(
        'INSERT INTO orders (customer_name, customer_email) VALUES (%s, %s) RETURNING id',
        (data['customer_name'], data['customer_email'])
    )
    order_id = cur.fetchone()[0]
    
    # Add order items
    for item in data['items']:
        cur.execute(
            'INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)',
            (order_id, item['product_id'], item['quantity'], item['price'])
        )
    
    # Send to message queue for processing
    order_data = {
        'order_id': order_id,
        'customer_name': data['customer_name'],
        'customer_email': data['customer_email'],
        'items': data['items']
    }
    queue_result = send_to_queue(order_data)
    
    conn.commit()
    cur.close()
    conn.close()
    
    # Invalidate products cache since inventory might have changed
    redis_client = get_redis_connection()
    redis_client.delete('products')
    
    return jsonify({
        'order_id': order_id, 
        'status': 'pending',
        'queue_status': 'sent to processing queue' if queue_result else 'queuing failed'
    })

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order_status(order_id):
    # Try to get from cache first
    redis_client = get_redis_connection()
    cache_key = f'order:{order_id}'
    cached_order = redis_client.get(cache_key)
    
    if cached_order:
        return jsonify(json.loads(cached_order))
    
    # If not in cache, get from database
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute('SELECT id, customer_name, status, created_at FROM orders WHERE id = %s', (order_id,))
    order = cur.fetchone()
    
    if not order:
        cur.close()
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    
    cur.execute('SELECT p.name, oi.quantity, oi.unit_price FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = %s', (order_id,))
    items = []
    for item in cur.fetchall():
        items.append({
            'product_name': item[0],
            'quantity': item[1],
            'unit_price': float(item[2]),
            'total': float(item[1] * item[2])
        })
    
    cur.close()
    conn.close()
    
    # Prepare order data
    order_data = {
        'order_id': order[0],
        'customer_name': order[1],
        'status': order[2],
        'created_at': order[3].strftime('%Y-%m-%d %H:%M:%S'),
        'items': items
    }
    
    # Cache for a short period (30 seconds) as order status might change
    redis_client.setex(cache_key, 30, json.dumps(order_data))
    
    return jsonify(order_data)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    health = {'status': 'ok', 'services': {}}
    
    # Check database connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        health['services']['database'] = 'healthy'
    except Exception as e:
        health['services']['database'] = f'unhealthy: {str(e)}'
        health['status'] = 'degraded'
    
    # Check RabbitMQ connection
    try:
        connection = get_rabbitmq_connection()
        if connection:
            connection.close()
            health['services']['rabbitmq'] = 'healthy'
        else:
            health['services']['rabbitmq'] = 'unhealthy: connection failed'
            health['status'] = 'degraded'
    except Exception as e:
        health['services']['rabbitmq'] = f'unhealthy: {str(e)}'
        health['status'] = 'degraded'
    
    # Check Redis connection
    try:
        redis_client = get_redis_connection()
        if redis_client.ping():
            health['services']['redis'] = 'healthy'
        else:
            health['services']['redis'] = 'unhealthy: ping failed'
            health['status'] = 'degraded'
    except Exception as e:
        health['services']['redis'] = f'unhealthy: {str(e)}'
        health['status'] = 'degraded'
    
    return jsonify(health)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)