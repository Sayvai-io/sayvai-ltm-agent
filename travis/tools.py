import os
import uuid
from typing import List

from datetime import datetime
from langchain_community.tools import TavilySearchResults
from langchain_postgres import PGVector
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
# from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("POSTGRES_USER", "sayvai")
password = os.getenv("POSTGRES_PASSWORD", "8056896266")
database = os.getenv("POSTGRES_DB", "user-conversations")
host = os.getenv("POSTGRES_HOST", "postgres")
port = os.getenv("POSTGRES_PORT", "5432")

# Create the connection string
PGVECTOR_URL = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

try:
    recall_vector_store = PGVector(
        connection=PGVECTOR_URL,
        embeddings=OpenAIEmbeddings(),
        collection_name="document_vectors"  # Optional: specify a collection name
    )
except Exception as e:
    print(f"Failed to connect to vector store: {str(e)}")
    raise ValueError(f"Failed to connect to vector store. {str(e)}"
                     )


def get_user_id(config: RunnableConfig) -> str:
    user_id = config["configurable"].get("user_id")
    if user_id is None:
        raise ValueError("User ID needs to be provided to save a memory.")

    return user_id


# recall_vector_store = InMemoryVectorStore(OpenAIEmbeddings())

@tool
def save_recall_memory(memory: str, config: RunnableConfig) -> str:
    """Save memory to vectorstore for later semantic retrieval."""
    user_id = get_user_id(config)
    document = Document(
        page_content=memory, id=str(uuid.uuid4()), metadata={"user_id": user_id}
    )
    recall_vector_store.add_documents([document])
    return memory


@tool
def search_recall_memories(query: str, config: RunnableConfig) -> List[str]:
    """Search for relevant memories."""
    user_id = get_user_id(config)

    # def _filter_function(doc: Document) -> bool:
    #     return doc.metadata.get("user_id") == user_id

    documents = recall_vector_store.similarity_search(
        query, k=3, filter={"user_id": {"$eq": user_id}}
    )
    return [document.page_content for document in documents]

@tool
def get_date_time() -> str:
    """Get the current date and time.
    :return: Current date and time in the format "YYYY-MM-DD HH:MM:SS".
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 3 tools are defined in this snippet: save_recall_memory, search_recall_memories, and search.
search = TavilySearchResults(max_results=1)
