"""
Next URL Function for quotes.toscrape.com

This function extracts the next page URL from the pagination navigation.
It is designed to work with the common spider.py and is called during
the scraping process to determine the next URL to scrape.

Usage:
    This function is referenced in websites_input.json as:
    "next_url_func": "next_url_funcs.quote_next_url_func.quote_next_url"

The function receives a response object from the Scrapy spider and
returns the next URL string if pagination exists, or None if there
 are no more pages.
"""


def quote_next_url(response):
    """
    Extract the next page URL from the quotes.toscrape.com pagination.

    Args:
        response: Scrapy Response object containing the current page

    Returns:
        str: The full URL of the next page, or None if no next page exists

    Example:
        >>> from scrapy.http import HtmlResponse
        >>> # Simulated response with pagination
        >>> next_url = quote_next_url(response)
        >>> print(next_url)
        'http://quotes.toscrape.com/page/2/'
    """
    # CSS selector to find the "next" page link
    # The pagination uses li.next > a pattern
    next_page = response.css('li.next a::attr(href)').get()

    if next_page:
        # Convert relative URL to absolute URL
        next_url = response.urljoin(next_page)
        return next_url

    return None
