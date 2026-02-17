"""
Quotes Spider - Scrapy Spider for quotes.toscrape.com

This spider starts from a logged-in state by using cookies from extract_cookies.py
Anti-detection features implemented:
- User-Agent rotation
- Random delays between requests
- Playwright for JavaScript rendering (real browser)
- Proper headers mimicry

Usage:
    scrapy runspider quotes/spiders/quotes_spider.py -o quotes.json

The spider will use cookies from quotes/cookies.json (extracted by extract_cookies.py)
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
ALIAS = "quotes"
COOKIES_FILE = f"{ALIAS}/cookies.json"
JOBDIR = f"{ALIAS}/.scrapy"  # Website-specific directory for checkpoint files
PAGES_FILE = os.path.join(JOBDIR, "scraped_pages.json")

# User-Agent rotation list
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
]

# Additional headers to mimic real browser
def get_random_headers():
    """Generate random browser headers"""
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': f'en-US,en;q={random.uniform(0.8, 1.0):.1f}',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }


def get_random_user_agent():
    """Get a random User-Agent from the list"""
    return random.choice(USER_AGENTS)


class QuotesSpider(scrapy.Spider):
    name = ALIAS
    allowed_domains = ["quotes.toscrape.com"]
    
    # Target URL - start from the main quotes page after login
    start_urls = ["http://quotes.toscrape.com/"]
    
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
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
        'PLAYWRIGHT_PAGE_INIT_CALLBACK': 'quotes_spider.QuotesSpider.playwright_page_init',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 2,
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, *args, **kwargs):
        """Initialize spider with request counter and checkpoint tracking"""
        super().__init__(*args, **kwargs)
        self.request_count = 0
        self.quotes_extracted = 0
        
        # Create job directory for this website
        if not os.path.exists(JOBDIR):
            os.makedirs(JOBDIR)
        
        # Load checkpoint - track scraped pages
        self.scraped_pages = self.load_scraped_pages()
        
        logger.info("=== Anti-Detection Configuration ===")
        logger.info("DOWNLOAD_DELAY: 2 seconds")
        logger.info("RANDOMIZE_DOWNLOAD_DELAY: True")
        logger.info("CONCURRENT_REQUESTS_PER_DOMAIN: 2")
        logger.info("AUTOTHROTTLE_ENABLED: True (start delay: 2s)")
        logger.info("PLAYWRIGHT_ENABLED: True (headless browser)")
        logger.info("Playwright stealth: ENABLED (playwright-stealth package)")
        logger.info("Playwright stealth args:")
        logger.info("  - --disable-blink-features=AutomationControlled")
        logger.info("  - --disable-dev-shm-usage")
        logger.info("  - --disable-gpu")
        logger.info("  - --window-size=1920,1080")
        logger.info("User-Agent pool size: %d", len(USER_AGENTS))
        logger.info("Progress will be saved to: %s", JOBDIR)
        logger.info("======================================")

    def load_scraped_pages(self):
        """Load list of already scraped pages from checkpoint file"""
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
        """Save list of scraped pages to checkpoint file"""
        try:
            # Ensure directory exists
            os.makedirs(JOBDIR, exist_ok=True)
            with open(PAGES_FILE, 'w') as f:
                json.dump(list(self.scraped_pages), f)
            logger.debug("💾 Saved checkpoint: %d pages scraped", len(self.scraped_pages))
        except Exception as e:
            logger.error("Could not save checkpoint: %s", e)

    def get_stealth_headers(self):
        """Get headers with rotated User-Agent"""
        headers = get_random_headers()
        ua = get_random_user_agent()
        headers['User-Agent'] = ua
        
        # Log the anti-detection settings being used
        logger.debug("=== Anti-Detection Settings ===")
        logger.debug("User-Agent: %s", ua[:50] + "...")
        logger.debug("Accept: %s", headers.get('Accept', 'N/A')[:30] + "...")
        logger.debug("Accept-Language: %s", headers.get('Accept-Language'))
        logger.debug("DNT: %s", headers.get('DNT'))
        logger.debug("Sec-Fetch-Dest: %s", headers.get('Sec-Fetch-Dest'))
        logger.debug("Sec-Fetch-Mode: %s", headers.get('Sec-Fetch-Mode'))
        logger.debug("================================")
        
        return headers

    async def playwright_page_init(self, page, request):
        """Apply stealth to each new page - evades automation detection"""
        logger.debug("Applying stealth patches to page: %s", request.url)
        
        # Apply stealth patches to hide automation
        # Note: scrapy-playwright wraps the page differently
        # Using route interception to inject stealth scripts
        await page.add_init_script("""
            () => {
                // Hide navigator.webdriver
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Add plugins (empty but present)
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Add languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                
                // Mock chrome runtime
                window.chrome = {
                    runtime: {},
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
                
                // Spoof webgl vendor
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, arguments);
                };
            }
        """)
        
        logger.debug("Stealth patches applied successfully")
        
        # Log detection evasion results
        try:
            is_automation = await page.evaluate('navigator.webdriver')
            logger.debug("navigator.webdriver = %s (should be undefined)", is_automation)
        except Exception as e:
            logger.debug("Could not check webdriver: %s", e)

    def start_requests(self):
        """Load cookies and start requests from logged-in state"""
        
        logger.info("Starting requests to %s", self.start_urls)
        logger.debug("Total requests so far: %d", self.request_count)
        
        # Try to load cookies
        if os.path.exists(COOKIES_FILE):
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            
            logger.info("Loaded %d cookies from %s", len(cookies), COOKIES_FILE)
            logger.debug("Cookie names: %s", [c.get('name') for c in cookies])
            
            for url in self.start_urls:
                self.request_count += 1
                headers = self.get_stealth_headers()
                
                logger.info("Request #%d: Fetching %s", self.request_count, url)
                logger.debug("Using User-Agent: %s", headers.get('User-Agent', 'N/A'))
                
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
            logger.warning("No cookies found at %s - proceeding without authentication", COOKIES_FILE)
            logger.info("Please run: python3 extract_cookies.py quotes http://quotes.toscrape.com/login to generate cookies")
            
            for url in self.start_urls:
                self.request_count += 1
                headers = self.get_stealth_headers()
                
                logger.info("Request #%d: Fetching %s (no cookies)", self.request_count, url)
                
                yield scrapy.Request(
                    url=url,
                    headers=headers,
                    callback=self.parse,
                    errback=self.errback,
                    meta={
                        'playwright': True,
                        'playwright_page_init_callback': self.playwright_page_init,
                    }
                )

    async def parse(self, response):
        """Parse the quotes page and extract quote data"""
        page = response.meta.get('playwright_page')
        
        # Checkpoint: skip if already scraped (but still follow pagination)
        if response.url in self.scraped_pages:
            logger.info("⏭️  Skipping already scraped page: %s", response.url)
            # Still follow pagination from this page
            next_page = response.css('li.next a::attr(href)').get()
            if next_page:
                next_url = response.urljoin(next_page)
                if next_url in self.scraped_pages:
                    logger.info("⏭️  Next page also already scraped: %s", next_url)
                else:
                    logger.info("Following pagination from skipped page to: %s", next_url)
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
            if page:
                await page.close()
            return
        
        logger.info("Parsing response from: %s (status: %d)", response.url, response.status)
        logger.debug("Response headers: %s", dict(response.headers))
        
        # Check if we're logged in
        if "login" in response.url.lower():
            logger.warning("Redirected to login page! Cookies may be invalid or expired")
            logger.info("Please re-run: python3 extract_cookies.py quotes http://quotes.toscrape.com/login to refresh cookies")
            if page:
                await page.close()
            return
        
        # Extract quotes from the page
        quotes = response.css('div.quote')
        
        logger.info("Found %d quotes on page: %s", len(quotes), response.url)
        
        for quote in quotes:
            item = {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('span small::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
                'url': response.url,
            }
            self.quotes_extracted += 1
            logger.debug("Extracted quote #%d by %s", self.quotes_extracted, item.get('author'))
            yield item
        
        # Mark this page as scraped and save checkpoint
        self.scraped_pages.add(response.url)
        self.save_scraped_pages()
        logger.info("✅ Page saved to checkpoint: %s", response.url)
        
        logger.info("Total quotes extracted so far: %d", self.quotes_extracted)
        
        # Follow pagination
        next_page = response.css('li.next a::attr(href)').get()
        if next_page:
            next_url = response.urljoin(next_page)
            
            # Checkpoint: skip if next page already scraped
            if next_url in self.scraped_pages:
                logger.info("⏭️  Next page already scraped, skipping: %s", next_url)
            else:
                logger.info("Following pagination to: %s", next_url)
                
                # Add random delay before next request
                delay = random.uniform(1.5, 3.0)
                logger.debug("Waiting %.1f seconds before next request", delay)
                await asyncio.sleep(delay)
                
                # Load cookies again for next page
                if os.path.exists(COOKIES_FILE):
                    with open(COOKIES_FILE, 'r') as f:
                        cookies = json.load(f)
                    
                    self.request_count += 1
                    headers = self.get_stealth_headers()
                    
                    logger.info("Request #%d: Fetching next page %s", self.request_count, next_url)
                    
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
        else:
            logger.info("No more pages to follow. Scraping complete!")
            logger.info("Final stats - Requests: %d, Quotes: %d", self.request_count, self.quotes_extracted)
        
        # Close the page
        if page:
            await page.close()

    async def errback(self, failure):
        """Handle errors"""
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()
        
        logger.error("Request failed: %s", failure.value)
        logger.debug("Failed request URL: %s", failure.request.url)
        logger.debug("Failure type: %s", type(failure.value).__name__)
