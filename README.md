# 🍀 Semi-Automated Web Scraping Project

This project demonstrates a semi-automated approach to web scraping where:
1. **You** manually login to the website
2. **I** extract cookies and build a Scrapy spider
3. **We** investigate the page structure together
4. **The spider** scrapes data from the logged-in state

## 📁 Project Structure

```
python-scrape/
├── extract_cookies.py      # Extract cookies from logged-in browser
├── quotes_spider.py        # Scrapy spider for quotes.toscrape.com
├── quotes/
│   └── settings.py         # Scrapy settings
├── scrapy.cfg             # Scrapy configuration
├── cookies.json           # Extracted cookies (generated)
└── quotes.json            # Scraped data (generated)
```

## 🚀 Quick Start

### Step 1: Manual Login

1. Open Chrome and go to: http://quotes.toscrape.com/login
2. Login with: `admin` / `admin`
3. Keep the browser open!

### Step 2: Extract Cookies

```bash
cd /home/richard/shared/jianglei/openclaw/python-scrape
python3 extract_cookies.py
```

This will:
- Connect to your Chrome browser (or launch new one)
- Extract cookies from the logged-in session
- Save to `cookies.json`

### Step 3: Run the Spider

```bash
cd /home/richard/shared/jianglei/openclaw/python-scrape
scrapy runspider quotes_spider.py -o quotes.json
```

Or with output to different formats:

```bash
# JSON
scrapy runspider quotes_spider.py -o quotes.json

# CSV
scrapy runspider quotes_spider.py -o quotes.csv

# XML
scrapy runspider quotes_spider.py -o quotes.xml
```

## 📝 Workflow

### Phase 1: Login & Cookie Extraction
```
User → Opens Chrome → Goes to quotes.toscrape.com/login → Logs in
Agent → Runs extract_cookies.py → Gets cookies → Saves to cookies.json
```

### Phase 2: Page Structure Investigation
```
Agent → Uses Playwright to inspect page
     → Identifies CSS selectors for quotes
     → Works with user to refine selectors
     → Updates quotes_spider.py with correct selectors
```

### Phase 3: Scraping
```
Spider → Loads cookies.json
      → Starts from logged-in URL
      → Scrapes all pages
      → Exports to quotes.json
```

## 🔧 Configuration

### Changing the Target Website

Edit `quotes_spider.py`:

```python
class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["your-target-domain.com"]
    start_urls = ["http://your-target-domain.com/protected-page"]
```

### Adding More Data Fields

Edit the `parse` method in `quotes_spider.py`:

```python
for quote in quotes:
    item = {
        'text': quote.css('span.text::text').get(),
        'author': quote.css('span small::text').get(),
        'tags': quote.css('div.tags a.tag::text').getall(),
        # Add more fields here
        'date_added': quote.css('::attr(data-date)').get(),
    }
    yield item
```

## 🛠️ Installation

Using system Chrome (already installed):
```bash
pip3 install playwright scrapy
# No need to download Chromium - using system Google Chrome
```

Verify installation:
```bash
python3 test_install.py
```

## ⚠️ Important Notes

1. **Respect robots.txt** - Always check if scraping is allowed
2. **Rate limiting** - The spider has delays to avoid overloading servers
3. **Legal considerations** - Only scrape sites you have permission to access
4. **Session expiry** - Cookies may expire; re-run extract_cookies.py if needed

## 📚 Resources

- [Scrapy Documentation](https://docs.scrapy.org/)
- [Playwright Python](https://playwright.dev/python/)
- [CSS Selectors](https://www.w3schools.com/cssref/css_selectors.asp)
