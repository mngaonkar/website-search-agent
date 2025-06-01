
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
import hashlib
import shutil
from common.logging_config import logger

def download_transcripts_func(state: GraphState) -> None:
    """Download transcripts from the provided content.
    Args:
        content (str): The HTML content to search for Atom feed links.
    """
    logger.debug(f"state = {state}")  # Print the first 100 characters of content for debugging
    links = json.loads(state["messages"][-1].content)
    if not isinstance(links, list):
        raise ValueError("Expected 'links' to be a list, but got: {}".format(type(links)))

    blog_index = {}
    visited_links = set()
    hash_set = set()

    # Create the transcripts directory if it doesn't exist
    if os.path.exists("transcripts"):
        logger.info("Transcripts directory already exists, removing it.")
        shutil.rmtree("transcripts")

    os.makedirs("transcripts")
    logger.info("Created transcripts directory.")


    # Traverse all the links and download the transcripts
    for link in links:
        if link in visited_links:
            logger.info(f"Skipping already visited link: {link}")
            continue
        visited_links.add(link)
        logger.info(f"Processing link: {link}")

        # Visit the web page and get the content
        content = VisitWebPageSyncTool().invoke(input={"url": link, "clean_flag": False})

        # Find the transcript link in the content
        transcript_link = extract_transcript_link_func(content)
        logger.info(f"transcript_link = {transcript_link}")
        if transcript_link is not None:
            web_content = VisitWebPageSyncTool().invoke(input={"url":transcript_link, "clean_flag":True})
            transcript_content = extract_transcript_content_func(web_content)

            # Calculate hash of the transcript content to avoid duplicates
            if not transcript_content:
                logger.warning(f"No transcript content found for link: {link}")
                continue
            
            hash_val = hashlib.sha256(transcript_content.encode('utf-8')).hexdigest()
            if hash_val in hash_set:
                logger.info(f"Transcript content already exists for link: {link}, skipping.")
                continue
            hash_set.add(hash_val)
            logger.info(f"Transcript content found for link: {link}")

            title = link.replace(":", "_").replace("/", "_").replace(".", "_") # Replace special characters in the link
            title = f"{title}.txt"
            with open(os.path.join("transcripts", title), "w") as f:
                f.write(transcript_content)
                logger.info(f"Transcript content saved to {title}")
            
            blog_index[title] = {
                "title": title,
                "link": link,
                "transcript_link": transcript_link
            }

    # Save the blog index to a JSON file
    with open("transcripts/blog_index.json", "w") as f:
        json.dump(blog_index, f, indent=4)
        logger.info("Blog index saved to transcripts/blog_index.json")

    logger.info("All transcripts downloaded and saved.")