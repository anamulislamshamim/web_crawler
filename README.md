# Async Book Crawler API

An **async, modular FastAPI project** to crawl book data, store it in MongoDB, and expose APIs for book retrieval and change logs.  
Supports **daily scheduling**, **API key-based authentication**, **rate limiting**, and **modular routers** for scalability.

---

## Author

**Shamim**  
Remote Backend Engineer (Mid)  
Short Circuit Science, London, UK  
[LinkedIn Profile](https://www.linkedin.com/in/anamul-islam-shamim/)

---

---

## Table of Contents

- [Features](#features)  
- [Setup Instructions](#setup-instructions)  
- [Python Version & Dependencies](#python-version--dependencies)  
- [Environment Variables (.env)](#environment-variables-env)  
- [API Endpoints](#api-endpoints)  
- [Site Keys & Authentication](#site-keys--authentication) 

---

## Features

This project is a **production-ready content aggregation system** designed to crawl, monitor, and serve book data from a sample e-commerce website.  

### 1. Scalable and Robust Web Crawler
- Crawl **all book-related information** and store it in MongoDB.
- Collected data includes:
  - Name, description, and category of the book  
  - Prices (including and excluding taxes)  
  - Availability status  
  - Number of reviews  
  - Book cover image URL  
  - Rating  
- Store metadata for each book: **crawl timestamp, status, source URL, raw HTML snapshot**.  
- **Async programming** with `httpx` ensures fast and efficient crawling.  
- **Retry logic** and **resumable crawls** handle transient failures.  
- MongoDB schema optimized for **efficient querying and deduplication**.  
- Book data modeled using **Pydantic schemas** for validation and consistency.  

### 2. Scheduler and Change Detection
- **Daily scheduler** detects newly added books and inserts them into the database.  
- **Change detection** compares stored book data with the website to update changes (e.g., price or availability).  
- Maintains a **change log** in MongoDB for tracking all updates.  
- Option to **generate daily change reports** in JSON or CSV format.  
- Optimized detection using **content hashing or fingerprinting**.  
- Logging and alerting system for significant changes or new books.  
- Scheduler supports **APScheduler**.  

### 3. RESTful API
- Modular FastAPI routers for `/books`, `/changes` and `/crawler`.  
- Endpoints with **filtering, pagination, and sorting** for book data.  
- **API key-based authentication** for secure access.  
- **Rate limiting** to prevent abuse.  
- OpenAPI/Swagger documentation for easy API exploration.  

### 4. Production-Ready Architecture
- Modular codebase for **scalability and maintainability**.  
- Proper configuration via `.env` files.  
- Full **test coverage** for crawlers, APIs, and database operations.  
- Logging for monitoring crawler performance and system health.  

---

## Setup Instructions

1. **Clone the repository**
```bash
git clone https://github.com/anamulislamshamim/web_crawler.git
cd web_crawler
````

2. **Create a Python virtual environment**

```bash
python3.8 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
   Copy `.env.example` to `.env` and edit values if needed.

5. **Run the FastAPI app**

```bash
uvicorn app.main:app --reload
```

6. **Access Swagger docs**

**Swigger API Documentation (Please visit after run the project successfully in your local machine)**
```bash
http://127.0.0.1:8000/docs

```

---
## Python Version & Dependencies

* Python **3.8.2**
* Key dependencies (full list in `requirements.txt`):

  * fastapi==0.119.0
  * httpx==0.28.1
  * motor==3.6.1
  * APScheduler==3.11.0
  * pymongo==4.9.2
  * pytest==8.3.5
  * pytest-asyncio==0.24.0

---

## Environment Variables (.env)

```dotenv
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=book_crawler

# Crawler Configuration
SITE_KEY=books_toscrape

# Scheduler Configuration
SCHEDULER_TIMEZONE=Asia/Dhaka
SCHEDULER_INTERVAL_MINUTES=1440  # 1 day (24 hours)

# API Key
API_KEY_NAME=web_crawler_9a0d2e8f27d6a4b2f3a1c9eb4d7a2f15
```

---

## API Endpoints

### Health Check

```
GET /health
```

### Crawler Endpoints

```
POST /crawler/start/{site_key}    # Start crawling
POST /crawler/resume/{site_key}   # Resume crawling
POST /crawler/stop/{site_key}     # Stop crawling
GET  /crawler/status/{site_key}   # Check crawler status
```

### Books Endpoints

```
GET /books                        # List books with pagination, filters, sorting
GET /books/{book_id}               # Get book details by ID
```

### Changes Endpoints

```
GET /changes/report                # View recent updates or change logs
```

---

## Site Keys & Authentication

* **SITE_KEY**: `books_toscrape`
* **API key-based authentication**: provide the following HTTP header:

```http
x-api-key: web_crawler_9a0d2e8f27d6a4b2f3a1c9eb4d7a2f15
```

---
## Testing
```bash
pytest -v
```
---

## Further Improvement Proposals  

- Implement **distributed rate limiting** using Redis for scalability.  
- Containerize the application with **Docker** and add CI/CD pipelines.  
- Enhance **logging, monitoring, and alerting** with tools like Grafana or ELK Stack.  
- Use **Celery workers** for distributed and parallel crawling.  
- Strengthen **security and configuration management** using secrets vaults.  
- Add **analytics and reporting dashboards** for crawl and change insights.  

---

## 🙏 Thank You  

Thank you for taking the time to review my assignment.  
I truly appreciate the opportunity to demonstrate my skills and approach to designing scalable, production-ready Python applications.
