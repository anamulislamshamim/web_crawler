CRAWLERS = {}

def get_all_crawlers():
    return CRAWLERS.values()

def add_crawler(site_key, crawler):
    CRAWLERS[site_key] = crawler

def get_crawler(site_key):
    return CRAWLERS.get(site_key)

def remove_crawler(site_key):
    return CRAWLERS.pop(site_key, None)