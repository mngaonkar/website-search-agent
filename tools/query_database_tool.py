
from langchain.tools import BaseTool
from pydantic import BaseModel
from typing import Optional, Type
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import os

load_dotenv()
MAX_RESULTS = os.environ.get("MAX_RESULTS")

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

    max_results: int = MAX_RESULTS  # Default maximum number of results to return
    client: chromadb.PersistentClient = None # ChromaDB client instance
    collections: list = None  # List of collections in the database
    embedding_model: Optional[Type] = None  # Embeddings model, if needed

    def _run(self, query: str) -> str:
        """
        Run the tool with the given query.
        """
        results = self._query_vector_store(query)
        if not results or not results["documents"]:
            return None
        self._print_search_results(results)
        return results["documents"][0]

    async def _arun(self, query: str) -> str:
        """
        Asynchronously run the tool with the given query.
        """
        return self._run(query)  # For simplicity, using the synchronous method in this example
    
    def __init__(self, db_path: Optional[str] = None, max_results: int = 5):
        """
        Initialize the QueryDatabaseTool with a database path and maximum results.
        Args:
            db_path (Optional[str]): Path to the database. If None, defaults to "chroma_db".
            max_results (int): Maximum number of results to return from the query.
        """
        super().__init__()
        self.max_results = max_results
        if db_path is None:
            db_path = "chroma_db"
        self.client = chromadb.PersistentClient(path=db_path)
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Verify the client is initialized by listing collections (optional)
        self.collections = self.client.list_collections()
        print(f"Collections in the database: {self.collections}")
    
    def _query_vector_store(self, query: str) -> list:
        """Function to query the vector store."""
        if len(self.collections) == 0:
            raise ValueError("No collections found in the database. Ensure the database is initialized correctly.")
        
        print(f"Collections in the database: {len(self.collections)}")
        results = self.client.get_collection(self.collections[0].name).query(
            query_embeddings=[self.embedding_model.embed_query(query)],  # Convert query to embeddings
            n_results=self.max_results  # Number of results to return
        )

        return results

    def _print_search_results(self, results) -> None:
        """Function to print search results."""
        print("Search results:")
        for i, result in enumerate(results["documents"][0]):
            print(f"Result {i+1}:")
            print(f"{result[:100]}... (Distance: {results['distances'][0][i]})")
            print(f"metadata: {results['metadatas'][0][i]}")
        
        

if __name__ == "__main__":
    # Example usage
    tool = QueryDatabaseTool(db_path="chroma_db", max_results=5)
    query = "data management"
    result = tool.invoke(input={"query": query})
