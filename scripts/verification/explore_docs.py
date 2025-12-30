import requests
from bs4 import BeautifulSoup

url = "https://docs.aws.amazon.com/"
try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Look for links that might point to services
        # Usually they are in a grid or list
        links = soup.find_all('a', href=True)
        print(f"Found {len(links)} links.")
        
        # Filter for potential service links
        # They often look like /service-name/ or https://docs.aws.amazon.com/service-name/
        service_links = []
        for a in links:
            href = a['href']
            text = a.get_text(strip=True)
            if text and (href.startswith("/") or "docs.aws.amazon.com" in href):
                service_links.append(f"{text} -> {href}")
        
        print("Potential service links (first 20):")
        for link in service_links[:20]:
            print(link)
            
    else:
        print(f"Failed to fetch {url}: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
