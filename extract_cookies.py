"""
Cookie Extraction Script for Semi-Automated Scraping

This script extracts cookies from a logged-in browser session for websites configured
in websites_input.json.

Usage:
    python3 extract_cookies.py <alias>

    Or run without arguments to select from a list:
    python3 extract_cookies.py

Arguments:
    alias       - Website alias as defined in websites_input.json (optional)

Examples:
    # For quotes.toscrape.com:
    python3 extract_cookies.py quotes

    # Interactive mode (no alias provided):
    python3 extract_cookies.py
    # Then type a number to select website

The script will:
1. Read the alias and login_url from websites_input.json
2. Launch Chrome browser and navigate to the login URL
3. Wait for you to manually login
4. Extract cookies after login
5. Save cookies as {alias}_cookies.json and terminate
"""

import json
import sys
import os
from playwright.sync_api import sync_playwright


def load_website_configs():
    """
    Load all website configurations from websites_input.json.

    Returns:
        list: List of website configuration dictionaries
    """
    config_path = "websites_input.json"

    if not os.path.exists(config_path):
        print(f"❌ Error: Website configuration file not found: {config_path}")
        return []

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            websites = json.load(f)

        if not isinstance(websites, list):
            print(f"❌ Error: websites_input.json must contain a list of websites")
            return []

        return websites

    except Exception as e:
        print(f"❌ Error: Failed to load website config: {e}")
        return []


def load_website_config_by_alias(alias):
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

    print("\n" + "=" * 60)
    print("📋 Select a website to extract cookies:")
    print("=" * 60)

    for i, website in enumerate(websites, 1):
        alias = website.get('alias', 'Unknown')
        login_url = website.get('login_url', 'No URL')
        print(f"  [{i}] {alias}")
        print(f"      URL: {login_url}")

    print("\n  [0] Cancel")
    print("-" * 60)

    try:
        choice = input("Enter your choice (0-{0}): ".format(len(websites)))
        choice = int(choice)

        if choice == 0:
            print("Cancelled.")
            return None
        elif 1 <= choice <= len(websites):
            return websites[choice - 1]
        else:
            print(f"❌ Error: Invalid choice. Please enter a number between 0 and {len(websites)}")
            return None

    except ValueError:
        print("❌ Error: Please enter a valid number")
        return None
    except KeyboardInterrupt:
        print("\nCancelled.")
        return None


def extract_cookies(alias):
    """Extract cookies from a logged-in browser session for a specific website alias"""

    # Load website config to get login_url
    config = load_website_config_by_alias(alias)
    if not config:
        sys.exit(1)

    login_url = config.get('login_url')
    if not login_url:
        print(f"❌ Error: No login_url found for alias: {alias}")
        sys.exit(1)

    # Generate cookies filename based on alias
    cookies_file = f"{alias}_cookies.json"

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
    print(f"📁 Cookie File: {cookies_file}")
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
        print(f"📝 Next: scrapy runspider spider.py {alias}")
        print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Alias provided as command line argument
        alias = sys.argv[1]
        extract_cookies(alias)
    else:
        # No alias provided - show interactive selection
        config = select_website()

        if config:
            alias = config.get('alias')
            extract_cookies(alias)
        else:
            sys.exit(0)
