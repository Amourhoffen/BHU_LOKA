"""
BHU LOKA Guardrails Engine (Input & Output Safeguards)
Detects prompt injection, out-of-domain gibberish, hallucinations, and ungrounded claims.
Author: Prince Kumar (IIT Patna, PA2511CDH37) | Supervisor: Pallav Rustogi
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class InputGuardrailResult:
    passed: bool
    risk_level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    violation_type: Optional[str]
    details: str
    sanitized_query: str


@dataclass
class OutputGuardrailResult:
    passed: bool
    faithfulness_score: float  # 0.0 - 1.0
    grounded_claims: List[str]
    ungrounded_claims: List[str]
    context_groundedness_pct: float
    agent_self_ratio_pct: float
    decision: str  # "ALLOW", "FLAG_UNGROUNDED", "REFUSE_HALLUCINATION"
    reasoning: str


class BhuLokaGuardrails:
    """
    Production Guardrails protecting the BHU LOKA geospatial decision pipeline.
    """

    # Prompt injection and jailbreak signatures
    INJECTION_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous\s+|prior\s+)?instructions?", re.I),
        re.compile(r"system\s+prompt\s+(reveal|leak|show|dump)", re.I),
        re.compile(r"disregard\s+(all\s+)?guidelines?", re.I),
        re.compile(r"you\s+are\s+now\s+(DAN|unrestricted|jailbroken|prithvi)", re.I),
        re.compile(r"pretend\s+you\s+have\s+no\s+(limits|rules|filters)", re.I),
        re.compile(r"bypass\s+safety", re.I),
    ]

    # Geospatial, earth observation, environmental keywords
    DOMAIN_KEYWORDS = {
        "earth", "globe", "satellite", "starlink", "isro", "dem", "elevation",
        "flood", "water", "river", "ganga", "son", "kosi", "sar", "copernicus",
        "heat", "temperature", "climate", "air", "aqi", "pm2.5", "pm10",
        "soil", "groundwater", "bihar", "patna", "bihta", "india", "state",
        "district", "ward", "ulsi", "land", "safe", "hazard", "seismic",
        "harappa", "rakhigarhi", "ramayana", "asi", "heritage", "map", "legend",
        "red", "blue", "green", "purple", "amber", "color", "line", "prithvi",
        "creator", "prince", "kumar", "iit", "patna", "rustogi", "provenance"
    }

    @classmethod
    def evaluate_input(cls, query: str) -> InputGuardrailResult:
        """
        Inspect incoming query for prompt injections, gibberish, and out-of-domain scope.
        """
        if not query or not query.strip():
            return InputGuardrailResult(
                passed=False,
                risk_level="HIGH",
                violation_type="EMPTY_INPUT",
                details="Query is blank or whitespace only.",
                sanitized_query=""
            )

        q_clean = query.strip()

        # 1. Prompt Injection Detection
        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(q_clean):
                return InputGuardrailResult(
                    passed=False,
                    risk_level="CRITICAL",
                    violation_type="PROMPT_INJECTION_DETECTED",
                    details=f"Query matched adversarial prompt injection pattern: {pattern.pattern}",
                    sanitized_query=q_clean
                )

        # 2. Adversarial Gibberish Detection (Uncalibrated keystrokes e.g. "asdfghjklaaaa")
        words = re.findall(r"[a-zA-Z\u0900-\u097F]+", q_clean)
        if len(words) >= 1 and len(q_clean) > 8:
            # Check character repetition or consonant clusters without vowels
            vowels = set("aeiouAEIOU\u0904-\u0914\u093E-\u094C")
            all_letters = "".join(words)
            vowel_count = sum(1 for c in all_letters if c in vowels)
            vowel_ratio = vowel_count / max(1, len(all_letters))
            if vowel_ratio < 0.08 and len(all_letters) > 10:
                return InputGuardrailResult(
                    passed=False,
                    risk_level="HIGH",
                    violation_type="GIBBERISH_INPUT",
                    details="Uncalibrated random keystroke cluster detected (vowel ratio < 8%).",
                    sanitized_query=q_clean
                )

        # 3. Domain Context Check
        tokens = set(re.findall(r"[a-z0-9]+", q_clean.lower()))
        matched_domain = tokens.intersection(cls.DOMAIN_KEYWORDS)

        # Pass through with clean status
        return InputGuardrailResult(
            passed=True,
            risk_level="LOW",
            violation_type=None,
            details=f"Input passed guardrails; domain keyword matches: {len(matched_domain)}.",
            sanitized_query=q_clean
        )

    @classmethod
    def evaluate_output(
        cls,
        query: str,
        answer: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> OutputGuardrailResult:
        """
        Strict Hallucination & Faithfulness Guardrail:
        Extracts factual propositions from the answer and verifies if they exist in retrieved_docs.
        Checks whether claims come from context or AI agent self-generation.
        """
        if not answer or not answer.strip():
            return OutputGuardrailResult(
                passed=False,
                faithfulness_score=0.0,
                grounded_claims=[],
                ungrounded_claims=["Empty answer"],
                context_groundedness_pct=0.0,
                agent_self_ratio_pct=100.0,
                decision="REFUSE_HALLUCINATION",
                reasoning="Answer is empty."
            )

        # Concatenate all retrieved document text into searchable reference context
        context_corpus = " ".join([
            (doc.get("text") or doc.get("content") or doc.get("title") or "")
            for doc in retrieved_docs
        ]).lower()

        # Split answer into factual sentences / propositions
        raw_sentences = re.split(r"[.\n•!?;]+", answer)
        claims = [s.strip() for s in raw_sentences if len(s.strip()) > 15]

        if not claims:
            claims = [answer.strip()]

        grounded = []
        ungrounded = []

        for claim in claims:
            # Extract key named entities, numbers, and identifiers
            tokens = re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", claim.lower())
            meaningful_tokens = [t for t in tokens if len(t) > 3 and t not in {"this", "that", "with", "from", "have", "more", "also", "into", "hain", "kare", "karna"}]

            if not meaningful_tokens:
                grounded.append(claim)
                continue

            # Check overlap against context
            hits = sum(1 for t in meaningful_tokens if t in context_corpus)
            overlap_ratio = hits / max(1, len(meaningful_tokens))

            # If at least 50% of entity tokens or specific numbers appear in context, consider grounded
            numbers = re.findall(r"\b\d+(?:\.\d+)?\b", claim)
            numbers_grounded = all(n in context_corpus for n in numbers) if numbers else True

            if (overlap_ratio >= 0.45 or (overlap_ratio >= 0.30 and numbers_grounded)):
                grounded.append(claim)
            else:
                ungrounded.append(claim)

        total_claims = len(grounded) + len(ungrounded)
        faithfulness = round(len(grounded) / max(1, total_claims), 3)
        context_groundedness = round(faithfulness * 100.0, 1)
        agent_self_ratio = round(100.0 - context_groundedness, 1)

        # Decision rule: >= 0.70 passes; < 0.70 flags; < 0.40 refuses
        if faithfulness >= 0.70:
            decision = "ALLOW"
            passed = True
            reasoning = f"Answer is grounded in retrieved context (Faithfulness: {faithfulness:.1%})."
        elif faithfulness >= 0.40:
            decision = "FLAG_UNGROUNDED"
            passed = False
            reasoning = f"Partial grounding detected: {len(ungrounded)} claims unsupported by context (Agent self ratio: {agent_self_ratio}%)."
        else:
            decision = "REFUSE_HALLUCINATION"
            passed = False
            reasoning = f"Critical hallucination risk: {agent_self_ratio}% of claims generated from agent memory without context grounding."

        return OutputGuardrailResult(
            passed=passed,
            faithfulness_score=faithfulness,
            grounded_claims=grounded,
            ungrounded_claims=ungrounded,
            context_groundedness_pct=context_groundedness,
            agent_self_ratio_pct=agent_self_ratio,
            decision=decision,
            reasoning=reasoning
        )

