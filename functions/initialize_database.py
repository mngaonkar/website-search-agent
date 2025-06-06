from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import json
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import logging
from common.common import GraphState
import shutil
from common.logging_config import logger

load_dotenv()

DOC_LOCATION = os.environ.get("DOC_LOCATION")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP"))
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")

def initialize_database(state: GraphState) -> None:
    """
    Initializes the database by loading documents retrieved by web crawler.
    """
    doc_location = DOC_LOCATION

    # Create a text splitter
    logger.info(f"Creating text splitter with chunk size {CHUNK_SIZE} and overlap {CHUNK_OVERLAP}.")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP)

    # Load file index
    logger.info(f"Loading blog index from {doc_location}/blog_index.json")
    if not os.path.exists(os.path.join(doc_location, "blog_index.json")):
        raise FileNotFoundError(f"File index file does not exist: {doc_location}")
    
    try:
        with open(os.path.join(doc_location, "blog_index.json"), "r") as f:
            blog_index = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error decoding JSON from file index: {e}")
    
    # Load text files from directory and split them into chunks
    documents = []
    for file in os.listdir(DOC_LOCATION):
        if not file.endswith('.txt'):
            continue

        with open(os.path.join(DOC_LOCATION, file), 'r') as f:
            text = f.read()
            doc = text_splitter.split_text(text)
            documents.append({
                "text": doc,
                "metadata": {"source": os.path.join(DOC_LOCATION, file),
                            "link": blog_index[file]["link"],}
            })
    
    doc_list = [Document(page_content=json.dumps(doc["text"]), metadata=doc["metadata"]) for doc in documents]

    if os.path.exists("chroma_db"):
        logger.warning("Chroma database already exists, removing it.")
        try:
            # Remove the existing Chroma database directory
            shutil.rmtree("chroma_db")
        except Exception as e:
            logger.error(f"Error removing existing Chroma database: {e}")
            raise

    # Initialize the vector store with the documents
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    vector_store = Chroma.from_documents(
        documents=doc_list,
        embedding=embeddings,
        persist_directory="chroma_db"
    )

if __name__ == "__main__":
    initialize_database(None)
    logger.info("Database initialized successfully.")