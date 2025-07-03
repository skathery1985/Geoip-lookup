#!/usr/bin/env python3
"""
Hello World FastMCP Server
A simple demonstration of FastMCP server capabilities with greeting and echo tools.
"""

from fastmcp import FastMCP
import main
# Create the FastMCP server
app = FastMCP("Hello World FastMCP Server")

@app.prompt()
def prompt_find_geo(ip_address: str) -> str:
    """Generate a prompt template for analyzing GeoIP data.
    
    Args:
        ip_address: The IP address to analyze
    
    Returns:
        A prompt template for AI models to analyze GeoIP information
    """
    geo_data = main.find_geo(ip_address)
    
    prompt_template = f"""
Analyze the following GeoIP information for IP address {geo_data}:

Geographic Data:
- Country: 
- City: 
- Continent: 
- Location: 
- IP Version: 

Please provide insights about:
1. The geographic location and its significance
2. Potential security considerations for this IP
3. Network infrastructure observations
4. Any notable patterns or anomalies

Format your response in a clear, structured manner with both English and Arabic context where relevant.
"""
    
    return prompt_template


@app.tool()
def tool_find_geo(ip_address: str) -> dict:
    """Find geographic information for an IP address.
    
    Args:
        ip_address: The IP address to lookup
    
    Returns:
        Geographic information including country, city, continent, and location data
    """
    return main.find_geo(ip_address)


if __name__ == "__main__":
    # Run the server with HTTP transport
    app.run(transport="sse", host="localhost", port=8001)
