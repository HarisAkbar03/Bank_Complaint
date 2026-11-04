# Banking Complaint Management API

## Overview

A FastAPI application connected to PostgreSQL using SQLAlchemy ORM. The API provides liveness and readiness endpoints for application health monitoring.

## Requirements

- Python 3.10+
- PostgreSQL
- pip

## Installation

```powershell
python -m pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file with the following variables:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

## Run the Application

```powershell
python -m uvicorn main:app --reload
```

API: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

## Health Endpoints

### GET /health/live

Returns HTTP 200 when the API is running.

```json
{"status": "alive"}
```

### GET /health/ready

Returns HTTP 200 when PostgreSQL is accessible:

```json
{
  "status": "ready",
  "database": "connected"
}
```

Returns HTTP 503 when PostgreSQL is unavailable.

## Verification

1. Start PostgreSQL and FastAPI.
2. Confirm both health endpoints return HTTP 200.
3. Stop PostgreSQL.
4. Confirm liveness continues returning HTTP 200.
5. Confirm readiness returns HTTP 503.
6. Restart PostgreSQL and verify readiness returns HTTP 200 again.