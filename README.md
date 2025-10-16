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
