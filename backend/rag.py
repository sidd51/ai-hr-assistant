
#   HR Policy PDFs/Text files
#        ↓
#   LlamaIndex loads + chunks them
#        ↓
#   Embeddings generated (HuggingFace, free)
#        ↓
#   ChromaDB stores the vectors
#        ↓
#   Agent can now answer "What is the leave policy?"


import os
import chromadb
from dotenv import load_dotenv

from llama_index.core import (
  VectorStoreIndex,
  SimpleDirectoryReader,
  StorageContext,
)

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings


load_dotenv()

POLICIES_PATH = os.getenv("POLICIES_PATH" , "policies/")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma_store")

def _get_embed_model():
  """ 
  Free local embeddings via HuggingFace.
  'all-MiniLM-L6-v2' is small, fast, and great for semantic search.
  Downloads once (~90MB), cached after that.
  """
  return HuggingFaceEmbedding(model_name = "sentence-transformers/all-MiniLM-L6-v2")


def build_index():
  """
  Loads all policy files → chunks them → embeds them → stores in ChromaDB.
  Run this once whenever your policy files change.


  
  """
  print("Loading policy documemts...")
  documents = SimpleDirectoryReader(POLICIES_PATH).load_data()
  print(f" Laoded{len(documents)} document(s)")

  # ChromaDB client — persists to disk at CHROMA_PATH
  chroma_client     = chromadb.PersistentClient(path= CHROMA_PATH)
  chroma_collection = chroma_client.get_or_create_collection("hr_policies")
  vector_store      = ChromaVectorStore( chroma_collection= chroma_collection)
  storage_context   = StorageContext.from_defaults(vector_store= vector_store)

  # Tell LlamaIndex to use our free HuggingFace embeddings
  Settings.embed_model = _get_embed_model()
  Settings.llm =None # # LlamaIndex won't need its own LLM — our agent handles that
 
  print("Generating embeddings and storing in ChromaDB...")

  index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context,
  )
  print("Index built and saved to:", CHROMA_PATH)
  return index

def load_index():
  """
    Loads the existing ChromaDB index from disk.
    Use this at app startup — much faster than rebuilding.
  """
  chroma_client      = chromadb.PersistentClient( path=CHROMA_PATH)
  chroma_collection  = chroma_client.get_or_create_collection("hr_policies")
  vector_store       = ChromaVectorStore(chroma_collection= chroma_collection)
  storage_context    = StorageContext.from_defaults(vector_store=vector_store)

  Settings.embed_model = _get_embed_model()
  Settings.llm = None

  index = VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context
  )
  return index


def get_query_engine():
    """
    Returns a query engine the LangChain agent will use as a tool.
    similarity_top_k=3 means it retrieves the 3 most relevant chunks.
    """
    index = load_index()
    return index.as_query_engine(similarity_top_k=3)


if __name__ == "__main__":
    # Run this file directly to build the index
    build_index()

    # Test retrieval immediately
    print("\nTesting retrieval...")
    engine = get_query_engine()

    test_questions = [
        "How many days of annual leave do employees get?",
        "What is the maternity leave policy?",
        "How do I submit an expense claim?",
    ]

    for q in test_questions:
        print(f"\nQ: {q}")
        print(f"A: {engine.query(q)}")



