# Event Trigger Platform

A scalable event trigger platform that supports scheduled and API-based triggers with event logging and monitoring capabilities.

## Acknowledgments

This project was developed with the assistance of several AI tools:

- [Cursor.ai](https://cursor.ai/) - AI-powered code editor that provided intelligent code suggestions and completions
- [ChatGPT](https://chat.openai.com) - Helped with code review, debugging, and architectural decisions
- [Claude](https://anthropic.com/claude) - Assisted with documentation writing and API design

These AI tools significantly enhanced the development process and helped create a more robust and well-documented solution.

## Live Demo

The application is deployed on Vercel at: https://y-d3q1rf5z4-shreeshas-projects-779b213d.vercel.app/

## Features

- Scheduled and API-based triggers
- Event logging and monitoring
- Real-time event tracking
- Event archival system
- REST API endpoints
- Containerized deployment
- MongoDB integration

## Local Setup

### Prerequisites

- Docker and Docker Compose
- Git

### Running Locally

1. Clone the repository:
bash
git clone https://github.com/ShreeshaPradeep/event-trigger-platform
cd event-trigger-platform


2. Create a `.env` file in the root directory:
env
MONGODB_URL=mongodb+srv://your-mongodb-url
DATABASE_NAME=event_triggers
ENVIRONMENT=development

3. Build and run using Docker Compose:
bash
docker-compose up --build

The application will be available at `http://localhost:8000`

## API Documentation

### 1. Create Trigger
bash

POST /api/v1/triggers/

API Trigger Example
{
"name": "Sample API Trigger",
"description": "Test API trigger",
"trigger_type": "api",
"api_config": {
"endpoint": "https://api.example.com/webhook",
"method": "POST",
"payload_schema": {
"message": "string",
"priority": "number"
}
}
}

Scheduled Trigger Example

{
"name": "Daily Report",
"description": "Runs daily at 9 AM",
"trigger_type": "scheduled",
"schedule_config": {
"schedule_type": "recurring",
"interval_type": "days",
"interval_value": 1,
"specific_time": {
"hour": 9,
"minute": 0
}
}
}
Response
{
"trigger_id": "507f1f77bcf86cd799439011"
}

### 2. Execute Trigger

bash
POST /api/v1/triggers/{trigger_id}/execute
Request Body
{
"message": "Test execution",
"priority": 1
}
Response
{
"message": "Trigger executed successfully",
"event_id": "507f1f77bcf86cd799439012"
}

### 3. Get Recent Events
bash
GET /api/v1/events/recent
Response
[
{
"id": "507f1f77bcf86cd799439013",
"trigger_id": "507f1f77bcf86cd799439011",
"trigger_name": "Sample API Trigger",
"execution_time": "2024-01-01T12:00:00Z",
"status": "success",
"payload": {
"message": "Test execution",
"priority": 1
}
}
]

## Cost Analysis (30 days, 5 queries/day)

### Free Tier Resources:
- Vercel Hobby Plan (Free)
- MongoDB Atlas Free Tier
- Docker Hub Free Tier

### Monthly Usage:
- API Calls: 5 queries/day × 30 days = 150 calls/month
- Database Storage: ~100MB
- Container Registry: 1 repository

### Total Cost: $0/month
All services used are within free tier limits:
- Vercel: Free for hobby projects
- MongoDB Atlas: Free tier includes 512MB storage
- Docker Hub: Free for public repositories

## Architecture

The application uses:
- FastAPI for the backend API
- MongoDB for data storage
- APScheduler for scheduled tasks
- Docker for containerization
- Vercel for deployment

## Testing

Run tests using Docker:
bash
docker-compose run app pytest


## Limitations

Free tier limitations:
- Vercel: Cold starts on serverless functions
- MongoDB Atlas: 512MB storage limit
- Limited concurrent connections
- Basic monitoring features only



