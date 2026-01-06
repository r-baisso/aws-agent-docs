import requests

# Curated list of popular AWS services
# This list can be expanded. The key is the service name used in the URL.
AWS_SERVICES = []


import xml.etree.ElementTree as ET
import re

_CACHED_SERVICES_MAP = {}

def fetch_online_services() -> dict[str, str]:
    """
    Dynamically discovers AWS services from the official sitemap index.
    Returns a dict mapping service_name -> sitemap_url.
    Prioritizes 'userguide' over 'developerguide'.
    """
    url = "https://docs.aws.amazon.com/sitemap_index.xml"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
            
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Map service -> sitemap_url
        # We need to handle priorities: userguide > developerguide
        found_services = {} 
        
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace).text
            
            # We are looking for .../latest/userguide/sitemap.xml or .../latest/developerguide/sitemap.xml
            # Regex to capture service name and type
            # Example: https://docs.aws.amazon.com/AmazonS3/latest/userguide/sitemap.xml
            match = re.search(r'https://docs\.aws\.amazon\.com/([^/]+)/latest/(userguide|developerguide|devguide)/sitemap\.xml', loc)
            
            if match:
                service_name = match.group(1)
                guide_type = match.group(2)
                
                # If we haven't seen this service yet, or if this is a userguide (preferred), store it
                if service_name not in found_services:
                    found_services[service_name] = loc
                elif guide_type == "userguide":
                    found_services[service_name] = loc
        
        return found_services
    except Exception as e:
        print(f"Error fetching online services: {e}")
        return {}

def get_available_services() -> list[str]:
    """Returns the list of available service names."""
    global _CACHED_SERVICES_MAP
    
    if not _CACHED_SERVICES_MAP:
        _CACHED_SERVICES_MAP = fetch_online_services()
    
    return sorted(list(_CACHED_SERVICES_MAP.keys()))

def get_service_sitemap_url(service_name: str) -> str:
    """Returns the cached sitemap URL for a service, or None."""
    global _CACHED_SERVICES_MAP
    if not _CACHED_SERVICES_MAP:
        _CACHED_SERVICES_MAP = fetch_online_services()
    return _CACHED_SERVICES_MAP.get(service_name)
