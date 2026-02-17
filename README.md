# 🍀 Semi-Automated Multi-Website Scraping Project

This project supports scraping multiple websites with a reusable framework. Each website has its own spider, settings, and output directories.

## 📁 Project Structure

```
python-scrape/
├── extract_cookies.py           # Generic cookie extractor (works for any website)
├── quotes/
│   ├── __init__.py
│   ├── settings.py              # Scrapy settings for quotes
│   ├── .scrapy/                # Progress/checkpoint files (gitignored)
│   │   └── scraped_pages.json
│   ├── cookies.json             # Cookies extracted by extract_cookies.py
│   └── spiders/
│       ├── __init__.py
│       └── quotes_spider.py     # Spider for quotes.toscrape.com
├── huawei/
│   ├── __init__.py
│   ├── settings.py              # Scrapy settings for huawei
│   ├── .scrapy/                 # Progress/checkpoint files (gitignored)
│   │   └── scraped_pages.json
│   ├── cookies.json              # Cookies extracted by extract_cookies.py
│   └── spiders/
│       ├── __init__.py
│       └── huawei_spider.py    # Spider for cloud.huawei.com
├── scrapy.cfg                  # Scrapy configuration
├── .gitignore
└── requirements.txt
```

## 🚀 Quick Start

### Step 1: Extract Cookies for a Website

```bash
# For quotes website
python3 extract_cookies.py quotes http://quotes.toscrape.com/login

# For huawei website
python3 extract_cookies.py huawei https://cloud.huawei.com/login
```

This will:
- Launch Chrome browser and open the login page
- Wait for you to enter username and password
- After login, press Enter to extract cookies
- Save cookies to `{alias}/cookies.json`

### Step 2: Run the Spider

```bash
# For quotes website
scrapy runspider quotes/spiders/quotes_spider.py -o quotes.json

# For huawei website
scrapy runspider huawei/spiders/huawei_spider.py -o huawei.json

# With max images limit (for huawei)
scrapy runspider huawei/spiders/huawei_spider.py -a max_images=50 -o huawei.json
scrapy runspider huawei/spiders/huawei_spider.py -a max_images=-1 -o huawei.json  # Unlimited
```

---

## 🆕 How to Create a Spider for a New Website

Follow these steps to add a new website to the project:

### Step 1: Create the Website Directory Structure

```bash
# Create the project structure
mkdir -p {alias}/spiders
touch {alias}/__init__.py
touch {alias}/settings.py
touch {alias}/spiders/__init__.py
```

Example for `example.com`:
```bash
mkdir -p example/spiders
touch example/__init__.py
touch example/settings.py
touch example/spiders/__init__.py
```

### Step 2: Create the Settings File

Copy `quotes/settings.py` to `example/settings.py` and modify:

```python
# example/settings.py
BOT_NAME = "example"

SPIDER_MODULES = ["example.spiders"]
NEWSPIDER_MODULE = "example.spiders"

# Update logging
LOG_FILE = "example.log"
```

### Step 3: Create the Spider

Copy `quotes/spiders/quotes_spider.py` to `example/spiders/example_spider.py` and modify:

```python
# example/spiders/example_spider.py

# Update module name in PLAYWRIGHT_PAGE_INIT_CALLBACK
'PLAYWRIGHT_PAGE_INIT_CALLBACK': 'example_spider.ExampleSpider.playwright_page_init',

class ExampleSpider(scrapy.Spider):
    name = ALIAS  # Use "example" as alias
    allowed_domains = ["example.com"]
    start_urls = ["https://example.com/protected-page"]
```

### Step 4: Extract Cookies

```bash
python3 extract_cookies.py example https://example.com/login
```

This will create `example/cookies.json` and the `example/.scrapy/` directory.

### Step 5: Run the Spider

```bash
scrapy runspider example/spiders/example_spider.py -o example.json
```

---

## 📋 Spider Creation Template

Use this template when creating a new spider:

