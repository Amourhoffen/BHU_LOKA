from typing import Optional
from config.settings import settings
from ingestion.loader import KnowledgeLoader
from embeddings.embedder import SovereignDenseEmbedder
from vectorstore.vector_db import SovereignVectorDB
from rag.retriever import HybridRetriever
from rag.prompt_builder import PromptBuilder
from rag.generator import LocalSovereignGenerator
from rag.reranker import plan_agent2_map_actions


class RAGPipeline:
    """
    End-to-End Dual-Agent Enterprise RAG Pipeline orchestrating:
      Agent 1: Ingestion -> BM25 + Transformer Vector Search (FAISS) -> RRF -> Cross Re-Ranker -> Multilingual Grounded Synthesis
      Agent 2: Autonomous Cartographic Director returning synchronized 3D/2D Map & Auto-Hologram Actions
    """

    def __init__(self, preload_transformer: Optional[bool] = None, enable_transformer: Optional[bool] = None):
        self.loader = KnowledgeLoader(settings.crime_data_path)
        use_trans = settings.enable_transformer if enable_transformer is None else enable_transformer
        do_preload = settings.preload_transformer if preload_transformer is None else preload_transformer

        self.embedder = SovereignDenseEmbedder(
            n_components=24,
            model_name=settings.transformer_model,
            cache_path=settings.embedding_cache_path,
            enable_transformer=use_trans,
        )
        self.vector_db = SovereignVectorDB(dim=settings.embedding_dim)
        self.generator = LocalSovereignGenerator()
        self.documents: list[dict] = []
        self._doc_texts: list[str] = []
        self.retriever: HybridRetriever = self._initialize(preload_transformer=do_preload)

    def _initialize(self, preload_transformer: bool = False) -> HybridRetriever:
        self.documents = self.loader.load_all_documents()
        self._doc_texts = [
            f"{doc.get('title', '')} {doc.get('keywords', '')} {doc.get('content', '')}"
            for doc in self.documents
        ]
        svd_embs = self.embedder.fit_transform(self._doc_texts)
        self.vector_db.build_index(svd_embs, self.documents)

        if self.embedder.transformer_doc_vecs is not None:
            self.vector_db.build_transformer_index(self.embedder.transformer_doc_vecs)

        if preload_transformer and self.embedder.enable_transformer:
            self.ensure_transformer_ready()

        return HybridRetriever(
            embedder=self.embedder,
            vector_db=self.vector_db,
            documents=self.documents,
            rrf_k=settings.rrf_k,
        )

    def ensure_transformer_ready(self) -> bool:
        """Load local SentenceTransformer (`all-MiniLM-L6-v2`) synchronously & activate 384-d FAISS index."""
        ok = self.embedder.load_transformer_sync(texts=self._doc_texts)
        if ok and self.embedder.transformer_doc_vecs is not None:
            self.vector_db.build_transformer_index(self.embedder.transformer_doc_vecs)
        return ok

    def start_background_transformer_warmup(self) -> None:
        """Non-blocking background Transformer warmup for FastAPI daemon runtime."""
        self.embedder.start_background_warmup(
            texts=self._doc_texts,
            on_ready=lambda vecs: self.vector_db.build_transformer_index(vecs),
        )

    def run(self, query: str, top_k: int = 3, language_override: Optional[str] = None):
        retrieved = self.retriever.retrieve(query, top_k=top_k)
        encoder_label = self.embedder.active_backend_label()
        PromptBuilder.build_rag_prompt(query, retrieved)
        norm_lang = language_override if language_override in {"en", "hi", "hinglish"} else None
        answer, lang = self.generator.generate(
            query,
            retrieved,
            encoder_label=encoder_label,
            language_override=norm_lang,
        )
        agent2_actions = plan_agent2_map_actions(query, retrieved)

        provenance_list = list(
            dict.fromkeys(
                r["document"].get("source_provenance", r["document"].get("category", "Verified Local Archive"))
                for r in retrieved
            )
        )

        return {
            "query": query,
            "language": lang,
            "encoder_backend": encoder_label,
            "reranker": "BhuLokaCrossReranker (Stage-2 Lexical + Dense + Entity)",
            "source_provenance": provenance_list,
            "answer": answer,
            "agent2_map_actions": agent2_actions,
            "retrieved_sources": [
                {
                    "id": r["document"].get("id"),
                    "title": r["document"]["title"],
                    "category": r["document"]["category"],
                    "content": r["document"].get("content", ""),
                    "source_provenance": r["document"].get("source_provenance", r["document"]["category"]),
                    "rrf_score": round(r["rrf_score"], 5),
                    "vector_score": r.get("vector_score", 0.0),
                    "bm25_score": r.get("bm25_score", 0.0),
                    "rerank_score": r.get("rerank_score", round(r["rrf_score"], 5)),
                }
                for r in retrieved
            ],
        }
