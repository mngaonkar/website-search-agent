from typing import Any, Optional, Type
from pydantic import BaseModel, Field
from bs4 import BeautifulSoup
from langchain.tools import BaseTool

def extract_transcript_link_func(content: str) -> Any:
    # Parse the HTML
    soup = BeautifulSoup(content, 'html.parser')

    # Find the anchor tag after the <b>SHOW TRANSCRIPT: </b>
    transcript_tag = soup.find('b', string="SHOW TRANSCRIPT: ")
    if transcript_tag is None:
        print("Transcript tag not found.")
        return None
    link_tag = transcript_tag.find_next('a')

    # Extract the href attribute
    transcript_url = link_tag['href'] if link_tag else None

    print("Transcript URL:", transcript_url)
    return transcript_url

