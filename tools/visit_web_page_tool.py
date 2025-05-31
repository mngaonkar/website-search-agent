# Import things that are needed generically
from pydantic import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Type, Optional, Any
from playwright.sync_api import sync_playwright
import re
from common.logging_config import logger

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class VisitWebPageSyncToolInput(BaseModel):
    url: str = Field(description="Web page URL to visit")
    clean_flag: Optional[bool] = Field(default=False, description="Clean web page text content, this helps to get text from dynamic web page.")

class VisitWebPageSyncTool(BaseTool):
    name: str = "visit_webpage"
    description: str = "Visit a web page and get the text content."
    args_schema: Type[BaseModel] = VisitWebPageSyncToolInput

    def _run(self, url: str, 
             clean_flag=False, 
             run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        logger.info(f"Visiting webpage: {url} with clean_flag={clean_flag}")
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                try:
                    page.goto(url, timeout=30000)  # Set a timeout for navigation
                except Exception as e:
                    logger.error(f"Error navigating to {url}: {str(e)}")
                    return ""
                
                title = page.title()
                
                # Extract the text content of the page
                content = page.content()

                # Extract all text from the page using JavaScript
                all_text = page.evaluate("""
                    () => {
                        // Get all text nodes from the body
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        let text = '';
                        let node;
                        while (node = walker.nextNode()) {
                            text += node.nodeValue.trim() + ' ';
                        }
                        return text;
                    }
                """)

                # Clean up the text (remove extra spaces, newlines, etc.)
                cleaned_text = re.sub(r'\s+', ' ', all_text).strip()

                browser.close()
                if clean_flag:
                    return cleaned_text
                else:
                    return content
            except Exception as e:
                browser.close()
                raise Exception(f"Error visiting webpage: {str(e)}")
            
    def _arun(self, url: str, 
             clean_flag=False, 
             run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        raise NotImplementedError("visit_webpage does not support async")