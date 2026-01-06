import requests
from bs4 import BeautifulSoup
import os
from api.core.config import settings

import requests
from bs4 import BeautifulSoup
import os
import json
import time
from markdownify import markdownify as md
from api.core.config import settings
from api.services.aws_metadata import get_service_sitemap_url
import logging

logger = logging.getLogger(__name__)


def scrape_page(url):
    """Scrape a single page and return the Markdown content."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            # AWS docs main content is usually in #main-col-body
            main_content = soup.find('div', id='main-col-body')
            if main_content:
                # Convert HTML to Markdown
                return md(str(main_content), heading_style="ATX")
            else:
                # Fallback to body if main content not found
                return md(str(soup.body), heading_style="ATX")
        else:
            logger.warning(f"Failed to fetch {url}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        return None

from concurrent.futures import ThreadPoolExecutor

import json
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.services.aws_metadata import get_service_sitemap_url

def get_sitemap_urls(sitemap_content):
    """Extract page URLs from a sitemap XML."""
    urls = []
    try:
        root = ET.fromstring(sitemap_content)
        # Sitemaps use a namespace usually
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            if loc is not None and loc.text:
                urls.append(loc.text)
    except Exception as e:
        logger.error(f"Error parsing sitemap XML: {e}")
    return urls

def scrape_aws_docs(service_list: list[str], limit: int = None, max_jobs: int = 4):
    # Yields JSON strings for progress updates
    
    # Ensure max_jobs is reasonable
    if max_jobs < 1: max_jobs = 1
    if max_jobs > 20: max_jobs = 20

    for service in service_list:
        yield json.dumps({"type": "log", "message": f"Locating sitemap for: {service}..."})
        
        # 1. Get Sitemap URL from Metadata
        sitemap_url = get_service_sitemap_url(service)
        
        if not sitemap_url:
            logger.warning(f"Sitemap for {service} not found in index.")
            yield json.dumps({"type": "error", "service": service, "message": "Sitemap not found in AWS index."})
            continue

        yield json.dumps({"type": "log", "message": f"Found sitemap: {sitemap_url}"})
        logger.info(f"Fetching Sitemap from {sitemap_url}...")
        
        try:
            # 2. Fetch Sitemap XML
            response = requests.get(sitemap_url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch sitemap: {response.status_code}")
                yield json.dumps({"type": "error", "service": service, "message": f"Failed to fetch sitemap (HTTP {response.status_code})."})
                continue
                
            # 3. Parse URLs
            page_urls = get_sitemap_urls(response.content)
            
            # Deduplicate and sort
            page_urls = sorted(list(dict.fromkeys(page_urls)))
            
            total_pages = len(page_urls)
            logger.info(f"Found {total_pages} pages for {service}.")
            yield json.dumps({"type": "log", "message": f"Found {total_pages} pages."})
            
            if limit:
                # If limiting, maybe user guides have an order? Sitemap is usually arbitrary.
                # Sorting by URL might help keep it consistent.
                page_urls = page_urls[:limit]
                total_pages = len(page_urls)
                logger.info(f"Limiting to first {limit} pages.")
                yield json.dumps({"type": "log", "message": f"Limiting to {limit} pages."})
            
            full_content_blocks = [None] * total_pages
            
            # Report Initial Progress
            yield json.dumps({
                "type": "progress", 
                "service": service, 
                "current": 0, 
                "total": total_pages, 
                "message": "Starting scrape..."
            })
            
            completed_count = 0
            
            # 4. Scrape Pages
            with ThreadPoolExecutor(max_workers=max_jobs) as executor:
                future_to_index = {executor.submit(scrape_page, url): i for i, url in enumerate(page_urls)}
                
                for future in as_completed(future_to_index):
                    i = future_to_index[future]
                    url = page_urls[i]
                    try:
                        content = future.result()
                        if content:
                            block = f"--- START PAGE: {url} ---\n{content}\n--- END PAGE: {url} ---\n\n"
                            full_content_blocks[i] = block
                        
                        completed_count += 1
                        # Yield Progress
                        yield json.dumps({
                            "type": "progress", 
                            "service": service, 
                            "current": completed_count, 
                            "total": total_pages,
                            "message": f"Scraped {url}"
                        })
                        
                    except Exception as e:
                            logger.error(f"Error scraping {url}: {e}")
                            completed_count += 1
            
            final_content = [b for b in full_content_blocks if b]
            
            filename = f"{service}.md"
            filepath = os.path.join(settings.RAW_DATA_DIR, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("".join(final_content))
            
            yield json.dumps({
                "type": "result", 
                "service": service, 
                "status": "success", 
                "pages_scraped": len(final_content), 
                "path": filepath
            })
                
        except Exception as e:
            logger.error(f"Scrape error: {e}")
            yield json.dumps({"type": "error", "service": service, "message": str(e)})
