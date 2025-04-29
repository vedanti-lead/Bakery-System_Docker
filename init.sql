CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Insert some sample products
INSERT INTO products (name, description, price, image_url) VALUES
('Chocolate Cake', 'Rich chocolate layer cake with ganache', 29.99, 'https://www.bbc.co.uk/food/recipes/easy_chocolate_cake_31070'),
('Sourdough Bread', 'Artisanal sourdough bread', 8.99, 'https://cookidoo.co.uk/recipes/recipe/en-GB/r643607'),
('Blueberry Muffin', 'Moist muffin loaded with blueberries', 3.99, 'https://www.wildernesswife.com/blog/2019/08/04/jordan-marsh-blueberry-muffin-recipe/'),
('Croissant', 'Buttery, flaky French pastry', 4.50, 'https://www.istockphoto.com/photos/butter-croissant');