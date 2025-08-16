from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_community.embeddings import HuggingFaceEmbeddings


class VectorStore:
    def __init__(self, persist_directory="chroma_db"):
        self.persist_directory = persist_directory
        self.embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Try to load existing Chroma DB or create a new one
        try:
            self.vector_store = Chroma(
                embedding_function=self.embedder,
                persist_directory=self.persist_directory
            )
        except Exception:
            self.vector_store = None  # Will be created with from_documents()

    def index_documents(self, all_chunks):
        """
        all_chunks: list of dicts with 'combined_heading', 'paragraph', 'block_ids', 'page'
        """
        docs = [
            Document(
                page_content=f"{item['paragraph']}",
                metadata={
                    "paragraph": item["paragraph"],
                    "block_ids": ",".join(item["block_ids"]),
                    "page": item["page"],
                    "page_id": item["page_id"]
                }
            )
            for item in all_chunks
        ]

        self.vector_store = Chroma.from_documents(
            documents=docs,
            embedding=self.embedder,
            persist_directory=self.persist_directory
        )
        self.vector_store.persist()

    def add_documents(self, texts_with_metadata: list):
        """
        texts_with_metadata: list of tuples [(text, metadata), ...]
        """
        docs = [Document(page_content=text, metadata=meta) for text, meta in texts_with_metadata]
        self.vector_store.add_documents(docs)
        self.vector_store.persist()

    def retrieve(self, query: str, k=3):
        return self.vector_store.similarity_search_with_score(query, k=k)

    def retrieve_by_vector(self, query_embedding, k=3):
        return self.vector_store.similarity_search_by_vector(query_embedding, k=k)
