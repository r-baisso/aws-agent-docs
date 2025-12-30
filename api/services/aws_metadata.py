import requests

# Curated list of popular AWS services
# This list can be expanded. The key is the service name used in the URL.
AWS_SERVICES = []

def get_service_toc_url(service_name: str) -> str:
    """Constructs the TOC URL for a given service."""
    return f"https://docs.aws.amazon.com/{service_name}/latest/userguide/toc-contents.json"

def validate_service(service_name: str) -> (bool, str):
    """
    Checks if the service documentation exists by trying to fetch its TOC.
    """
    url = get_service_toc_url(service_name)
    try:
        response = requests.head(url, timeout=5)

        url_developer = f"https://docs.aws.amazon.com/{service_name}/latest/developerguide/toc-contents.json"
        response_developer = requests.head(url_developer, timeout=5)
        
        url_dev = f"https://docs.aws.amazon.com/{service_name}/latest/devguide/toc-contents.json"
        response_dev = requests.head(url_dev, timeout=5)
        
        
        if response.status_code == 200:
            return True, url
        if response_developer.status_code == 200:
            return True, url_developer
        if response_dev.status_code == 200:
            return True, url_dev
        
        return False, None
    except Exception as e:
        print(f"Validation error for {service_name}: {e}")
        return False, None

import xml.etree.ElementTree as ET
import re

_CACHED_SERVICES = []

def fetch_online_services() -> list[str]:
    """
    Dynamically discovers AWS services from the official sitemap.
    """
    url = "https://docs.aws.amazon.com/sitemap_index.xml"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            return []
            
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        services = set()
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace).text
            match = re.search(r'https://docs\.aws\.amazon\.com/([^/]+)/latest/', loc)
            if match:
                services.add(match.group(1))
                
        return sorted(list(services))
    except Exception as e:
        print(f"Error fetching online services: {e}")
        return []

def get_available_services() -> list[str]:
    """Returns the list of services, preferring dynamic discovery."""
    global _CACHED_SERVICES
    
    if _CACHED_SERVICES:
        return _CACHED_SERVICES
        
    discovered = fetch_online_services()
    if discovered:
        _CACHED_SERVICES = discovered
        return _CACHED_SERVICES
        
    return sorted(AWS_SERVICES)
