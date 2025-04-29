Design Decisions for the Bakery System
1️⃣ Microservices Architecture with Docker Compose
Why: To isolate each component (frontend, backend, DB, cache, queue, worker) for better scalability, flexibility, and maintainability.

Decision: Use Docker Compose to orchestrate multiple services with individual responsibilities.

2️⃣ React Frontend
Why: React is a lightweight, component-based library ideal for dynamic UIs.

Decision: Built a SPA (Single Page App) for smooth user experience, real-time cart management, and fast navigation without reloads.

3️⃣ Flask Backend (API Server)
Why: Flask is lightweight and easy to integrate with PostgreSQL, Redis, and RabbitMQ.

Decision: Acts as a REST API server with 3 endpoints (products, place order, order status). Uses caching and queuing for efficiency.

4️⃣ PostgreSQL as Primary Database
Why: PostgreSQL is reliable, ACID-compliant, and supports structured relationships between tables (orders, order_items, products).

Decision: Used it to store all persistent transactional data (product catalog, orders, customer info).

5️⃣ Redis for Caching
Why: Redis is fast (in-memory) and helps reduce load on PostgreSQL.

Decision: Cached product listings for 5 minutes and order statuses for 30 seconds to optimize performance and reduce latency.

6️⃣ RabbitMQ for Asynchronous Processing
Why: Decouples real-time customer interactions from slower backend tasks (order preparation).

Decision: Orders are sent to RabbitMQ, then processed by a separate worker to simulate real bakery flow.

7️⃣ Python Worker Service
Why: Keeps backend fast and responsive. Simulates processing time realistically.

Decision: Worker listens to RabbitMQ, simulates baking delays, updates order status in DB — improving user experience and realism.

8️⃣ Docker & Volumes
Why: Containers ensure portability and isolation; volumes persist data.

Decision: Docker used for every service. Volumes used for PostgreSQL, Redis, and RabbitMQ to avoid data loss across reboots.

9️⃣ Health Checks & Retry Logic
Why: Ensures services are reliable and self-healing.

Decision: Health checks added for backend, Redis, RabbitMQ, PostgreSQL. Retry logic used for queue connections.
