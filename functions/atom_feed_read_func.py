from typing import Any, Optional, Type
from langchain.tools import BaseTool
import feedparser
from pydantic import BaseModel, Field

def atom_feed_read_func(link: str) -> Any:
    feed = feedparser.parse(link)
    if feed.bozo:
        raise ValueError(f"Failed to parse feed: {feed.bozo_exception}")
    
    return feed.entries

