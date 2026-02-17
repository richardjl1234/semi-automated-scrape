"""
Cookie Extraction Script for Semi-Automated Scraping

This script is designed to work with any website. Each website should have:
- A dedicated spider script named {alias}_spider.py
- A settings folder named {alias}/
- Cookie file: {alias}/cookies.json
- Output data file: {alias}.json

Usage:
    python3 extract_cookies.py <alias> <login_url>
    
Arguments:
    alias       - Website alias (e.g., quotes, example, mysite)
    login_url   - Full login URL for the target website
    
Examples:
    # For quotes.toscrape.com:
    python3 extract_cookies.py quotes http://quotes.toscrape.com/login
    
    # For any other website:
    python3 extract_cookies.py mysite https://example.com/login

The script will:
1. Accept alias and URL as command line arguments
2. Launch Chrome browser and navigate to the URL
3. Wait for you to manually login
4. Extract cookies after login
5. Save cookies as {alias}_cookies.json and terminate
"""

import json
import sys
import os
from playwright.sync_api import sync_playwright


def extract_cookies(alias, login_url):
    """Extract cookies from a logged-in browser session for a specific website alias"""
    
    # Generate cookies filename based on alias
    cookies_file = f"{alias}/cookies.json"
    
    # Ensure the alias directory exists
    os.makedirs(alias, exist_ok=True)
    
    # Validate alias
    if not alias:
        print("❌ Error: No alias provided!")
        print("\nUsage: python3 extract_cookies.py <alias> <login_url>")
        print("Example: python3 extract_cookies.py quotes http://quotes.toscrape.com/login")
        sys.exit(1)
    
    # Validate alias format (alphanumeric and underscores only)
    if not all(c.isalnum() or c == '_' for c in alias):
        print("❌ Error: Invalid alias format!")
        print("Alias must contain only alphanumeric characters and underscores.")
        sys.exit(1)
    
    # Validate URL format
    if not login_url.startswith(("http://", "https://")):
        print("❌ Error: Invalid URL format!")
        print("URL must start with http:// or https://")
        sys.exit(1)
    
    print("=" * 60)
    print("🍪 Semi-Automated Cookie Extraction")
    print("=" * 60)
    print(f"\n🌐 Target Website Alias: {alias}")
    print(f"📍 Target URL: {login_url}")
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
        with open(cookies_file, 'w') as f:
            json.dump(all_cookies, f, indent=2)
        
        print(f"\n✅ Cookies saved to: {cookies_file}")
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
        print(f"📝 Next: Run scrapy runspider {alias}_spider.py -o {alias}.json")
        print("=" * 60)


if __name__ == "__main__":
    # Get alias and URL from command line arguments
    if len(sys.argv) < 3:
        print("❌ Error: Missing arguments!")
        print("\nUsage: python3 extract_cookies.py <alias> <login_url>")
        print("Example: python3 extract_cookies.py quotes http://quotes.toscrape.com/login")
        sys.exit(1)
    
    alias = sys.argv[1]
    login_url = sys.argv[2]
    extract_cookies(alias, login_url)
