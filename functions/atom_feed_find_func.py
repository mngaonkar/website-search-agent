from common.common import GraphState
from bs4 import BeautifulSoup

def atom_feed_find_func(html_content: str) -> list[str]:
    feed_links = []
    soup = BeautifulSoup(html_content, 'html.parser')
    # Find all <a> tags with "feed" in href
    for link in soup.find_all('a', href=lambda x: x and 'feed' in x.lower()):
        feed_links.append(link.get('href'))
    
    print(f"Found {len(feed_links)} feed links.")
    return feed_links

