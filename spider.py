"""
Common Spider for Semi-Automated Multi-Website Scraping

This is a generic spider that works for any website configured in websites_input.json.
It uses cookies from extract_cookies.py and applies anti-detection features:
- User-Agent rotation
- Random delays between requests
- Playwright for JavaScript rendering (real browser)
- Proper headers mimicry
- Chunked output support

Usage:
    # With alias as positional argument:
    scrapy runspider spider.py quotes

    # With -a alias= syntax:
    scrapy runspider spider.py -a alias=quotes

    # Interactive mode (no alias - will prompt for selection):
    scrapy runspider spider.py

The spider will use cookies from {alias}_cookies.json (extracted by extract_cookies.py)
Output file is determined by output_path in websites_input.json
"""

import json
import logging
import os
import random
import asyncio
import importlib
import sys
import scrapy
from scrapy_playwright.page import PageMethod

# Import User-Agent list from settings
from settings import USER_AGENT_LIST

# Create logger for this module
logger = logging.getLogger(__name__)


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
    return random.choice(USER_AGENT_LIST)


def load_website_configs():
    """
    Load all website configurations from websites_input.json.

    Returns:
        list: List of website configuration dictionaries
    """
    config_path = "websites_input.json"

    if not os.path.exists(config_path):
        logger.error("Website configuration file not found: %s", config_path)
        return []

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            websites = json.load(f)

        if not isinstance(websites, list):
            logger.error("websites_input.json must contain a list of websites")
            return []

        return websites

    except Exception as e:
        logger.error("Failed to load website config: %s", e)
        return []


def load_website_config(alias):
    """
    Load website configuration by alias from websites_input.json.

    Args:
        alias: The website alias to look up

    Returns:
        dict: Website configuration dictionary or None if not found
    """
    websites = load_website_configs()

    for website in websites:
        if website.get('alias') == alias:
            return website

    logger.error("Website alias not found in config: %s", alias)
    logger.info("Available aliases: %s", [w.get('alias') for w in websites])
    return None


