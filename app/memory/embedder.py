import os
from typing import List
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

class Embedder:
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the HuggingFace embedder with a specified model.
        
        Args:
            model (str): Name of the HuggingFace model to use for embeddings.
                         Default is "all-MiniLM-L6-v2" (good balance of speed/quality).
                         Other options: "all-mpnet-base-v2" (higher quality but slower),
                                       "multi-qa-MiniLM-L6-cos-v1" (optimized for retrieval),
                                       or any other SentenceTransformer model.
        """
        self.model = SentenceTransformer(model)
        self.dim = self.model.get_sentence_embedding_dimension()
        
    def embed_text(self, text: str):
        return self.model.encode([text])[0]

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Takes a list of text chunks and returns a list of vector embeddings.

        Args:
            texts (List[str]): Chunks of text

        Returns:
            List[List[float]]: Corresponding embedding vectors
        """
        # Convert texts to embeddings
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        
        # Convert numpy arrays to lists of floats
        return [embedding.tolist() for embedding in embeddings]