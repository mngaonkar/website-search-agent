
from functions.atom_feed_find_func import atom_feed_find_func
from functions.atom_feed_read_func import atom_feed_read_func
from tools.visit_web_page_tool import VisitWebPageSyncTool
from functions.extract_transcript_link_func import extract_transcript_link_func
from functions.extract_transcript_content_func import extract_transcript_content_func
import os
import logging
from langchain_core.tools import tool
from common.common import GraphState
import json

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def download_transcripts_func(state: GraphState) -> None:
    """Download transcripts from the provided content.
    Args:
        content (str): The HTML content to search for Atom feed links.
    """
    print(f"state = {state}")  # Print the first 100 characters of content for debugging
    links = json.loads(state["messages"][-1].content)
    if not isinstance(links, list):
        raise ValueError("Expected 'links' to be a list, but got: {}".format(type(links)))

    feed_links = [item for item in links if "feed" in item]

    print("feed links = ", feed_links)
    print("no of atom links = ", len(feed_links))

    blog_index = {}

    # Iterate through each Atom feed link and read the entries
    for link in feed_links:
        response = atom_feed_read_func(link)
        print(f"response = {response}")

        for entry in response:
            logger.info("title = {entry.title}")
            logger.info("link = {entry.link}")
            content = VisitWebPageSyncTool().invoke(input={"url": entry.link, "clean_flag": False})
            transcript_link = extract_transcript_link_func(content)
            logger.info("transcript_link = {transcript_link}")
            if transcript_link is not None:
                transcript = VisitWebPageSyncTool().invoke(input={"url":transcript_link, "clean_flag":True})
                transcript_content = extract_transcript_content_func(transcript)

                # Create the transcripts directory if it doesn't exist
                if os.path.exists("transcripts") is False:
                    os.makedirs("transcripts")
                    logger.info("Created transcripts directory.")
                entry.title = entry.title.replace(" ", "_") + ".txt"  # Replace spaces with underscores and add .txt extension
                with open(os.path.join("transcripts", entry.title), "w") as f:
                    f.write(transcript_content)
                    logger.info(f"Transcript content saved to {entry.title}")
                
                blog_index[entry.title] = {
                    "title": entry.title,
                    "link": entry.link,
                    "transcript_link": transcript_link
                }
    # Save the blog index to a JSON file
    with open("transcripts/blog_index.json", "w") as f:
        json.dump(blog_index, f, indent=4)
        logger.info("Blog index saved to transcripts/blog_index.json")

    logger.info("All transcripts downloaded and saved.")