# 🍀 Semi-Automated Multi-Website Scraping Project

This project supports scraping multiple websites with a reusable framework. Each website is configured in `websites_input.json` and uses a common spider with website-specific next_url functions.

## 📁 Project Structure

```
python-scrape/
├── scrapy.cfg                      # Scrapy configuration
├── settings.py                      # Common Scrapy settings for all websites
├── websites_input.json              # Website configuration file
├── extract_cookies.py              # Generic cookie extractor (reads from websites_input.json)
├── spider.py                       # Common spider (takes alias as argument)
├── next_url_funcs/                 # Website-specific next URL generation functions
│   ├── __init__.py
│   └── quote_next_url_func.py      # Next URL function for quotes.toscrape.com
├── quotes_cookies.json             # Cookies extracted by extract_cookies.py
├── quotes.json                     # Scraped output (or chunked files: quotes_0.json, quotes_1.json, etc.)
├── .scrapy/                       # Progress/checkpoint files (gitignored)
│   └── quotes_scraped_pages.json   # Checkpoint file (prefixed with alias)
├── .gitignore
└── requirements.txt
```

## 🚀 Quick Start

### Step 1: Configure the Website

Add your website to `websites_input.json`:

```json
[
    {
        "alias": "quotes",
        "login_url": "http://quotes.toscrape.com/login",
        "start_url": "http://quotes.toscrape.com/",
        "next_url_func": "next_url_funcs.quote_next_url_func.quote_next_url",
        "output_path": "quotes",
        "chunked_size": 0,
        "allowed_domains": ["quotes.toscrape.com"]
    }
]
```

### Step 2: Extract Cookies for a Website

```bash
# With alias argument:
python3 extract_cookies.py quotes

# Interactive mode (no alias - will prompt for selection):
python3 extract_cookies.py
```

This will:
- Read the alias and login_url from `websites_input.json`
- Launch Chrome browser and open the login page
- Wait for you to enter username and password
- After login, press Enter to extract cookies
- Save cookies to `{alias}_cookies.json` (e.g., `quotes_cookies.json`)

### Step 3: Run the Spider

```bash
# Simplified syntax (recommended):
python spider.py quotes

# Or using scrapy runspider:
scrapy runspider spider.py -a alias=quotes

# Interactive mode (no alias - will prompt for selection):
python spider.py
```

**Note:** Output file is determined by `output_path` in `websites_input.json`. No need to specify `-o` in command line.

### Chunked Output

If `chunked_size` is set in config, output will be split into multiple files:
- `{output_path}_0.json`
- `{output_path}_1.json`
- etc.

---

## 📋 websites_input.json Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `alias` | string | Yes | Unique identifier for the website |
| `login_url` | string | Yes | URL of the login page |
| `start_url` | string | Yes | Starting URL for scraping |
| `next_url_func` | string | Yes | Dot-path to next URL function (e.g., `next_url_funcs.quote_next_url_func.quote_next_url`) |
| `output_path` | string | Yes | Output file path (without extension) |
| `chunked_size` | integer | No | Number of items per chunk file (0 = no chunking, default) |
| `allowed_domains` | array | Yes | List of allowed domains |

### Chunked Output Example

When `chunked_size` is set to 10:

```
quotes_0.json  # First 10 items
quotes_1.json  # Next 10 items
quotes_2.json  # Next 10 items
...
```

When `chunked_size` is 0 (disabled):

```
quotes.json  # All items in a single file
```

---

## 🆕 How to Add a New Website

### Step 1: Create the Next URL Function

Create a new file in `next_url_funcs/` with the next URL generation logic:

```python
# next_url_funcs/example_next_url_func.py

def example_next_url(response):
    """
    Extract the next page URL from the example website pagination.

    Args:
        response: Scrapy Response object containing the current page

    Returns:
        str: The full URL of the next page, or None if no next page exists
    """
    # CSS selector to find the "next" page link
    next_page = response.css('a.next::attr(href)').get()

    if next_page:
        next_url = response.urljoin(next_page)
        return next_url

    return None
```

### Step 2: Update websites_input.json

Add the new website configuration:

```json
[
    {
        "alias": "quotes",
        "login_url": "http://quotes.toscrape.com/login",
        "start_url": "http://quotes.toscrape.com/",
        "next_url_func": "next_url_funcs.quote_next_url_func.quote_next_url",
        "output_path": "quotes",
        "chunked_size": 0,
        "allowed_domains": ["quotes.toscrape.com"]
    },
    {
        "alias": "example",
        "login_url": "https://example.com/login",
        "start_url": "https://example.com/page/1",
        "next_url_func": "next_url_funcs.example_next_url_func.example_next_url",
        "output_path": "example_output",
        "chunked_size": 50,
        "allowed_domains": ["example.com"]
    }
]
```

### Step 3: Extract Cookies

```bash
python3 extract_cookies.py example
```

### Step 4: Run the Spider

```bash
scrapy runspider spider.py example
```

**Note:** Output file is determined by `output_path` in `websites_input.json` (configured as `example_output`).

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

The spider automatically saves its progress to prevent duplicate scraping:

- **Checkpoint Directory**: `.scrapy/`
- **Checkpoint File**: `{alias}_scraped_pages.json` (e.g., `quotes_scraped_pages.json`)

```bash
# View checkpoint status
cat .scrapy/quotes_scraped_pages.json

# To start fresh (delete checkpoint)
rm -rf .scrapy/
```

**Note:** Each website has its own checkpoint file prefixed with the alias to avoid conflicts when scraping multiple websites.

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
