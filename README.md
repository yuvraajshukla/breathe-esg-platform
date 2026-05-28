# Breathe ESG Platform

A full-stack ESG emissions ingestion and review platform built using Django REST Framework and React.

## Features

* Upload ESG CSV files (SAP / Utility / Travel)
* Automatic emission record normalization
* Suspicious activity detection
* Approve / Reject workflow
* Audit log tracking
* Django Admin panel
* REST API backend
* React dashboard frontend

## Tech Stack

### Backend

* Django
* Django REST Framework
* SQLite
* Pandas

### Frontend

* React
* Vite
* Axios

---

## Project Structure

backend/breathe-esg → Django backend

frontend → React frontend

---

## Setup Instructions

### Backend

```bash
cd backend/breathe-esg
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

### Upload CSV

POST `/api/upload/sap/`

POST `/api/upload/utility/`

POST `/api/upload/travel/`

### Records

GET `/api/records/`

### Review Record

PATCH `/api/review/<id>/`

---

## Admin Panel

```text
http://127.0.0.1:8000/admin/
```

---

## Author

Yuvraaj Shukla
