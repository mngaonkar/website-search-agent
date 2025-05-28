
from langchain_core.documents import Document
from typing import TypedDict

class GraphState(TypedDict):
    query: str
    html_content: str
    messages: any
    results: list[Document]