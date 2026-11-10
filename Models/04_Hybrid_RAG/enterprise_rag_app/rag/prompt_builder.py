class PromptBuilder:
    """
    Builds structured, grounded system prompts containing retrieved context.
    Prevents hallucination and enforces scientific attribution.
    """
    @staticmethod
    def build_rag_prompt(query: str, retrieved_docs: list) -> str:
        context_str = "\n\n".join([
            f"--- [SOURCE {i+1}: {d['document']['title']} ({d['document']['category']})] ---\n{d['document']['content']}"
            for i, d in enumerate(retrieved_docs)
        ])
        
        prompt = (
            f"SYSTEM: You are BHU LOKA (भूलोक) - Sovereign Geospatial Decision Engine for Patna, India.\n"
            f"Created by Prince Kumar (IIT Patna, PA2511CDH37) under supervision of Pallav Rustogi.\n"
            f"Use ONLY the verified scientific evidence below to answer the user query.\n\n"
            f"VERIFIED EVIDENCE CONTEXT:\n{context_str}\n\n"
            f"USER QUERY: {query}\n"
            f"RESPONSE INSTRUCTIONS: Deliver an authoritative, precise, evidence-grounded report with numerical figures."
        )
        return prompt

