"""
Cookie Extraction Script for Semi-Automated Scraping

Usage:
    python3 extract_cookies.py <login_url>
    
Example:
    python3 extract_cookies.py http://quotes.toscrape.com/login
    python3 extract_cookies.py https://example.com/login

The script will:
1. Accept a URL as command line argument (required)
2. Launch Chrome browser and navigate to the URL
3. Wait for you to manually login
4. Extract cookies after login
5. Save cookies and terminate
"""

import json
import sys
import os
from playwright.sync_api import sync_playwright

# Default cookies file
COOKIES_FILE = "cookies.json"


def extract_cookies(login_url):
    """Extract cookies from a logged-in browser session"""
    
    # Validate URL
    if not login_url:
        print("❌ Error: No URL provided!")
        print("\nUsage: python3 extract_cookies.py <login_url>")
        print("Example: python3 extract_cookies.py http://quotes.toscrape.com/login")
        sys.exit(1)
    
    # Validate URL format
    if not login_url.startswith(("http://", "https://")):
        print("❌ Error: Invalid URL format!")
        print("URL must start with http:// or https://")
        sys.exit(1)
    
    print("=" * 60)
    print("🍪 Semi-Automated Cookie Extraction")
    print("=" * 60)
    print(f"\n🌐 Target URL: {login_url}")
    print("\n📋 Instructions:")
    print("1. Browser will open to the login page")
    print("2. Enter your username and password to login")
    print("3. After successful login, press Enter to extract cookies")
    print("4. Cookies will be saved and browser will close\n")
    
    with sync_playwright() as p:
        # Launch Chrome with persistent context
        print("🔄 Launching Chrome browser...")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir="/tmp/playwright-cookie-extraction",
            headless=False,  # Show browser for manual login
            viewport={"width": 1280, "height": 800},
            executable_path="/usr/bin/google-chrome",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        
        # Create new page and navigate to login URL
        page = context.new_page()
        print(f"📱 Navigating to: {login_url}")
        page.goto(login_url)
        
        # Wait for user to login
        print("\n⏳ Waiting for you to login...")
        print("   Press Enter in this terminal after successful login...")
        input()
        
        # Wait a moment for cookies to be set
        page.wait_for_timeout(1000)
        
        # Get cookies
        all_cookies = context.cookies()
        
        if not all_cookies:
            print("\n⚠️  Warning: No cookies found!")
            print("   Make sure you have successfully logged in.")
        
        # Save cookies to file
        with open(COOKIES_FILE, 'w') as f:
            json.dump(all_cookies, f, indent=2)
        
        print(f"\n✅ Cookies saved to: {COOKIES_FILE}")
        print(f"📊 Total cookies: {len(all_cookies)}")
        
        # Show cookies info
        if all_cookies:
            print("\n🍪 Cookie details:")
            for cookie in all_cookies:
                name = cookie.get('name', 'N/A')
                value = cookie.get('value', 'N/A')
                domain = cookie.get('domain', 'N/A')
                print(f"   - {name}: {value[:30]}... ({domain})")
        
        # Close browser
        context.close()
        
        print("\n" + "=" * 60)
        print("🎉 Cookie extraction complete!")
        print(f"📝 Run: scrapy runspider quotes_spider.py -o quotes.json")
        print("=" * 60)


if __name__ == "__main__":
    # Get URL from command line argument
    if len(sys.argv) < 2:
        print("❌ Error: Missing URL argument!")
        print("\nUsage: python3 extract_cookies.py <login_url>")
        print("Example: python3 extract_cookies.py http://quotes.toscrape.com/login")
        sys.exit(1)
    
    login_url = sys.argv[1]
    extract_cookies(login_url)
