from api.services.scraper import scrape_aws_docs
import os
from api.core.config import settings

# Test with AmazonS3 and a limit of 5 pages
print("Starting scraper verification...")
results = scrape_aws_docs(["AmazonS3"], limit=5)
print("Scraper finished.")
print(results)

# Check if file exists
filepath = os.path.join(settings.RAW_DATA_DIR, "AmazonS3.md")
if os.path.exists(filepath):
    print(f"File created at {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"File content length: {len(content)}")
        print("First 500 chars:")
        print(content[:500])
else:
    print("File not created!")
