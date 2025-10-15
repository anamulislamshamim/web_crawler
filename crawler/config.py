SITE_CONFIG = {
    # Example config for http://books.toscrape.com/ (demo site)
    "books_toscrape": {
        "start_url": "http://books.toscrape.com/catalogue/page-1.html",
        "pagination": {
            # function to generate next page URL: we'll implement simple pattern
            "type": "pattern", # 'pattern' or 'link'
            "pattern": "http://books.toscrape.com/catalogue/page-{page}.html",
            "start_page": 1,
            "max_pages": None # None => crawl until site stops returning books
        },
        "selectors": {
            # selectors relative to catalog pages and book detail pages
            "book_card": "article.product_pod",
            "book_link": "h3 > a", # attribute href
            # For detail page parsing - CSS selectors
            "name": "div.product_main > h1",
            "price_including_tax": "table.table.table-striped tr:contains('Price (incl. tax)') td",
            "price_excluding_tax": "table.table.table-striped tr:contains('Price (excl. tax)') td",
            "availability": "div.product_main > p.availability",
            "description": "#product_description ~ p", # next sibling
            "category": "ul.breadcrumb li:nth-last-child(2) a",
            "number_of_reviews": "table.table.table-striped tr:contains('Number of reviews') td",
            "rating": "div.product_main > p.star-rating", # class contains rating
            "image": "div.carousel-inner img",
        },
        # optional transform for relative links
        "make_absolute": lambda url: url if url.startswith('http') else 'http://books.toscrape.com/catalogue/' + url.lstrip('../')
    }
}