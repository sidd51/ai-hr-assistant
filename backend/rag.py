import os

import chromadb
from dotenv import load_dotenv
from llama_index.core import Settings, SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

POLICIES_PATH = os.getenv("POLICIES_PATH", "policies/")
CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma_store")


def _get_embed_model():
    """
    Free local embeddings via HuggingFace.
    Downloads once and is cached after that.
    """
    return HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def build_index():
    """
    Loads policy files, generates embeddings, and stores them in ChromaDB.
    Run this whenever the policy files change.
    """
    print("Loading policy documents...")
    documents = SimpleDirectoryReader(POLICIES_PATH).load_data()
    print(f"Loaded {len(documents)} document(s)")

    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("hr_policies")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    Settings.embed_model = _get_embed_model()

    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )
    print("Index built and saved to:", CHROMA_PATH)
    return index


def load_index():
    """
    Loads the existing ChromaDB index from disk.
    Use this at app startup or on demand.
    """
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("hr_policies")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    Settings.embed_model = _get_embed_model()

    return VectorStoreIndex.from_vector_store(
        vector_store,
        storage_context=storage_context,
    )


def retrieve_policy_context(query: str, top_k: int = 3) -> list[str]:
    """
    Retrieves the most relevant policy chunks for a user question.
    """
    retriever = load_index().as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)

    chunks = []
    for item in nodes:
        text_value = None

        if hasattr(item, "node"):
            node = item.node
            if hasattr(node, "get_content"):
                text_value = node.get_content()
            elif hasattr(node, "get_text"):
                text_value = node.get_text()
            else:
                text_value = getattr(node, "text", None)
        elif hasattr(item, "get_content"):
            text_value = item.get_content()
        elif hasattr(item, "get_text"):
            text_value = item.get_text()
        else:
            text_value = getattr(item, "text", None)

        if text_value:
            chunks.append(text_value.strip())

    return chunks


if __name__ == "__main__":
    build_index()

    print("\nTesting retrieval...")
    test_questions = [
        "How many days of annual leave do employees get?",
        "What is the maternity leave policy?",
        "How do I submit an expense claim?",
    ]

    for question in test_questions:
        print(f"\nQ: {question}")
        for index, chunk in enumerate(retrieve_policy_context(question), start=1):
            print(f"Excerpt {index}: {chunk[:250]}...")

def get_or_build_index():
    """
    Checks if index exists on disk.
    Builds it fresh if not (first deploy).
    Loads from disk if it does (subsequent restarts).
    """
    if not os.path.exists(CHROMA_PATH) or not os.listdir(CHROMA_PATH):
        print("No index found — building from scratch...")
        build_index()
    return load_index()