````markdown
# Async Book Crawler API

An **async, modular FastAPI project** to crawl book data, store it in MongoDB, and expose APIs for book retrieval and change logs.  
Supports **daily scheduling**, **API key-based authentication**, **rate limiting**, and **modular routers** for scalability.

---

## Table of Contents

- [Features](#features)  
- [Setup Instructions](#setup-instructions)  
- [Python Version & Dependencies](#python-version--dependencies)  
- [Environment Variables (.env)](#environment-variables-env)  
- [API Endpoints](#api-endpoints)  
- [Site Keys & Authentication](#site-keys--authentication)  
- [License](#license)  

---

## Features

- Async crawling using `httpx` and async concurrency  
- MongoDB integration (NoSQL storage) with raw HTML snapshots  
- Daily scheduler to detect new books and changes  
- Change log and daily change reports (JSON/CSV)  
- API endpoints for books, changes, and crawler control  
- API key-based authentication & in-memory rate limiting  
- Modular routers for `/crawler` and `/books`  
- OpenAPI/Swagger documentation available via FastAPI  

---

## Setup Instructions

1. **Clone the repository**
```bash
git clone <repo_url>
cd <repo_name>
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

```
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