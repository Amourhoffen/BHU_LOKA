from typing import Optional
import numpy as np

try:
    import faiss
    _FAISS_AVAILABLE = True
except Exception:
    faiss = None
    _FAISS_AVAILABLE = False


class _NumpyIndexFlatIP:
    """Seamless pure-numpy fallback when FAISS C++ OpenMP runtime DLL is unavailable."""
    def __init__(self, dim: int):
        self.dim = dim
        self.vectors = None

    def add(self, x: np.ndarray):
        if self.vectors is None:
            self.vectors = np.ascontiguousarray(x, dtype=np.float32)
        else:
            self.vectors = np.vstack([self.vectors, np.ascontiguousarray(x, dtype=np.float32)])

    def search(self, q: np.ndarray, k: int):
        if self.vectors is None:
            return np.zeros((q.shape[0], k), dtype=np.float32), -np.ones((q.shape[0], k), dtype=int)
        scores = np.dot(self.vectors, q.T).T
        n_avail = min(k, scores.shape[1])
        top_indices = np.argsort(-scores, axis=1)[:, :n_avail]
        top_scores = np.take_along_axis(scores, top_indices, axis=1)
        if n_avail < k:
            pad_len = k - n_avail
            top_indices = np.pad(top_indices, ((0, 0), (0, pad_len)), constant_values=-1)
            top_scores = np.pad(top_scores, ((0, 0), (0, pad_len)), constant_values=-1.0)
        return top_scores, top_indices


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
        if _FAISS_AVAILABLE and faiss is not None:
            self.index = faiss.IndexFlatIP(self.dim)
        else:
            self.index = _NumpyIndexFlatIP(self.dim)
        self.index.add(emb)
        self.doc_store = {i: doc for i, doc in enumerate(documents)}

    def build_transformer_index(self, embeddings: Optional[np.ndarray]):
        if embeddings is None or embeddings.shape[0] == 0:
            return
        emb = np.ascontiguousarray(embeddings, dtype=np.float32)
        dim = int(emb.shape[1])
        if _FAISS_AVAILABLE and faiss is not None:
            t_idx = faiss.IndexFlatIP(dim)
        else:
            t_idx = _NumpyIndexFlatIP(dim)
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
