import requests
from bs4 import BeautifulSoup
import csv
import time
from urllib.parse import urljoin

# Base URL and start page
BASE_URL = "https://www.merckmanuals.com"
START_URL = f"{BASE_URL}/en-ca/home/health-topics"

# Set to track visited URLs
visited_urls = set()

def fetch_page(url):
    """Fetch the HTML content for a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_links(html, current_url):
    """
    Extract only relevant internal topic links.
    - Excludes professional pages, author pages, and non-topic sections.
    """
    soup = BeautifulSoup(html, 'html.parser')
    links = set()
    
    for a in soup.find_all('a', href=True):
        href = a['href']
        if (
            href.startswith("/en-ca/home/") 
            and "professional" not in href 
            and "resourcespages" not in href 
            and "author" not in href
            and "about" not in href  
            and "contact" not in href  
        ):
            full_url = urljoin(BASE_URL, href)
            if full_url != current_url:  # Avoid self-referencing links
                links.add(full_url)
    
    return list(links)

def extract_main_text(html):
    """
    Extract clean text from the main content container.
    - Removes navigation, links, and non-content elements.
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Target main content area
    content_container = soup.find('div', class_='content') or soup.find('body')
    
    if content_container:
        # Remove unnecessary elements (menus, links, scripts)
        for tag in content_container(['script', 'style', 'nav', 'footer', 'header', 'a']):
            tag.extract()
        
        text = content_container.get_text(separator=" ", strip=True)
        return text.replace("\n", " ")  # Ensure single-line text per row
    
    return ""

def scrape(url, csv_writer):
    """Recursively scrape the given URL and its subpages."""
    if url in visited_urls:
        return
    visited_urls.add(url)

    print(f"Scraping: {url}")
    
    html = fetch_page(url)
    if not html:
        return

    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    page_title = title_tag.get_text(strip=True) if title_tag else "No Title"
    
    # Extract clean text
    text_content = extract_main_text(html)
    
    # Write structured data to CSV
    csv_writer.writerow([page_title, url, text_content])
    
    # Process sub-links recursively
    sub_links = extract_links(html, url)
    for link in sub_links:
        time.sleep(1) 
        scrape(link, csv_writer)

def main():
    with open("merck_latest.csv", "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Title", "URL", "Content"])
        scrape(START_URL, writer)

if __name__ == "__main__":
    main()