def select_website():
    """
    Display a list of websites and ask user to select one.

    Returns:
        dict: Selected website configuration, or None if cancelled
    """
    websites = load_website_configs()

    if not websites:
        return None

    print("\n" + "=" * 60, file=sys.stderr)
    print("🕷️  Select a website to scrape:", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    for i, website in enumerate(websites, 1):
        alias = website.get('alias', 'Unknown')
        start_url = website.get('start_url', 'No URL')
        output_path = website.get('output_path', alias)
        print(f"  [{i}] {alias}", file=sys.stderr)
        print(f"      Start URL: {start_url}", file=sys.stderr)
        print(f"      Output: {output_path}.json", file=sys.stderr)

    print("\n  [0] Cancel", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    try:
        choice = input("Enter your choice (0-{0}): ".format(len(websites)))
        choice = int(choice)

        if choice == 0:
            print("Cancelled.", file=sys.stderr)
            return None
        elif 1 <= choice <= len(websites):
            return websites[choice - 1]
        else:
            print(f"Error: Invalid choice. Please enter a number between 0 and {len(websites)}", file=sys.stderr)
            return None

    except ValueError:
        print("Error: Please enter a valid number", file=sys.stderr)
        return None
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return None


def load_next_url_func(func_path):
    """
    Dynamically load the next_url_func from the given path.

    Args:
        func_path: Dot-separated path to the function (e.g., 'next_url_funcs.quote_next_url_func.quote_next_url')

    Returns:
        callable: The next_url function, or None if loading fails
    """
    try:
        # Split the path to get module and function names
        parts = func_path.split('.')

        # The last part is the function name, the rest is the module path
        func_name = parts[-1]
        module_path = '.'.join(parts[:-1])

        # Import the module
        module = importlib.import_module(module_path)

        # Get the function
        func = getattr(module, func_name)
        logger.info("Loaded next_url_func: %s", func_path)
        return func

    except Exception as e:
        logger.error("Failed to load next_url_func: %s", e)
        logger.error("Function path: %s", func_path)
        return None


class CommonSpider(scrapy.Spider):
    name = "common_spider"

    # NOTE: When using scrapy runspider, settings from settings.py may not be fully loaded.
    # To ensure consistent behavior, key Playwright settings are defined here in custom_settings.
    # These will override any settings from settings.py (which is correct behavior).
    # Only spider-specific settings (like callbacks) should be unique to the spider.
    custom_settings = {
        # Keep minimal settings here - most are inherited from settings.py
        # The callback must point to this spider's method
        'PLAYWRIGHT_PAGE_INIT_CALLBACK': 'spider.CommonSpider.playwright_page_init',
    }

    def __init__(self, alias=None, *args, **kwargs):
        """
        Initialize spider with website configuration.

        Args:
            alias: Website alias (positional argument, optional)
            chunk_size: Number of items per chunk file (optional, default=0 for no chunking)
        """
        super().__init__(*args, **kwargs)
        self.alias = alias
        self.chunk_size = int(kwargs.get('chunk_size', 0))

        # If no alias provided, show interactive selection
        if not self.alias:
            config = select_website()
            if config:
                self.alias = config.get('alias')
                self.config = config
            else:
                sys.exit(0)
        else:
            # Load website configuration from alias
            self.config = load_website_config(self.alias)
            if not self.config:
                sys.exit(1)

        # Apply speed overrides from config if present
        speed_override = self.config.get('speed_override', {})
        if speed_override:
            for key, value in speed_override.items():
                self.custom_settings[key.upper()] = value
                logger.info("Speed setting overridden: %s = %s", key, value)

        # Set spider properties from config
        self.name = self.alias
        self.allowed_domains = self.config.get('allowed_domains', [])
        self.start_urls = [self.config.get('start_url')]
        self.output_path = self.config.get('output_path', self.alias)
        self.chunked_size = self.config.get('chunked_size', 0)

        # Cookie file path
        self.cookies_file = f"{self.alias}_cookies.json"

        # Job directory for checkpoints
        self.jobdir = ".scrapy"
        self.pages_file = os.path.join(self.jobdir, f"{self.alias}_scraped_pages.json")

        # Chunked output tracking
        self.current_chunk = 0
        self.current_chunk_items = []
        self.items_in_current_chunk = 0

        # Initialize request and item counters
        self.request_count = 0
        self.items_extracted = 0

        # Load next_url_func
        next_url_func_path = self.config.get('next_url_func')
        if next_url_func_path:
            self.next_url_func = load_next_url_func(next_url_func_path)
            if not self.next_url_func:
                logger.warning("next_url_func not found, pagination may not work")
                self.next_url_func = None
        else:
            logger.warning("No next_url_func configured for this website")
            self.next_url_func = None

        # Create job directory
        if not os.path.exists(self.jobdir):
            os.makedirs(self.jobdir)

        # Load checkpoint - track scraped pages
        self.scraped_pages = self.load_scraped_pages()

        logger.info("=== Spider Configuration ===")
        logger.info("Alias: %s", self.alias)
        logger.info("Start URL: %s", self.start_urls)
        logger.info("Output path: %s", self.output_path)
        logger.info("Chunked size: %s", self.chunked_size if self.chunked_size > 0 else "Disabled")
        logger.info("Cookies file: %s", self.cookies_file)
        logger.info("Checkpoint file: %s", self.pages_file)
        logger.info("============================")

    def load_scraped_pages(self):
        """Load list of already scraped pages from checkpoint file"""
        if os.path.exists(self.pages_file):
            try:
                with open(self.pages_file, 'r') as f:
                    pages = json.load(f)
                logger.info("Loaded checkpoint: %d pages already scraped", len(pages))
                return set(pages)
            except Exception as e:
                logger.warning("Could not load checkpoint file: %s", e)
        return set()

    def save_scraped_pages(self):
        """Save list of scraped pages to checkpoint file"""
        try:
            os.makedirs(self.jobdir, exist_ok=True)
            with open(self.pages_file, 'w') as f:
                json.dump(list(self.scraped_pages), f)
            logger.debug("Saved checkpoint: %d pages scraped", len(self.scraped_pages))
        except Exception as e:
            logger.error("Could not save checkpoint: %s", e)

    def get_stealth_headers(self):
        """Get headers with rotated User-Agent"""
        headers = get_random_headers()
        ua = get_random_user_agent()
        headers['User-Agent'] = ua
        return headers

    async def playwright_page_init(self, page, request):
        """Apply stealth to each new page - evades automation detection"""
        logger.debug("Applying stealth patches to page: %s", request.url)

        await page.add_init_script("""
            () => {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
                window.chrome = {
                    runtime: {},
                };
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
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

    def start_requests(self):
        """Load cookies and start requests from logged-in state"""
        logger.info("Starting requests to %s", self.start_urls)

        if not os.path.exists(self.cookies_file):
            logger.warning("No cookies found at %s - proceeding without authentication", self.cookies_file)
            logger.info("Please run: python3 extract_cookies.py %s to generate cookies", self.alias)

        for url in self.start_urls:
            self.request_count += 1
            headers = self.get_stealth_headers()

            logger.info("Request #%d: Fetching %s", self.request_count, url)

            yield scrapy.Request(
                url=url,
                headers=headers,
                callback=self.parse,
                errback=self.errback,
                meta={
                    'playwright': True,
                    'playwright_include_page': True,
                    'playwright_page_init_callback': self.playwright_page_init,
                }
            )

    def save_item_to_output(self, item):
        """
        Save item to output, handling chunked output if enabled.

        Args:
            item: The scraped item to save
        """
        if self.chunked_size > 0:
            # Chunked output mode
            self.current_chunk_items.append(item)
            self.items_in_current_chunk += 1

            if self.items_in_current_chunk >= self.chunked_size:
                self._write_chunk()
        else:
            # Single file output mode - accumulate items and write on close
            self.current_chunk_items.append(item)
            logger.debug("Item extracted: %s", item.get('text', item.get('title', item.get('url', 'unknown'))))

    def _write_chunk(self):
        """Write current chunk to file"""
        if not self.current_chunk_items:
            logger.debug("No items to write in chunk")
            return

        if self.chunked_size > 0:
            # Chunked output: {output_path}_0.json, {output_path}_1.json, etc.
            chunk_filename = f"{self.output_path}_{self.current_chunk}.json"
        else:
            # Single output file
            chunk_filename = f"{self.output_path}.json"

        logger.info("Writing %d items to %s", len(self.current_chunk_items), chunk_filename)

        try:
            # Create output directory if it doesn't exist
            output_dir = os.path.dirname(chunk_filename)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info("Created output directory: %s", output_dir)

            with open(chunk_filename, 'w', encoding='utf-8') as f:
                json.dump(self.current_chunk_items, f, indent=2, ensure_ascii=False)

            logger.info("Successfully wrote %d items to %s",
                       len(self.current_chunk_items), chunk_filename)

            self.current_chunk += 1
            self.current_chunk_items = []
            self.items_in_current_chunk = 0

        except Exception as e:
            logger.error("Failed to write chunk: %s", e)
            import traceback
            logger.error(traceback.format_exc())

    def close_spider(self, reason):
        """Called when spider is closed - write any remaining items"""
        try:
            if self.current_chunk_items:
                self._write_chunk()

            logger.info("Spider closed: %s", reason)
            logger.info("Final stats - Requests: %d, Items: %d", self.request_count, self.items_extracted)
        except Exception as e:
            logger.error("Error in close_spider: %s", e)
            import traceback
            logger.error(traceback.format_exc())

    async def parse(self, response):
        """Parse the page and extract data"""
        page = response.meta.get('playwright_page')

        # Checkpoint: skip if already scraped (but still follow pagination)
        if response.url in self.scraped_pages:
            logger.info("Skipping already scraped page: %s", response.url)

            # Still follow pagination from this page
            if self.next_url_func:
                next_url = self.next_url_func(response)
                if next_url and next_url not in self.scraped_pages:
                    async for req in self.follow_next_page(response, next_url):
                        yield req

            if page:
                await page.close()
            return

        logger.info("Parsing response from: %s (status: %d)", response.url, response.status)

        # Check if logged in
        if "login" in response.url.lower():
            logger.warning("Redirected to login page! Cookies may be invalid or expired")
            logger.info("Please run: python3 extract_cookies.py %s to refresh cookies", self.alias)
            if page:
                await page.close()
            return

        # Extract data from the page (this should be overridden by website-specific parsing)
        items = await self.extract_items(response)

        for item in items:
            self.items_extracted += 1
            self.save_item_to_output(item)
            yield item

            if self.items_extracted % 10 == 0:
                logger.info("Total items extracted so far: %d", self.items_extracted)

        # Mark this page as scraped and save checkpoint
        self.scraped_pages.add(response.url)
        self.save_scraped_pages()
        logger.info("Page saved to checkpoint: %s", response.url)

        # Follow pagination
        if self.next_url_func:
            next_url = self.next_url_func(response)
            if next_url:
                # Checkpoint: skip if next page already scraped
                if next_url in self.scraped_pages:
                    logger.info("Next page already scraped, skipping: %s", next_url)
                else:
                    async for req in self.follow_next_page(response, next_url):
                        yield req
            else:
                logger.info("No more pages to follow. Scraping complete!")
                # Write remaining items to file
                if self.current_chunk_items:
                    self._write_chunk()
                logger.info("Spider closed: finished")
                logger.info("Final stats - Requests: %d, Items: %d", self.request_count, self.items_extracted)
        else:
            logger.info("No next_url_func configured. Pagination will not be followed.")

        # Close the page
        if page:
            await page.close()

    async def extract_items(self, response):
        """
        Extract items from the response. Override this method for website-specific parsing.

        Args:
            response: Scrapy Response object

        Returns:
            list: List of extracted item dictionaries
        """
        # Default implementation - override this in subclasses or configure parsing
        # This is a placeholder that should be customized per website
        logger.warning("Using default extract_items - parsing logic should be customized for this website")

        # Try to extract common elements or return empty list
        # Website-specific parsing should be implemented by:
        # 1. Creating a custom parse_items function in next_url_funcs/
        # 2. Or subclassing CommonSpider and overriding extract_items
        # 3. Or configuring a parse_items_func in websites_input.json

        return []

    async def follow_next_page(self, response, next_url):
        """Follow to the next page with anti-detection measures"""
        # Add random delay before next request
        delay = random.uniform(1.5, 3.0)
        logger.debug("Waiting %.1f seconds before next request", delay)
        await asyncio.sleep(delay)

        # Load cookies for next page
        cookies = None
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
            except Exception as e:
                logger.warning("Could not load cookies: %s", e)

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

    async def errback(self, failure):
        """Handle errors"""
        page = failure.request.meta.get('playwright_page')
        if page:
            await page.close()

        logger.error("Request failed: %s", failure.value)
        logger.debug("Failed request URL: %s", failure.request.url)


class QuotesSpider(CommonSpider):
    """
    Quotes-specific spider that extends CommonSpider with quotes.toscrape.com parsing.
    """

    name = "quotes"

    async def extract_items(self, response):
        """
        Extract quotes from the quotes.toscrape.com page.

        Args:
            response: Scrapy Response object

        Returns:
            list: List of quote dictionaries
        """
        # Extract quotes from the page
        quotes = response.css('div.quote')

        logger.info("Found %d quotes on page: %s", len(quotes), response.url)

        items = []
        for quote in quotes:
            item = {
                'text': quote.css('span.text::text').get(),
                'author': quote.css('span small::text').get(),
                'tags': quote.css('div.tags a.tag::text').getall(),
                'url': response.url,
            }
            items.append(item)

        return items


# Create a factory function to get the appropriate spider class
def get_spider_class(alias):
    """
    Get the spider class for the given alias.

    Args:
        alias: Website alias

    Returns:
        Spider class or CommonSpider as default
    """
    # Map of known aliases to their spider classes
    spider_classes = {
        'quotes': QuotesSpider,
    }

    return spider_classes.get(alias, CommonSpider)


# Allow running with: python spider.py [alias]
if __name__ == '__main__':
    import sys
    from scrapy.cmdline import execute
    
    # Handle simplified syntax: python spider.py quotes
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        alias = sys.argv[1]
        sys.argv = ['scrapy', 'runspider', 'spider.py', '-a', f'alias={alias}']
    else:
        sys.argv = ['scrapy', 'runspider', 'spider.py']
    
    execute()
