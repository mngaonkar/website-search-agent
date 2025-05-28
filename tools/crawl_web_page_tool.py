from playwright.async_api import async_playwright
from urllib.parse import urlparse, urljoin
from typing import Optional, List, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import asyncio
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CrawlWebPageSyncToolInput(BaseModel):
    url: str = Field(description="Web page URL to crawl")
    max_depth: Optional[int] = Field(default=2, description="Maximum depth to crawl.")


class CrawlWebPageSyncTool(BaseTool):
    name: str = "crawl_web_page"
    description: str = "Crawl a web page and return all links found up to a specified depth."
    args_schema: Type[BaseModel] = CrawlWebPageSyncToolInput

    def _run(self, url: str, max_depth: int = 10) -> List[str]:
        """Crawl a web page and return all links found up to a specified depth."""
        raise NotImplementedError("This tool is designed to be used asynchronously. Use the async version instead.")
    
    async def _arun(self, url: str, max_depth: int = 2) -> List[str]:
        """Asynchronous version of the crawl_web_page method."""
        return await crawl_web_page(url, max_depth)
    

async def crawl_web_page(url: str, max_depth: int = 2) -> list:
    """Crawl a web page and return all links found up to a specified depth.
    Args:
        url (str): The URL of the web page to crawl.
        max_depth (int): The maximum depth to crawl. Default is 2.
    Returns:
        list: A list of unique links found on the web page."""
    visited = set()
    links = []

    async def crawl(url: str, depth: int):
        if depth > max_depth or url in visited:
            return
        visited.add(url)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle", timeout=10000)

                page_links = await page.query_selector_all('a[href]')
                logger.info(f"Visiting {url} at depth {depth}, found {len(page_links)} links.")
                for link in page_links:
                    href = await link.get_attribute('href')
                    if href:
                        full_url = urljoin(url, href)
                        parsed_url = urlparse(full_url)
                        if parsed_url.scheme in ['http', 'https']:
                            links.append(full_url)
                            crawl(full_url, depth + 1)
            except Exception as e:
                logger.info(f"Error visiting {url}: {e}")
            finally:
                await browser.close()

    await crawl(url, 0)
    return list(set(links))  # Return unique links

async def main():
    url = "https://www.thecloudcast.net"
    max_depth = 2
    links = await crawl_web_page(url, max_depth)
    logger.info(f"Crawled {len(links)} links from {url} up to depth {max_depth}.")
    for link in links:
        logger.info(link)

if __name__ == "__main__":
   asyncio.run(main())