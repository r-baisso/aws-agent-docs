import requests
import re
import xml.etree.ElementTree as ET

def discover_services():
    url = "https://docs.aws.amazon.com/sitemap_index.xml"
    try:
        print(f"Fetching sitemap from {url}...")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            return []

        # Parse XML
        root = ET.fromstring(response.content)
        # Namespace is usually http://www.sitemaps.org/schemas/sitemap/0.9
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        services = set()
        
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace).text
            # Example: https://docs.aws.amazon.com/acm/latest/userguide/sitemap.xml
            # Pattern: https://docs.aws.amazon.com/([^/]+)/latest/
            
            match = re.search(r'https://docs\.aws\.amazon\.com/([^/]+)/latest/', loc)
            if match:
                service = match.group(1)
                services.add(service)
            else:
                 # Try matching without 'latest' if needed, or nested like ai/responsible-ai
                 # But our scraper expects {service}/latest/..., so we only want those matching that pattern
                 pass

        print(f"Found {len(services)} unique services.")
        sorted_services = sorted(list(services))
        print(sorted_services[:20]) # Print first 20
        return sorted_services

    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    discover_services()
