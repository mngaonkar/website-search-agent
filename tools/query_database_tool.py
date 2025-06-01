
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing import Optional, Type
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os
from common.logging_config import logger
import bm25s
import json

load_dotenv()
MAX_RESULTS = os.environ.get("MAX_RESULTS")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
DOC_LOCATION = os.environ.get("DOC_LOCATION", "transcripts")

class QueryDatabaseToolInput(BaseModel):
    """
    Input model for the QueryDatabaseTool.
    """
    query: str


class QueryDatabaseTool(BaseTool):
    """
    Tool to query a database.
    """

    name: str = "query_database"
    description: str = "A tool to query a vector database. It find matching entries based on similarity search. " \
    "Input should be a text."
    args_schema: Type[BaseModel] = QueryDatabaseToolInput

    max_results: int = int(MAX_RESULTS)  # Default maximum number of results to return
    client: chromadb.PersistentClient = None # ChromaDB client instance
    collections: list = None  # List of collections in the database
    embedding_model: Optional[Type] = None  # Embeddings model, if needed
    db_path: Optional[str] = None  # Path to the database
    bm25_model: Optional[Type] = None  # BM25 model for lexical search

    def _run(self, query: str) -> str:
        """
        Run the tool with the given query.
        """
        sparse_results, dense_results = self._query_vector_store(query)
        if not sparse_results or not dense_results["documents"]:
            return None
        return self._return_search_results(sparse_results, dense_results)

    async def _arun(self, query: str) -> str:
        """
        Asynchronously run the tool with the given query.
        """
        return self._run(query)  # For simplicity, using the synchronous method in this example
    
    def __init__(self, db_path: Optional[str] = None, max_results: int = int(MAX_RESULTS)):
        """
        Initialize the QueryDatabaseTool with a database path and maximum results.
        Args:
            db_path (Optional[str]): Path to the database. If None, defaults to "chroma_db".
            max_results (int): Maximum number of results to return from the query.
        """
        super().__init__()
        self.max_results = max_results
        if db_path is None:
            self.db_path = "chroma_db"
        else:
            self.db_path = db_path

        # Dense vector embeddings model for semantic search
        self.embedding_model = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

        # Load documents from the blog index file
        # Save blog index and text associated as JSON text dump in document
        documents = []
        blog_index_path = os.path.join(DOC_LOCATION, "blog_index.json")
        if not os.path.exists(blog_index_path):
            raise FileNotFoundError(f"Blog index file does not exist: {blog_index_path}")
        
        with open(blog_index_path, "r") as f:
            blog_index = json.load(f)
            for key, value in blog_index.items():
                text = open(os.path.join(DOC_LOCATION, key), 'r').read()
                value["text"] = text  # Add the text to the value
                value_text = json.dumps(value)
                documents.append(value_text)

        # Sparse vector embeddings model with BM25 search for lexical search
        self.bm25_model = bm25s.BM25(
            corpus=documents
        )
        self.bm25_model.index(bm25s.tokenize(documents))
    
    def _query_vector_store(self, query: str) -> list:
        """Function to query the vector store."""

        # Query the BM25 model for lexical search
        sparse_results = {}
        results, scores = self.bm25_model.retrieve(bm25s.tokenize(query), k=self.max_results)
        for i in range(len(results[0])):
            try:
                result_json = json.loads(results[0, i])
                link = result_json.get("link", None)
                if link is not None:
                    sparse_results[link] = {"link": link, "score": scores[0, i]}
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from BM25 result: {e}")
                continue
        logger.info(f"BM25 search results: {sparse_results}")

        # Query the ChromaDB vector store for semantic search
        self.client = chromadb.PersistentClient(path=self.db_path)

        # Verify the client is initialized by listing collections (optional)
        self.collections = self.client.list_collections()
        logger.info(f"Collections in the database: {self.collections}")

        if len(self.collections) == 0:
            raise ValueError("No collections found in the database. Ensure the database is initialized correctly.")
        
        logger.info(f"Collections in the database: {len(self.collections)}")
        dense_results = self.client.get_collection(self.collections[0].name).query(
            query_embeddings=[self.embedding_model.embed_query(query)],  # Convert query to embeddings
            n_results=self.max_results  # Number of results to return
        )

        return sparse_results, dense_results

    def _return_search_results(self, sparse_results: dict, dense_results: dict) -> None:
        """Function to print search results."""
        links = set()
        logger.info(f"Processing sparse results: {sparse_results}")
        results_str = ""

        for i, result in enumerate(dense_results["documents"][0]):
            distance = dense_results['distances'][0][i]
            link = dense_results['metadatas'][0][i]["link"]
            logger.info(f"Result {i+1}: {link} (Distance: {distance})")

            if link in sparse_results:
                sparse_results[link]["score"] = sparse_results[link]["score"] * 2  # Boost the score if it exists in sparse results
                logger.info(f"Updated score for {link}: {sparse_results[link]['score']}")
                continue

            links.add(link)
            results_str += f"{dense_results['metadatas'][0][i]["link"]}\n"
        
        if results_str == "":
            results_str = "No results found."

        final_result = [[x["link"], x["score"]] for x in sparse_results.values()]
        final_result.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Final results: {final_result}")
        return "\n".join([x[0] for x in final_result])  # Return the results as a string
        

if __name__ == "__main__":
    # Example usage
    tool = QueryDatabaseTool(db_path="chroma_db", max_results=5)
    query = "data management"
    result = tool.invoke(input={"query": query})
