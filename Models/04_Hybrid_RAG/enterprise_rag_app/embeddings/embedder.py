import hashlib
import os
import threading
from typing import Callable, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD


class SovereignDenseEmbedder:
    """
    Dual-mode Dense Embedder powering FAISS Vector Search:
      1. Primary Neural Mode: Cached `sentence-transformers/all-MiniLM-L6-v2` (384-d Transformer)
         loading strictly from local HuggingFace cache (`local_files_only=True`).
      2. Instant Boot / Offline Fallback: Deterministic TF-IDF (word + char_wb ngrams) + TruncatedSVD,
         ready in <15ms while Transformer weights warm cleanly in the background.
    """

    def __init__(
        self,
        n_components: int = 24,
        model_name: str = "all-MiniLM-L6-v2",
        cache_path: Optional[str] = None,
        enable_transformer: bool = True,
    ):
        self.n_components = n_components
        self.model_name = model_name
        self.cache_path = cache_path
        self.enable_transformer = enable_transformer

        self.word_tfidf = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.is_fitted = False

        self.transformer_model = None
        self.transformer_ready = False
        self.transformer_doc_vecs: Optional[np.ndarray] = None
        self.transformer_dim: int = 384
        self._lock = threading.Lock()
        self._warming = False
        self._qvec_cache: dict[str, np.ndarray] = {}

    @staticmethod
    def _corpus_digest(texts: list[str]) -> str:
        h = hashlib.sha256()
        for t in texts:
            h.update(t.encode("utf-8", errors="ignore"))
            h.update(b"\x00")
        return h.hexdigest()[:16]

    @staticmethod
    def _l2_normalize(arr: np.ndarray) -> np.ndarray:
        norms = np.asarray(np.linalg.norm(arr, axis=-1, keepdims=True), dtype=np.float32)
        safe = np.where(norms == 0.0, 1.0, norms)
        return np.asarray(arr / safe, dtype=np.float32)

    def fit_transform_svd(self, texts: list[str]) -> np.ndarray:
        tfidf_mat = self.word_tfidf.fit_transform(texts)
        mat_shape = getattr(tfidf_mat, "shape", None)
        n_features = int(mat_shape[1]) if (isinstance(mat_shape, tuple) and len(mat_shape) > 1) else self.n_components + 1
        actual_comp = min(self.n_components, max(2, min(len(texts) - 1, n_features - 1)))
        self.svd.n_components = max(2, actual_comp)
        dense_vecs = np.asarray(self.svd.fit_transform(tfidf_mat), dtype=np.float32)
        self.is_fitted = True
        return self._l2_normalize(dense_vecs)

    def fit_transform(self, texts: list[str]) -> np.ndarray:
        """Fit SVD index immediately and load cached 384-d Transformer document vectors if available."""
        svd_vecs = self.fit_transform_svd(texts)
        digest = self._corpus_digest(texts)

        if self.enable_transformer and self.cache_path and os.path.exists(self.cache_path):
            try:
                npz = np.load(self.cache_path, allow_pickle=False)
                if str(npz["digest"]) == digest and int(npz["vecs"].shape[0]) == len(texts):
                    self.transformer_doc_vecs = self._l2_normalize(np.asarray(npz["vecs"], dtype=np.float32))
                    self.transformer_dim = int(self.transformer_doc_vecs.shape[1])
            except Exception:
                self.transformer_doc_vecs = None
        return svd_vecs

    def load_transformer_sync(self, texts: Optional[list[str]] = None) -> bool:
        """Synchronously load local `all-MiniLM-L6-v2` weights and compute/cache doc embeddings."""
        if not self.enable_transformer:
            return False
        with self._lock:
            if self.transformer_ready and self.transformer_model is not None:
                return True
            try:
                os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
                os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
                try:
                    import torch  # type: ignore
                    torch.set_num_threads(min(2, os.cpu_count() or 2))
                except Exception:
                    pass
                from sentence_transformers import SentenceTransformer  # type: ignore

                model = SentenceTransformer(self.model_name, local_files_only=True)
                self.transformer_model = model
                if texts and (self.transformer_doc_vecs is None or len(self.transformer_doc_vecs) != len(texts)):
                    raw_vecs = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
                    vecs = np.asarray(raw_vecs, dtype=np.float32)
                    self.transformer_doc_vecs = self._l2_normalize(vecs)
                    self.transformer_dim = int(vecs.shape[1])
                    if self.cache_path:
                        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
                        np.savez_compressed(
                            self.cache_path,
                            digest=np.array(self._corpus_digest(texts)),
                            vecs=self.transformer_doc_vecs,
                        )
                self.transformer_ready = True
                return True
            except Exception:
                self.transformer_ready = False
                return False

    def start_background_warmup(
        self,
        texts: list[str],
        on_ready: Optional[Callable[[np.ndarray], None]] = None,
    ) -> None:
        """Warm Transformer neural model in a background thread without blocking server startup."""
        if not self.enable_transformer or self.transformer_ready or self._warming:
            return
        self._warming = True

        def _worker():
            ok = self.load_transformer_sync(texts=texts)
            self._warming = False
            vecs = self.transformer_doc_vecs
            if ok and on_ready is not None and vecs is not None:
                try:
                    on_ready(vecs)
                except Exception:
                    pass

        t = threading.Thread(target=_worker, name="BhuLokaTransformerWarmup", daemon=True)
        t.start()

    def active_backend_label(self) -> str:
        if self.transformer_ready and self.transformer_doc_vecs is not None:
            return f"Transformer ({self.model_name}, {self.transformer_dim}-d) + FAISS"
        return f"TF-IDF SVD ({self.svd.n_components}-d) + FAISS"

    def transform_svd(self, query: str) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Embedder must be fitted before transforming queries.")
        tfidf_mat = self.word_tfidf.transform([query])
        dense_vec = np.asarray(self.svd.transform(tfidf_mat), dtype=np.float32)
        return self._l2_normalize(dense_vec)

    def transform_transformer(self, query: str) -> Optional[np.ndarray]:
        if not (self.transformer_ready and self.transformer_model is not None):
            return None
        cached = self._qvec_cache.get(query)
        if cached is not None:
            return cached
        with self._lock:
            cached = self._qvec_cache.get(query)
            if cached is not None:
                return cached
            vec = self.transformer_model.encode([query], show_progress_bar=False, normalize_embeddings=True)
            norm = self._l2_normalize(np.asarray(vec, dtype=np.float32))
            if len(self._qvec_cache) > 256:
                self._qvec_cache.clear()
            self._qvec_cache[query] = norm
            return norm

    def transform(self, query: str) -> np.ndarray:
        """Backwards-compatible dense vector projection."""
        t_vec = self.transform_transformer(query)
        if t_vec is not None:
            return t_vec
        return self.transform_svd(query)
