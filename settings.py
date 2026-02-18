# Scrapy Settings - Common for all websites

import logging

BOT_NAME = "common_scraper"

SPIDER_MODULES = ["spiders"]
NEWSPIDER_MODULE = "spiders"

# ============================================
# LOGGING SETTINGS
# ============================================

# Configure logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)8s] %(name)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# Enable Scrapy logging
LOG_ENABLED = True

# Log to both file and console
LOG_FILE = "scrapy.log"

# Detailed log settings
LOG_STDOUT = True
LOG_ENCODING = "utf-8"

# ============================================
# ANTI-DETECTION SETTINGS
# ============================================

# User-Agent rotation list (real browser User-Agents)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36"

USER_AGENT_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.129 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36",
]

# Default headers to mimic real browser
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9',
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

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests (reduced for stealth)
CONCURRENT_REQUESTS = 1

# Configure a delay for requests
DOWNLOAD_DELAY =1 
RANDOMIZE_DOWNLOAD_DELAY = True

# Disable cookies (enabled for login functionality)
COOKIES_ENABLED = True

# Enable Playwright
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

# Playwright settings - Stealth mode
PLAYWRIGHT_BROWSER_TYPE = "chromium"

# Try to find Chrome executable, fallback to default
import shutil
CHROME_PATH = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chromium-browser") or None

PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
    "executable_path": CHROME_PATH,
    "args": [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-blink-features=AutomationControlled",  # Hide automation
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--start-maximized",
        # Additional stealth arguments
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "--disable-features=TranslateUI",
        "--disable-ipc-flooding-protection",
        "--enable-features=NetworkService,NetworkServiceInProcess",
        "--disable-breakpad",
        "--disable-component-extensions-with-background-pages",
        "--disable-default-apps",
        "--disable-extensions",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
    ],
}

# Inject stealth script to hide automation
PLAYWRIGHT_PAGE_GOTO_OPTIONS = {
    "wait_until": "domcontentloaded",  # Changed from networkidle for better compatibility with slow networks
    "timeout": 60000,
}

PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 60000  # Increased to 60 seconds

# Enable and configure the AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
INITIAL_AUTOTHROTTLE_DELAY = 2.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_START_DELAY = 2.0

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
FEED_EXPORT_ENCODING = "utf-8"

# Enable HTTP compression
HTTP_COMPRESSION_ENABLED = True

# Retry settings
RETRY_ENABLED = True
RETRY_TIMES = 5  # Increased from 3 to 5 for more resilience
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 460, 499]
