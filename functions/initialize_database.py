from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import os
import json
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import logging
from common.common import GraphState

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

load_dotenv()

DOC_LOCATION = os.environ.get("DOC_LOCATION")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP"))

def initialize_database(state: GraphState) -> None:
    """
    Initializes the database by loading documents retrieved by web crawler.
    """
    doc_location = DOC_LOCATION
    
    # Create a text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, 
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""])

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

    # Initialize the vector store with the documents
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma.from_documents(
        documents=doc_list,
        embedding=embeddings,
        persist_directory="chroma_db"
    )

if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")