import re


_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")

# Unambiguous Romanized Hindi / Hinglish lexical cues
_HINGLISH_MARKERS = {
    "kya", "kaha", "kahan", "kaise", "kesa", "kesha", "kaisa", "kaisi", "koun", "kaun",
    "kisne", "bnaya", "banaya", "btao", "batao", "btado", "batado", "chahiye", "cahieye",
    "cahye", "jagah", "jgh", "zameen", "jamin", "accha", "acha", "acche", "krte", "karte",
    "kro", "karo", "kre", "kare", "apko", "aapko", "apka", "aapka", "apna", "aapna",
    "apne", "aapne", "mera", "mere", "meri", "behen", "bhai", "huaa", "hua", "tha",
    "the", "hai", "hain", "ho", "rha", "raha", "rhe", "rahe", "kitte", "kitne",
    "chal", "bhot", "bahut", "yhi", "yahi", "uska", "usko", "jisse", "esha", "aisa",
    "skte", "sakte", "nhi", "nahi", "ye", "wo", "woh", "sb", "sab", "koi", "kuch",
    "q", "kyu", "kyon", "kyunki", "sbhyata", "sabhyata", "kahata", "setelight",
    "dikhe", "dikhao", "bataye", "bataiye", "bare", "baare", "me", "ke", "ka", "ki",
    "ko", "se", "aur", "toh", "to", "abhi", "puch", "puche", "pehle",
}

# Pure Hinglish high-confidence single-word hits even in short queries
_STRONG_HINGLISH = {
    "kya", "kaha", "kahan", "kaise", "kesa", "kesha", "kaisa", "koun", "kaun",
    "kisne", "bnaya", "banaya", "btao", "batao", "chahiye", "cahieye", "jagah", "jgh",
    "krte", "karte", "apko", "aapko", "aapna", "aapne", "behen", "huaa", "hain",
    "kitte", "kitne", "nhi", "nahi", "yhi", "bhot", "sbhyata", "sabhyata", "kahata",
    "setelight", "dikhe", "zameen", "jamin", "ramayan", "haddapa", "behtar",
}


_EXPLICIT_EN_RE = re.compile(r"\b(in\s+english|in\s+eng|english\s+me|eng\s+me|reply\s+in\s+english|answer\s+in\s+english)\b")


def detect_query_language(query: str) -> str:
    """
    Detect query language cleanly without guessing wildly:
      - 'hi'       : Contains Devanagari script characters
      - 'en'       : Explicit English instruction or standard English (English first)
      - 'hinglish' : Romanized Hindi phrasing detected
    """
    if not query or not query.strip():
        return "en"

    q_low = query.lower()
    if _EXPLICIT_EN_RE.search(q_low):
        return "en"

    if _DEVANAGARI_RE.search(query):
        return "hi"

    tokens = re.findall(r"[a-z0-9]+", q_low)
    if not tokens:
        return "en"

    if any(t in _STRONG_HINGLISH for t in tokens):
        return "hinglish"

    hinglish_hits = sum(1 for t in tokens if t in _HINGLISH_MARKERS)
    if hinglish_hits >= 2 or (len(tokens) <= 4 and hinglish_hits >= 1 and tokens[0] not in {"what", "where", "who", "how", "is", "show", "explain"}):
        return "hinglish"

    return "en"

