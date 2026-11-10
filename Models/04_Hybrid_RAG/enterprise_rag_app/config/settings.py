import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "BHU LOKA Enterprise Hybrid RAG"
    version: str = "3.0.0"
    target_city: str = "Patna, Bihar, India"
    target_coords: tuple = (25.594, 85.137)
    rrf_k: int = 60
    top_k: int = 3
    embedding_dim: int = 384
    transformer_model: str = "all-MiniLM-L6-v2"
    enable_transformer: bool = True
    preload_transformer: bool = False
    data_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Data", "08_Processed_Outputs"))
    crime_data_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "Data", "09_Crime_Safety", "patna_crime_safety_index.json"))
    embedding_cache_path: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "embeddings", "doc_embeddings_minilm.npz"))


settings = Settings()
