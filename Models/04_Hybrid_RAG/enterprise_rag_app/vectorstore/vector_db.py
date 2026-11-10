from typing import Optional
import numpy as np
import faiss


class SovereignVectorDB:
    """
    Dual-Index FAISS Vector Store (`IndexFlatIP` Cosine Similarity via L2-Normalized Inner Product):
      - `transformer_index`: 384-dim SentenceTransformer vector index
      - `svd_index`        : Instant fallback dense SVD index
    """

    def __init__(self, dim: int = 384):
        self.dim = dim
        self.index = None
        self.transformer_index = None
        self.doc_store: dict = {}

    def build_index(self, embeddings: np.ndarray, documents: list):
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        self.dim = int(emb.shape[1])
        self.index = faiss.IndexFlatIP(self.dim)
        self.index.add(emb)
        self.doc_store = {i: doc for i, doc in enumerate(documents)}

    def build_transformer_index(self, embeddings: Optional[np.ndarray]):
        if embeddings is None or embeddings.shape[0] == 0:
            return
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        t_idx = faiss.IndexFlatIP(int(emb.shape[1]))
        t_idx.add(emb)
        self.transformer_index = t_idx

    def search(self, query_vec: np.ndarray, top_k: int = 10, use_transformer: bool = False):
        target_index = self.transformer_index if (use_transformer and self.transformer_index is not None) else self.index
        if target_index is None:
            raise RuntimeError("FAISS vector index not built.")
        q = np.ascontiguousarray(query_vec, dtype=np.float32)
        if q.ndim == 1:
            q = q.reshape(1, -1)
        scores, indices = target_index.search(q, top_k)
        results = []
        for idx, score in zip(indices[0], scores[0]):
            if idx != -1 and idx in self.doc_store:
                results.append({
                    "doc_id": int(idx),
                    "score": float(score),
                    "document": self.doc_store[int(idx)],
                })
        return results
