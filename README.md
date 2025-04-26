# Travel Booking Agent API

A web-to-API conversion agent that allows other AI agents to interact with travel booking websites like Expedia.

## Overview

This system enables AI agents to interact with complex travel booking websites through a clean API interface. It handles the complexity of website navigation, form filling, and data extraction, providing structured data that other AI systems can easily consume.

## Features

- Headless browser automation using Playwright
- Website structure mapping and navigation
- Form interaction and data extraction capabilities
- RESTful API interface for AI agents
- Natural language understanding for processing AI agent requests

## Core Booking Flows

- Flight search and results extraction
- Hotel search and results extraction
- Basic booking process navigation

## Getting Started

### Prerequisites

- Python 3.8+
- Playwright
- FastAPI
- Other dependencies listed in requirements.txt

### Installation

1. Clone the repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
python -m playwright install
```

4. Create a .env file based on .env.example

### Running the API

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, visit http://localhost:8000/docs for the interactive API documentation.

### Key Endpoints

#### Flight Search

- `POST /api/flights/search` - Start a flight search
- `GET /api/flights/search/{request_id}` - Get flight search results

#### Hotel Search

- `POST /api/hotels/search` - Start a hotel search
- `GET /api/hotels/search/{request_id}` - Get hotel search results

#### Natural Language Processing

- `POST /api/nlu/process` - Process natural language requests

## Architecture

The system consists of the following components:

1. **Browser Manager** - Manages browser instances and provides browser contexts
2. **Base Browser Actions** - Common browser interaction methods
3. **Website-specific Browsers** - Website-specific interaction logic (e.g., ExpediaFlightBrowser)
4. **API Layer** - FastAPI routes and endpoints
5. **Data Models** - Pydantic models for request/response validation
6. **NLU Processor** - Natural language understanding for processing AI agent requests

## Error Handling

The system includes comprehensive error handling:

- Browser navigation errors
- Timeouts and element not found scenarios
- Request validation errors
- Background task processing errors

## Testing

Run the tests using pytest:

```bash
python -m pytest
```

## Extending the System

To support additional travel websites:

1. Create a new browser class in `browsers/[website_name]/`
2. Implement the website-specific navigation and extraction logic
3. Update the API routes to use the new browser class

## License

This project is licensed under the MIT License - see the LICENSE file for details.
