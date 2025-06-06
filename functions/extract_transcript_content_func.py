from typing import Any, Optional, Type
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
import re
import json
from common.logging_config import logger

def extract_transcript_content_func(html_content: str) -> str:
    """Extract transcript context text from HTML content."""
    text_content = []
    matches = re.findall(r'DOCS_modelChunk\s=\s\[(.*?),\s*{', html_content, re.DOTALL)
    if matches is None:
        logger.warning("No match found in the HTML content.")
        return ""
    else:
        logger.info("Match found in the HTML content.")
        for match in matches:
            data = json.loads(match)
            if "s" in data:
                text_content.append(data["s"])

    return ' '.join(text_content)
    
