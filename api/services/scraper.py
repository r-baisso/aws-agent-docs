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
from api.services.aws_metadata import validate_service, get_service_toc_url
import logging

logger = logging.getLogger(__name__)

def get_toc_urls(toc_json, base_url):
    """Recursively extract URLs from the TOC JSON."""
    urls = []
    if isinstance(toc_json, dict):
        if "href" in toc_json and toc_json["href"] and not toc_json["href"].startswith("#"):
             # Handle relative URLs. Some might be relative to the TOC location.
             # Usually they are just filenames like "Welcome.html"
             urls.append(base_url + toc_json["href"])
        
        if "contents" in toc_json:
            for item in toc_json["contents"]:
                urls.extend(get_toc_urls(item, base_url))
    elif isinstance(toc_json, list):
        for item in toc_json:
            urls.extend(get_toc_urls(item, base_url))
    return urls

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
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_aws_docs(service_list: list[str], limit: int = None, max_jobs: int = 4):
    # Yields JSON strings for progress updates
    
    # Ensure max_jobs is reasonable
    if max_jobs < 1: max_jobs = 1
    if max_jobs > 20: max_jobs = 20

    for service in service_list:
        yield json.dumps({"type": "log", "message": f"Validating service: {service}..."})
        
        valid, toc_url = validate_service(service)
        if not valid:
            logger.warning(f"Service {service} validation failed.")
            yield json.dumps({"type": "error", "service": service, "message": "Validation failed or not found."})
            continue

        base_url = toc_url.replace("toc-contents.json", "")
        
        logger.info(f"Fetching TOC from {toc_url}...")
        yield json.dumps({"type": "log", "message": f"Fetching TOC for {service}..."})
        
        try:
            response = requests.get(toc_url, timeout=10)
            if response.status_code != 200:
                toc_url = toc_url.replace("userguide", "developerguide")
                base_url = toc_url.replace("toc-contents.json", "")
                logger.info(f"Retrying with Developer Guide: {toc_url}...")
                yield json.dumps({"type": "log", "message": "Retrying with Developer Guide..."})
                response = requests.get(toc_url, timeout=10)

            if response.status_code == 200:
                toc_data = response.json()
                page_urls = get_toc_urls(toc_data, base_url)
                page_urls = list(dict.fromkeys(page_urls))
                
                total_pages = len(page_urls)
                logger.info(f"Found {total_pages} pages for {service}.")
                yield json.dumps({"type": "log", "message": f"Found {total_pages} pages."})
                
                if limit:
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
                             # Still increment completed count effectively?
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
                
            else:
                 yield json.dumps({"type": "error", "service": service, "message": f"Top of Content not found (404)."})
                 
        except Exception as e:
            yield json.dumps({"type": "error", "service": service, "message": str(e)})
