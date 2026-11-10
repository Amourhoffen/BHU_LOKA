import math
from collections import defaultdict
from rag.reranker import BhuLokaCrossReranker, normalize_query_tokens


class HybridRetriever:
    """
    Production Multi-Stage Sovereign Retriever:
      Stage 1: Sparse BM25Okapi + Dense FAISS Vector Search (Transformer 384-d or SVD fallback),
               fused via Reciprocal Rank Fusion (RRF, k=60).
      Stage 2: Cross-Signal Re-Ranker (`BhuLokaCrossReranker`) re-scoring lexical coverage,
               bigrams, dense similarity, and domain intent alignment.
    """

    def __init__(self, embedder, vector_db, documents: list, rrf_k: int = 60):
        self.embedder = embedder
        self.vector_db = vector_db
        self.documents = documents
        self.rrf_k = rrf_k
        self.reranker = BhuLokaCrossReranker()

        self.tokenized_corpus = [
            normalize_query_tokens(f"{doc.get('title', '')} {doc.get('keywords', '')} {doc.get('content', '')}")
            for doc in documents
        ]
        self.doc_count = len(documents)
        self.avg_doc_len = sum(len(d) for d in self.tokenized_corpus) / max(1, self.doc_count)
        self.doc_freqs = defaultdict(int)
        for doc in self.tokenized_corpus:
            for word in set(doc):
                self.doc_freqs[word] += 1

    def _bm25_score(self, query: str, k1: float = 1.5, b: float = 0.75):
        q_tokens = normalize_query_tokens(query)
        scores = []
        for i, doc in enumerate(self.tokenized_corpus):
            score = 0.0
            doc_len = len(doc)
            counts = defaultdict(int)
            for t in doc:
                counts[t] += 1
            for q in q_tokens:
                if q in self.doc_freqs:
                    idf = math.log(1.0 + (self.doc_count - self.doc_freqs[q] + 0.5) / (self.doc_freqs[q] + 0.5))
                    f = counts[q]
                    denom = f + k1 * (1.0 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
                    score += idf * (f * (k1 + 1.0)) / max(1e-6, denom)
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def retrieve(self, query: str, top_k: int = 3):
        # Stage 1A: Sparse BM25 with multilingual token canonicalization
        bm25_ranked = self._bm25_score(query)
        bm25_map = {idx: sc for idx, sc in bm25_ranked}

        # Stage 1B: Dense Vector Search (use 384-d Transformer FAISS when warmed, else SVD FAISS)
        use_trans = bool(
            getattr(self.embedder, "transformer_ready", False)
            and getattr(self.vector_db, "transformer_index", None) is not None
        )
        q_vec = self.embedder.transform_transformer(query) if use_trans else self.embedder.transform_svd(query)
        dense_results = self.vector_db.search(
            q_vec,
            top_k=min(len(self.documents), 12),
            use_transformer=use_trans,
        )
        vec_map = {r["doc_id"]: r["score"] for r in dense_results}

        # Stage 1C: Reciprocal Rank Fusion (RRF)
        rrf_scores = defaultdict(float)
        for rank, (doc_idx, score) in enumerate(bm25_ranked):
            if score > 0.0:
                rrf_scores[doc_idx] += 1.0 / (self.rrf_k + (rank + 1))

        # Threshold avoids returning gibberish purely from tiny dense noise
        dense_gate = 0.22 if use_trans else 0.25
        for rank, res in enumerate(dense_results):
            if res.get("score", 0.0) > dense_gate or res["doc_id"] in rrf_scores:
                if res.get("score", 0.0) > 0.12:
                    rrf_scores[res["doc_id"]] += 1.0 / (self.rrf_k + (rank + 1))

        # Ensure top BM25 matches are never starved by dense vector bias
        # Build candidate pool from top RRF entries plus guaranteed top BM25 hits
        candidate_set = set([idx for idx, _ in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:14]])
        for b_idx, b_sc in bm25_ranked[:5]:
            if b_sc > 0.0:
                candidate_set.add(b_idx)

        # Stage 1D: Domain-Critical Force-Include for high-specificity queries
        q_tokens_set = set(normalize_query_tokens(query))
        _FORCE_INCLUDE_RULES = [
            ({"land", "zameen", "jamin", "ghar", "kharidne", "flat", "residential", "corridor"}, "doc_india_best_land_corridors"),
            ({"karte", "krte", "features", "capabilities", "capability"}, "doc_capabilities_mission"),
            ({"fake", "nakli", "honest", "source", "provenance", "asli"}, "doc_provenance_honesty_policy"),
        ]
        for trigger_tokens, force_doc_id in _FORCE_INCLUDE_RULES:
            if q_tokens_set & trigger_tokens:
                for doc_idx, doc in enumerate(self.documents):
                    if doc.get("id") == force_doc_id:
                        candidate_set.add(doc_idx)
                        if doc_idx not in rrf_scores:
                            rrf_scores[doc_idx] = 1.0 / (self.rrf_k + 1)
                        break

        if not candidate_set:
            return []

        candidate_ids = list(candidate_set)
        candidates = [
            {
                "doc_id": idx,
                "rrf_score": rrf_scores.get(idx, 0.0),
                "bm25_score": round(bm25_map.get(idx, 0.0), 4),
                "vector_score": round(vec_map.get(idx, 0.0), 4),
                "document": self.documents[idx],
            }
            for idx in candidate_ids
        ]

        # Stage 2: Cross-Signal Re-Ranking
        return self.reranker.rerank(query, candidates, top_k=top_k)
