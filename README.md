# GeoIP2-python Service

This is a FastAPI-based service that provides GeoIP lookup functionality with support for both English and Arabic languages. The service uses MaxMind's GeoLite2 databases and provides various endpoints for IP geolocation queries. The service also includes MCP (Model Context Protocol) support for integration with AI tools and agents.

## Prerequisites

Before running the service, make sure you have Python installed.

## Installation and Setup

### 1. Create a Virtual Environment (Recommended)

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Required packages:
- fastapi==0.110.1
- uvicorn==0.29.0
- geoip2==4.7.0
- fastmcp>=2.9.0
- mmdb-writer==0.2.5
- netaddr>=0.7

## Running the Service

### Main GeoIP Service

To run the main service, use the following command:

```bash
# Using uvicorn (recommended)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

```

The service will be available at `http://localhost:8000`

### MCP Layer Service

To run the MCP layer separately:

```bash
python mcp_layer.py
```

The MCP service will be available at `http://localhost:8001/sse`

## API Endpoints

### 1. Get Current IP
- **Endpoint:** `GET /ip`
- **Description:** Returns the IP address of the current request
- **Example Response:**
```json
{
    "your_ip": "127.0.0.1"
}
```

### 2. Get GeoIP Information
- **Endpoint:** `GET /ip/{input_ip}`
- **Description:** Returns detailed geographic information for a specific IP address
- **Example:** `GET /ip/188.54.109.98`
- **Example Response:**
```json
{
    "ip": "188.54.109.98",
    "ip_version": "IPv4",
    "generatedAt": "2025-07-03T16:03:49.226189",
    "country": {
        "iso_code": "SA",
        "en": "Saudi Arabia",
        "ar": "السعودية"
    },
    "continent": {
        "code": "AS",
        "en": "Asia",
        "ar": "آسيا"
    },
    "location": {
        "latitude": "24.6869",
        "longitude": "46.7224",
        "postal_code": null
    },
    "map": "https://www.google.com/maps/@24.6869,46.7224,15z",
    "city": {
        "en": "Riyadh",
        "ar": "منطقة الرياض"
    }
}
```

### 3. List IP Networks
- **Endpoint:** `GET /ipall`
- **Description:** Returns the first 100 IP networks with full details in English and Arabic
- **Example Response:**
```json
{
    "ip_networks": [
        {
            "network": "1.0.0.0/24",
            "country": {
                "id": "2077456",
                "iso_code": "AU",
                "en": "Australia",
                "ar": "أستراليا"
            },
            "city": {
                "id": "2147714",
                "en": "Sydney",
                "ar": "سيدني"
            },
            "continent": {
                "code": "OC",
                "en": "Oceania",
                "ar": "أوقيانوسيا"
            }
        }
    ]
}
```

### 4. Rebuild MMDB Database
- **Endpoint:** `POST /geoip/rebuild`
- **Description:** Rebuilds the MMDB database file from CSV blocks and Arabic labels
- **Example Response:**
```json
{
    "status": "success",
    "message": "MMDB file rebuilt with 12345 records."
}
```

## Database Files

The service uses several database files stored in the `db/` directory:
- GeoLite2-City-Locations.csv
- GeoLite2-City-Blocks-IPv4.csv
- GeoLite2-City-Custom.mmdb

## Features

- Bilingual support (English and Arabic)
- IP version detection
- Detailed geographic information
- Google Maps integration
- Custom MMDB database rebuilding
- FastAPI-powered API documentation
- MCP (Model Context Protocol) support for AI tool integration

## API Documentation

Once the service is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Error Handling

The service includes comprehensive error handling for:
- Invalid IP addresses
- Missing database entries
- Database rebuild errors
- Network-related issues

## MCP Layer Support

This project includes an MCP (Model Context Protocol) layer that exposes GeoIP functionality as tools for AI agents and other MCP-compatible systems. The MCP layer is implemented in `mcp_layer.py` and can be run separately:

```bash
python mcp_layer.py
```

The MCP HTTP API will be available at `http://localhost:8001/sse` and provides:
- GeoIP lookup tools
- Database rebuild tools
- Integration with AI agents and MCP-compatible systems

### Testing MCP Tools with Postman

You can test the MCP tools using HTTP POST requests:

**Lookup GeoIP Tool:**
- Endpoint: `http://localhost:8001/mcp/tools/lookup_geoip`
- Body: `{"ip": "8.8.8.8"}`

**Rebuild Database Tool:**
- Endpoint: `http://localhost:8001/mcp/tools/rebuild_database`
- Body: `{}` (empty JSON)

## Development

The service is built with FastAPI for optimal performance and includes auto-reload functionality during development. The `--reload` flag in the run command enables automatic reloading when code changes are detected.

## License

This project uses GeoLite2 data created by MaxMind, available from [https://www.maxmind.com](https://www.maxmind.com).