```python
"""
{Website Name} Spider - Scrapy Spider for {domain.com}

This spider starts from a logged-in state by using cookies from extract_cookies.py
Anti-detection features implemented:
- User-Agent rotation
- Random delays between requests
- Playwright for JavaScript rendering (real browser)
- Proper headers mimicry

Usage:
    scrapy runspider {alias}/spiders/{alias}_spider.py -o {alias}.json

The spider will use cookies from {alias}/cookies.json (extracted by extract_cookies.py)
"""

import json
import logging
import os
import random
import asyncio
import scrapy
from scrapy_playwright.page import PageMethod

# Create logger for this module
logger = logging.getLogger(__name__)

# Website alias
ALIAS = "{alias}"
COOKIES_FILE = f"{ALIAS}/cookies.json"
JOBDIR = f"{ALIAS}/.scrapy"  # Website-specific directory
PAGES_FILE = os.path.join(JOBDIR, "scraped_pages.json")
IMAGES_DIR = f"result/{ALIAS}"  # Only for image scraping

# User-Agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    # Add more User-Agents...
]

def get_random_headers():
    """Generate random browser headers"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,...',
        'Accept-Language': f'en-US,en;q={random.uniform(0.8, 1.0):.1f}',
        # Add more headers...
    }

def get_random_user_agent():
    return random.choice(USER_AGENTS)

class {CamelCase}Spider(scrapy.Spider):
    name = ALIAS
    allowed_domains = ["{domain.com}"]
    
    start_urls = ["https://{domain.com}/target-page"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 3,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'PLAYWRIGHT_ENABLED': True,
        'PLAYWRIGHT_LAUNCH_OPTIONS': {
            'headless': True,
            'args': [
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080',
            ],
        },
        'PLAYWRIGHT_PAGE_INIT_CALLBACK': '{alias}_spider.{CamelCase}Spider.playwright_page_init',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 3,
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request_count = 0
        self.items_extracted = 0
        
        # Create directories
        if not os.path.exists(JOBDIR):
            os.makedirs(JOBDIR)
        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR)
        
        # Load checkpoint
        self.scraped_pages = self.load_scraped_pages()

    def load_scraped_pages(self):
        if os.path.exists(PAGES_FILE):
            try:
                with open(PAGES_FILE, 'r') as f:
                    pages = json.load(f)
                logger.info("📂 Loaded checkpoint: %d pages already scraped", len(pages))
                return set(pages)
            except Exception as e:
                logger.warning("Could not load checkpoint file: %s", e)
        return set()
    
    def save_scraped_pages(self):
        try:
            os.makedirs(JOBDIR, exist_ok=True)
            with open(PAGES_FILE, 'w') as f:
                json.dump(list(self.scraped_pages), f)
        except Exception as e:
            logger.error("Could not save checkpoint: %s", e)

    def get_stealth_headers(self):
        headers = get_random_headers()
        ua = get_random_user_agent()
        headers['User-Agent'] = ua
        return headers

    async def playwright_page_init(self, page, request):
        """Apply stealth to each new page"""
        await page.add_init_script("""
            () => {
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            }
        """)

    def start_requests(self):
        """Load cookies and start requests from logged-in state"""
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            
            for url in self.start_urls:
                self.request_count += 1
                headers = self.get_stealth_headers()
                yield scrapy.Request(
                    url=url,
                    cookies=cookies,
                    headers=headers,
                    callback=self.parse,
                    errback=self.errback,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_init_callback': self.playwright_page_init,
                    }
                )
        else:
            logger.warning("No cookies found at %s", COOKIES_FILE)
            logger.info("Please run: python3 extract_cookies.py %s <login_url>", ALIAS)

    async def parse(self, response):
        """Parse the page and extract data"""
        page = response.meta.get('playwright_page')
        
        # Skip if already scraped
        if response.url in self.scraped_pages:
            logger.info("⏭️  Skipping already scraped page: %s", response.url)
            if page:
                await page.close()
            return
        
        logger.info("Parsing: %s (status: %d)", response.url, response.status)
        
        # Check if logged in
        if "login" in response.url.lower():
            logger.warning("Redirected to login page! Cookies may be invalid")
            if page:
                await page.close()
            return
        
        # Extract data - UPDATE THIS PART FOR YOUR WEBSITE
        items = response.css('div.item')  # Replace with actual selector
        
        for item in items:
            data = {
                'title': item.css('h2.title::text').get(),
                'url': response.url,
                # Add more fields...
            }
            self.items_extracted += 1
            yield data
        
        # Follow pagination - UPDATE THIS PART FOR YOUR WEBSITE
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            next_url = response.urljoin(next_page)
            delay = random.uniform(1.5, 3.0)
            await asyncio.sleep(delay)
            
            if os.path.exists(COOKIES_FILE):
                with open(COOKIES_FILE, 'r') as f:
                    cookies = json.load(f)
                self.request_count += 1
                headers = self.get_stealth_headers()
                yield scrapy.Request(
                    url=next_url,
                    cookies=cookies,
                    headers=headers,
                    callback=self.parse,
                    meta={
                        'playwright': True,
                        'playwright_include_page': True,
                        'playwright_page_init_callback': self.playwright_page_init,
                    }
                )
        
        # Mark page as scraped
        self.scraped_pages.add(response.url)
        self.save_scraped_pages()
        
        logger.info("Total items extracted so far: %d", self.items_extracted)
        
        if page:
            await page.close()

    async def errback(self, failure):
        """Handle errors"""
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()
        logger.error("Request failed: %s", failure.value)
```

---

## 🛡️ Anti-Detection Features

| Feature | Description |
|---------|-------------|
| **User-Agent Rotation** | 8 different browser User-Agents rotate per request |
| **Playwright Stealth** | Uses playwright-stealth to hide automation flags |
| **Real Browser Rendering** | Uses headless Chrome (not raw HTTP) |
| **Request Delays** | 2-3 second delay between requests (randomized) |
| **AutoThrottle** | Automatically adjusts speed based on server response |
| **Proper Headers** | Mimics real browser headers (Accept, Sec-Fetch-*, etc.) |

## 💾 Checkpoint / Resume (断点续传)

The spider automatically saves its progress:

- **Checkpoint Directory**: `{alias}/.scrapy/`
- **Checkpoint File**: `scraped_pages.json`

```bash
# View checkpoint status
cat {alias}/.scrapy/scraped_pages.json

# To start fresh (delete checkpoint)
rm -rf {alias}/.scrapy/
```

---

## 📦 Installation

```bash
pip3 install playwright scrapy scrapy-playwright playwright-stealth
```

---

## ⚠️ Important Notes

1. **Respect robots.txt** - Always check if scraping is allowed
2. **Rate limiting** - The spider has delays to avoid overloading servers
3. **Legal considerations** - Only scrape sites you have permission to access
4. **Session expiry** - Cookies may expire; re-run extract_cookies.py if needed
5. **Anti-detection** - This project uses stealth techniques; use responsibly

---

## 📚 Resources

- [Scrapy Documentation](https://docs.scrapy.org/)
- [Playwright Python](https://playwright.dev/python/)
- [CSS Selectors](https://www.w3schools.com/cssref/css_selectors.asp)
