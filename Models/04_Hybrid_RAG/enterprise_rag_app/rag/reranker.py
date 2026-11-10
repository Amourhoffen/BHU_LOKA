import difflib
import re
from typing import Any, Dict, List, Optional


_HINGLISH_CANONICAL = {
    "bnaya": "banaya",
    "bnao": "banao",
    "bta": "batao",
    "btao": "batao",
    "batado": "batao",
    "krte": "karte",
    "kro": "karo",
    "kre": "kare",
    "cahieye": "chahiye",
    "cahye": "chahiye",
    "jgh": "jagah",
    "jamin": "zameen",
    "kesa": "kaisa",
    "kesha": "kaisa",
    "koun": "kaun",
    "apko": "aapko",
    "aapna": "apna",
    "apna": "apna",
    "apne": "aapne",
    "ramayan": "ramayana",
    "haddapa": "harappa",
    "hadappa": "harappa",
    "sbhyata": "sabhyata",
    "kahata": "kahan tha",
    "kaha": "kahan",
    "setelight": "satellite",
    "statelite": "satellite",
    "setelite": "satellite",
    "kitte": "kitne",
    "q": "kyu why color",
    "wad": "ward",
    "bhot": "bahut",
    "yhi": "yahi",
    "inda": "india",
    "tranformar": "transformer",
    # English & bilingual color / geospatial typo normalizations
    "geen": "green",
    "grean": "green",
    "gren": "green",
    "grn": "green",
    "hara": "green",
    "bluu": "blue",
    "blu": "blue",
    "neela": "blue",
    "nila": "blue",
    "laal": "red",
    "yelow": "amber yellow",
    "yellw": "amber yellow",
    "peela": "amber yellow",
    "pila": "amber yellow",
    "purpel": "purple",
    "prpl": "purple",
    "baingani": "purple",
    "colur": "color",
    "clor": "color",
    "clr": "color",
    "lne": "line",
    "adres": "address",
    "adress": "address",
    "adrs": "address",
    "holgram": "hologram",
    "hlogrm": "hologram",
    "eng": "english",
}

_FUZZY_DOMAIN_VOCAB = (
    "green", "blue", "purple", "amber", "yellow", "orange", "color", "legend",
    "satellite", "starlink", "hologram", "harappa", "ramayana", "ayodhya",
    "rakhigarhi", "dholavira", "lothal", "patna", "bihta", "danapur", "bailey",
    "kankarbagh", "rajendra", "boring", "address", "flood", "farming",
    "agriculture", "heatwave", "district", "india", "bihar", "bengaluru", "hyderabad",
)

_SKIP_FUZZY = {
    "what", "where", "when", "which", "whose", "whom", "this", "that", "with",
    "from", "about", "explain", "show", "real", "view", "map", "line", "lines",
    "good", "best", "safe", "near", "here", "there", "have", "does", "were",
    "Meri", "behen", "liye", "jagah", "batao", "kaha", "kahan", "kaisa", "kaise",
    "kya", "kyu", "kaun", "kisne", "banaya", "aapko", "aap", "hain", "raha",
    "rahe", "chal", "kitne", "fake", "nahi", "abhi", "data",
}


def normalize_query_tokens(query: str) -> List[str]:
    raw_tokens = re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", query.lower())
    out: List[str] = []
    for t in raw_tokens:
        out.append(t)
        mapped = _HINGLISH_CANONICAL.get(t)
        if mapped:
            out.extend(mapped.split())
        elif t.isascii() and t.isalpha() and len(t) >= 4 and t not in _SKIP_FUZZY and t not in _FUZZY_DOMAIN_VOCAB:
            matches = difflib.get_close_matches(t, _FUZZY_DOMAIN_VOCAB, n=1, cutoff=0.80)
            if matches:
                out.append(matches[0])
    return list(dict.fromkeys(out))


class BhuLokaCrossReranker:
    """
    Stage-2 Cross-Signal Re-Ranker over fused BM25 + FAISS RRF candidates.
    Combines:
      - Stage-1 RRF score prior
      - Exact dense cosine similarity (`vector_score`)
      - Lexical token coverage & bigram phrase alignment (Hindi/Hinglish/English canonicalized)
      - Domain entity intent boost (Red/Blue line legend, Satellites, Ramayana, Harappa, Creator, Land Suitability, State/Districts)
    """

    ENTITY_BOOST_RULES = [
        ({"red", "blue", "cyan", "green", "purple", "magenta", "amber", "line", "color", "colour", "legend", "लाल", "नीली", "रंग", "रेखा"}, "doc_map_legend_colors", 0.45),
        ({"ramayan", "ramayana", "ayodhya", "sitamarhi", "mithila", "janakpur", "chitrakoot", "rameswaram", "रामायण", "राम", "अयोध्या"}, "doc_ramayana_circuit", 0.55),
        ({"harappa", "haddapa", "hadappa", "harappan", "indus", "mohenjo", "rakhigarhi", "dholavira", "lothal", "kalibangan", "sabhyata", "sbhyata", "हड़प्पा", "सिंधु", "सभ्यता"}, "doc_harappa_indus_civilization", 0.55),
        ({"starlink", "satellite", "satellites", "setelight", "iss", "orbit", "isro", "cartosat", "सैटेलाइट", "स्टारलिंक", "उपग्रह"}, "doc_live_satellites_constellations", 0.50),
        ({"banaya", "kisne", "creator", "built", "prince", "pallav", "rustogi", "किसने", "बनाया"}, "doc_identity_creator", 0.48),
        # Land suitability: raise boost to 0.52 so it reliably beats capabilities doc on land/ghar/zameen queries
        # Removed 'india' from trigger (too generic); kept high-specificity tokens only
        ({"land", "zameen", "jamin", "ghar", "kharidne", "bengaluru", "pune", "hyderabad", "chandigarh", "plateau", "flat", "residential", "जमीन", "घर"}, "doc_india_best_land_corridors", 0.52),
        ({"state", "states", "29", "28", "36", "bihar", "district", "districts", "38", "ward", "wards", "zila", "jila", "राज्य", "बिहार", "जिला"}, "doc_states_bihar_districts_hierarchy", 0.42),
        ({"fake", "nakli", "honest", "source", "provenance", "fabricated", "uncalibrated", "asli", "नकली", "असली", "स्रोत", "प्रमाण"}, "doc_provenance_honesty_policy", 0.48),
        ({"bihta", "iit"}, "doc_bihta_corridor", 0.46),
        ({"danapur", "sister", "behen", "behan"}, "doc_danapur_cantt", 0.50),
        ({"bailey", "saguna"}, "doc_bailey_road", 0.38),
        ({"kankarbagh"}, "doc_kankarbagh", 0.42),
        ({"rajendra"}, "doc_rajendra_nagar", 0.42),
        ({"boring"}, "doc_boring_road", 0.40),
        ({"enso", "iod", "ocean", "pacific", "teleconnection"}, "doc_macro_teleconnections", 0.42),
        ({"modi", "narendra"}, "doc_governance_leadership", 0.45),
        ({"prithvi"}, "doc_identity_bhu_loka_strict", 0.55),
        ({"farming", "farm", "kheti", "crop", "soil", "agriculture"}, "doc_agro_farming", 0.42),
        ({"modis", "heatwave", "46.25", "temperature", "lst"}, "doc_modis_lst", 0.38),
        # Capabilities doc: only wins when user explicitly asks about system features / what it does
        ({"karte", "krte", "features", "capabilities", "capability", "करते", "काम"}, "doc_capabilities_mission", 0.46),
    ]

    def rerank(self, query: str, candidates: List[Dict[str, Any]], top_k: int = 3) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        q_tokens = normalize_query_tokens(query)
        q_set = set(q_tokens)
        q_bigrams = {f"{q_tokens[i]} {q_tokens[i + 1]}" for i in range(max(0, len(q_tokens) - 1))}

        reranked: List[Dict[str, Any]] = []
        for c in candidates:
            doc = c["document"]
            doc_id = doc.get("id", "")
            doc_text = f"{doc.get('title', '')} {doc.get('keywords', '')} {doc.get('content', '')}".lower()
            doc_tokens = set(re.findall(r"[a-zA-Z0-9\u0900-\u097F]+", doc_text))

            overlap = len(q_set & doc_tokens) / max(1, len(q_set))
            bigram_hits = sum(1 for bg in q_bigrams if bg in doc_text) / max(1, len(q_bigrams))
            rrf_norm = min(1.0, float(c.get("rrf_score", 0.0)) * 32.0)
            vec_score = max(0.0, float(c.get("vector_score", 0.0)))

            entity_boost = 0.0
            for trigger_tokens, target_id, weight in self.ENTITY_BOOST_RULES:
                if doc_id == target_id and (q_set & trigger_tokens):
                    entity_boost += weight
            if doc_id == "doc_provenance_honesty_policy" and any(p in query.lower() for p in ("kaha se", "kahan se", "where does", "कहाँ से")):
                entity_boost += 0.46

            final_score = round(
                0.34 * rrf_norm + 0.28 * vec_score + 0.23 * overlap + 0.15 * bigram_hits + entity_boost,
                5,
            )
            item = dict(c)
            item["rerank_score"] = final_score
            item["lexical_overlap"] = round(overlap, 4)
            reranked.append(item)

        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]


# Location catalog for Agent-2 Autonomous Map & 3D Hologram Builder
KNOWN_LOCATIONS: Dict[str, Dict[str, Any]] = {
    "bihta": {"name": "Bihta / IIT Patna High Levee", "state": "Bihar", "lat": 25.536, "lon": 84.851, "view": "terrain", "zoom": 13, "notes": "Copernicus 30m DEM + S1 SAR verified (ULSI 91.5 Zone S1)"},
    "danapur": {"name": "Danapur Cantonment", "state": "Bihar", "lat": 25.630, "lon": 85.040, "view": "terrain", "zoom": 13, "notes": "Elevated levee 52.8m, 92/100 NCRB/PCR safety (ULSI 89.4)"},
    "bailey": {"name": "Bailey Road / Saguna More", "state": "Bihar", "lat": 25.612, "lon": 85.055, "view": "terrain", "zoom": 13, "notes": "Elevated ridge 52.4m, ULSI 86.2 (Zone S1)"},
    "boring": {"name": "Boring Road / SK Puri", "state": "Bihar", "lat": 25.615, "lon": 85.120, "view": "terrain", "zoom": 13, "notes": "Intermediate 49.5m plateau, ULSI 64.0 (Zone S2)"},
    "kankarbagh": {"name": "Kankarbagh Colony", "state": "Bihar", "lat": 25.588, "lon": 85.148, "view": "terrain", "zoom": 13, "notes": "Depression sink 45.1m, 98.8% S1 SAR flood risk (ULSI 28.2)"},
    "rajendra": {"name": "Rajendra Nagar Bowl", "state": "Bihar", "lat": 25.595, "lon": 85.158, "view": "terrain", "zoom": 13, "notes": "Deepest bowl 44.5m, 99.4% SAR double-bounce (ULSI 21.6)"},
    "bypass": {"name": "Patna Bypass / Transport Nagar", "state": "Bihar", "lat": 25.580, "lon": 85.185, "view": "terrain", "zoom": 13, "notes": "46.8m depression + highway corridor (ULSI 24.5)"},
    "ayodhya": {"name": "Ayodhya (Kosala / Sarayu Basin)", "state": "Uttar Pradesh", "lat": 26.795, "lon": 82.194, "view": "auto_hologram", "zoom": 11, "notes": "Ramayana birthplace axis along Sarayu alluvial terrace"},
    "ramayan": {"name": "Ayodhya — Mithila — Chitrakoot Circuit", "state": "Uttar Pradesh / Bihar", "lat": 26.795, "lon": 82.194, "view": "auto_hologram", "zoom": 7, "notes": "Valmiki Ramayana ASI Heritage Geography"},
    "sitamarhi": {"name": "Sitamarhi & Mithila / Janakpur Axis", "state": "Bihar", "lat": 26.591, "lon": 85.490, "view": "auto_hologram", "zoom": 10, "notes": "Mithila cultural core across North Bihar plain"},
    "buxar": {"name": "Buxar (Siddhashram Ganga Terrace)", "state": "Bihar", "lat": 25.565, "lon": 83.978, "view": "auto_hologram", "zoom": 10, "notes": "Historic confluence along western Ganga levee"},
    "chitrakoot": {"name": "Chitrakoot (Mandakini Vindhyan Hills)", "state": "Uttar Pradesh / MP", "lat": 25.199, "lon": 80.854, "view": "auto_hologram", "zoom": 11, "notes": "Vindhyan upland forest terrain along Ramayana Vanvas path"},
    "rakhigarhi": {"name": "Rakhigarhi Harappan Metropolis", "state": "Haryana", "lat": 29.291, "lon": 76.112, "view": "auto_hologram", "zoom": 11, "notes": "Largest Indus-Sarasvati site in India along Ghaggar-Drishadvati plain"},
    "harappa": {"name": "Rakhigarhi — Dholavira — Lothal IVC Basin", "state": "Haryana / Gujarat", "lat": 29.291, "lon": 76.112, "view": "auto_hologram", "zoom": 6, "notes": "Indus-Sarasvati Civilization ASI Heritage & Ghaggar Paleochannel"},
    "haddapa": {"name": "Rakhigarhi — Dholavira — Lothal IVC Basin", "state": "Haryana / Gujarat", "lat": 29.291, "lon": 76.112, "view": "auto_hologram", "zoom": 6, "notes": "Indus-Sarasvati Civilization ASI Heritage & Ghaggar Paleochannel"},
    "dholavira": {"name": "Dholavira (Rann of Kutch UNESCO IVC)", "state": "Gujarat", "lat": 23.886, "lon": 70.213, "view": "auto_hologram", "zoom": 11, "notes": "Monumental Harappan stone water-harvesting city"},
    "lothal": {"name": "Lothal Ancient Harappan Tidal Dockyard", "state": "Gujarat", "lat": 22.521, "lon": 72.249, "view": "auto_hologram", "zoom": 11, "notes": "Gulf of Khambhat Bronze Age maritime port basin"},
    "bengaluru": {"name": "Bengaluru Deccan Plateau Ridge (~910m)", "state": "Karnataka", "lat": 12.971, "lon": 77.594, "view": "auto_hologram", "zoom": 11, "notes": "Seismic Zone II high-elevation plateau low riverine flood exposure"},
    "pune": {"name": "Pune Western Deccan Foothills (~560m)", "state": "Maharashtra", "lat": 18.520, "lon": 73.856, "view": "auto_hologram", "zoom": 11, "notes": "Basaltic upland slope; choose non-riverbank ridges"},
    "hyderabad": {"name": "Hyderabad Deccan Granite Shield (~542m)", "state": "Telangana", "lat": 17.385, "lon": 78.486, "view": "auto_hologram", "zoom": 11, "notes": "Stable crystalline shield plateau, Seismic Zone II"},
    "chandigarh": {"name": "Chandigarh-Panchkula Shivalik Apron (~330m)", "state": "Chandigarh / Haryana", "lat": 30.733, "lon": 76.779, "view": "auto_hologram", "zoom": 11, "notes": "Planned stormwater sector grid"},
    "gaya": {"name": "Gaya — Rajgir Vindhyan Upland Ridge", "state": "Bihar", "lat": 24.795, "lon": 85.000, "view": "auto_hologram", "zoom": 10, "notes": "Rocky South Bihar highland outside Ganga alluvial floodplains"},
    "rajgir": {"name": "Rajgir Quartzite Hills Ridge", "state": "Bihar", "lat": 25.028, "lon": 85.421, "view": "auto_hologram", "zoom": 11, "notes": "Elevated South Bihar hill basin"},
    "nalanda": {"name": "Nalanda Ancient Terrace & District", "state": "Bihar", "lat": 25.136, "lon": 85.443, "view": "bihar", "zoom": 10, "notes": "South Bihar stable agricultural & heritage plateau"},
    "muzaffarpur": {"name": "Muzaffarpur (Burhi Gandak Basin)", "state": "Bihar", "lat": 26.120, "lon": 85.364, "view": "bihar", "zoom": 10, "notes": "North Bihar Tirhut alluvial corridor"},
    "darbhanga": {"name": "Darbhanga (Kamala-Bagmati Basin)", "state": "Bihar", "lat": 26.154, "lon": 85.891, "view": "bihar", "zoom": 10, "notes": "North Bihar fluvial flood-prone lowland"},
    "bhagalpur": {"name": "Bhagalpur (Lower Ganga Bank)", "state": "Bihar", "lat": 25.242, "lon": 86.984, "view": "bihar", "zoom": 10, "notes": "Southern Ganga levee bank"},
    "varanasi": {"name": "Varanasi Ganga Crescent", "state": "Uttar Pradesh", "lat": 25.317, "lon": 82.974, "view": "auto_hologram", "zoom": 12, "notes": "Kashi ancient riverfront alluvial ridge"},
    "agra": {"name": "Agra Yamuna Bank / Taj Corridor", "state": "Uttar Pradesh", "lat": 27.175, "lon": 78.042, "view": "auto_hologram", "zoom": 12, "notes": "Yamuna right bank heritage & urban terrace"},
    "jaipur": {"name": "Jaipur Aravalli Foothills", "state": "Rajasthan", "lat": 26.912, "lon": 75.787, "view": "auto_hologram", "zoom": 12, "notes": "Aravalli structural highland edge"},
    "lucknow": {"name": "Lucknow Gomti Basin", "state": "Uttar Pradesh", "lat": 26.847, "lon": 80.946, "view": "auto_hologram", "zoom": 12, "notes": "Central Gomti alluvial corridor"},
    "mumbai": {"name": "Mumbai Konkan Coastal Peninsula", "state": "Maharashtra", "lat": 19.076, "lon": 72.877, "view": "auto_hologram", "zoom": 12, "notes": "Arabian Sea coastal storm-surge benchmark"},
    "delhi": {"name": "New Delhi / Connaught Place Ridge", "state": "Delhi", "lat": 28.631, "lon": 77.217, "view": "auto_hologram", "zoom": 12, "notes": "Aravalli Delhi Ridge & Yamuna flood margin"},
    "kolkata": {"name": "Kolkata Hooghly Delta", "state": "West Bengal", "lat": 22.573, "lon": 88.364, "view": "auto_hologram", "zoom": 12, "notes": "Lower Gangetic cyclone-surge corridor"},
    "chennai": {"name": "Chennai Adyar-Cooum Coast", "state": "Tamil Nadu", "lat": 13.083, "lon": 80.270, "view": "auto_hologram", "zoom": 12, "notes": "Coromandel urban coastal flood plain"},
    "guwahati": {"name": "Guwahati Brahmaputra Gorge", "state": "Assam", "lat": 26.144, "lon": 91.736, "view": "auto_hologram", "zoom": 12, "notes": "Brahmaputra granitic hill & floodplain belt"},
    "leh": {"name": "Leh Indus Cryosphere Valley", "state": "Ladakh", "lat": 34.153, "lon": 77.577, "view": "auto_hologram", "zoom": 11, "notes": "High-altitude (~3500m) Trans-Himalayan crown"},
    "srinagar": {"name": "Srinagar Jhelum Basin", "state": "Jammu and Kashmir", "lat": 34.084, "lon": 74.797, "view": "auto_hologram", "zoom": 11, "notes": "Kashmir Valley intermontane alluvial basin"},
    "rishikesh": {"name": "Rishikesh Siwalik Ganga Gorge", "state": "Uttarakhand", "lat": 30.087, "lon": 78.268, "view": "auto_hologram", "zoom": 12, "notes": "Upper Ganga foothills discharge monitor"},
    "bodh gaya": {"name": "Bodh Gaya Niranjana Terrace", "state": "Bihar", "lat": 24.696, "lon": 84.991, "view": "auto_hologram", "zoom": 12, "notes": "South Bihar stable heritage upland"},
}


_CUSTOM_PLACE_RE = re.compile(
    r"(?:real\s+view|satellite\s+view|hologram|3d\s+(?:view|map|dem)|address|show|zoom)\s+(?:of|for|at|on)?\s*([a-zA-Z0-9,\-\s]{3,42})$",
    re.IGNORECASE,
)


def _extract_custom_address(query: str) -> Optional[str]:
    m = _CUSTOM_PLACE_RE.search(query.strip())
    if not m:
        return None
    cand = re.sub(r"\b(in\s+english|in\s+eng|map|please|now)\b", "", m.group(1), flags=re.IGNORECASE).strip(" ,.-?!")
    if len(cand) >= 3 and cand.lower() not in {"india", "world", "earth", "patna", "the map", "it"}:
        return cand
    return None


def plan_agent2_map_actions(query: str, reranked_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agent-2: Autonomous Cartographic Director / Map Action Planner.
    Translates Agent-1 retrieval intent + entities into deterministic 3D/2D map instructions.
    """
    q_norm = " ".join(normalize_query_tokens(query))
    q_low = query.lower()
    top_id = reranked_docs[0]["document"]["id"] if reranked_docs else ""

    actions: Dict[str, Any] = {
        "agent": "AGENT-2 (Cartographic Map Director)",
        "view_mode": "india",
        "callout_color_key": None,
        "highlight_layers": ["outer", "states", "hubs", "grid"],
        "fly_to": None,
        "auto_hologram_target": None,
        "summary": "Maintain Sovereign India 36-State 3D overview.",
    }

    # 1. Line / Color Explanation mode
    if top_id == "doc_map_legend_colors" or any(k in q_norm for k in ("red", "blue", "cyan", "green", "purple", "amber", "color", "colour", "line", "लाल", "नीली", "रेखा")):
        if "red" in q_norm or "rose" in q_norm or "लाल" in q_low:
            actions["callout_color_key"] = "red"
            actions["summary"] = "Spotlight RED layers: Bihar core border, 94.08 km2 S1 SAR urban double-bounce flood & Critical Zone S4 hubs."
        elif "blue" in q_norm or "cyan" in q_norm or "नील" in q_low:
            actions["callout_color_key"] = "blue"
            actions["summary"] = "Spotlight CYAN/BLUE layers: Sovereign 6.75N-37.10N border, Bay of Bengal LPS monsoon arc & Open Water specular drop."
        elif "green" in q_norm or "हर" in q_low:
            actions["callout_color_key"] = "green"
            actions["summary"] = "Spotlight GREEN layers: Ladakh & J&K Sovereign Crown, Safe Zone S1 ridges (>52m) & IOD Assam moisture arc."
        elif "purple" in q_norm or "magenta" in q_norm or "बैंगनी" in q_low:
            actions["callout_color_key"] = "purple"
            actions["summary"] = "Spotlight PURPLE layers: Trans-Himalayan Cryosphere melt feeder & Copernicus <47m depression sinks."
        elif "amber" in q_norm or "yellow" in q_norm or "orange" in q_norm or "पील" in q_low:
            actions["callout_color_key"] = "amber"
            actions["summary"] = "Spotlight AMBER layers: NASA MODIS 46.25C heatwave spots, Zone S2 ponding & Arabian Sea Surge arc."
        else:
            actions["callout_color_key"] = "all"
            actions["summary"] = "Spotlight full color legend across 3D India/Patna map layers."
        actions["highlight_layers"] = ["outer", "states", "arcs", "hubs", "grid"]
        return actions

    # 2. World Earth + Live Satellites mode
    if top_id == "doc_live_satellites_constellations" or any(k in q_norm for k in ("starlink", "satellite", "setelight", "world", "earth", "globe", "iss", "orbit", "सैटेलाइट", "स्टारलिंक")):
        actions["view_mode"] = "world"
        actions["highlight_layers"] = ["outer", "states", "satellites", "starlink", "eo", "iss"]
        actions["summary"] = "Switch to 3D World Earth & sync live NORAD/CelesTrak satellites (Starlink, ISS, Sentinel/MODIS, ISRO)."
        return actions

    # 3. Historical Heritage Circuits (Ramayana & Harappa)
    if top_id == "doc_ramayana_circuit" or any(k in q_norm for k in ("ramayan", "ramayana", "ayodhya", "sitamarhi", "mithila", "janakpur", "chitrakoot", "रामायण", "अयोध्या")):
        loc = KNOWN_LOCATIONS["ayodhya"]
        if "sitamarhi" in q_norm or "mithila" in q_norm or "janakpur" in q_norm:
            loc = KNOWN_LOCATIONS["sitamarhi"]
        elif "chitrakoot" in q_norm:
            loc = KNOWN_LOCATIONS["chitrakoot"]
        elif "buxar" in q_norm:
            loc = KNOWN_LOCATIONS["buxar"]
        actions["view_mode"] = "auto_hologram"
        actions["highlight_layers"] = ["outer", "states", "heritage_ramayana", "grid"]
        actions["fly_to"] = loc
        actions["auto_hologram_target"] = {"name": loc["name"], "state": loc["state"], "lat": loc["lat"], "lon": loc["lon"], "category": "heritage_ramayana"}
        actions["summary"] = f"Plot Ramayana Heritage Circuit in 3D & generate Copernicus 90m terrain hologram for {loc['name']}."
        return actions

    if top_id == "doc_harappa_indus_civilization" or any(k in q_norm for k in ("harappa", "haddapa", "hadappa", "harappan", "rakhigarhi", "dholavira", "lothal", "kalibangan", "indus", "mohenjo", "हड़प्पा", "सिंधु", "राखीगढ़ी", "धोलावीरा")):
        loc = KNOWN_LOCATIONS["rakhigarhi"]
        if "dholavira" in q_norm:
            loc = KNOWN_LOCATIONS["dholavira"]
        elif "lothal" in q_norm:
            loc = KNOWN_LOCATIONS["lothal"]
        actions["view_mode"] = "auto_hologram"
        actions["highlight_layers"] = ["outer", "states", "heritage_harappa", "grid"]
        actions["fly_to"] = loc
        actions["auto_hologram_target"] = {"name": loc["name"], "state": loc["state"], "lat": loc["lat"], "lon": loc["lon"], "category": "heritage_harappa"}
        actions["summary"] = f"Plot Harappan / IVC Sites & build live Copernicus 90m DEM 3D hologram for {loc['name']}."
        return actions

    # 4. Specific Named City / Bihar District / Patna Ward
    for key, loc in KNOWN_LOCATIONS.items():
        if key in q_norm:
            actions["view_mode"] = loc["view"]
            actions["fly_to"] = loc
            if loc["view"] == "terrain":
                actions["highlight_layers"] = ["states", "hubs", "grid", "dem"]
                actions["summary"] = f"Fly 3D DEM camera to Patna Ward: {loc['name']}."
            elif loc["view"] == "bihar":
                actions["highlight_layers"] = ["states", "bihar_districts", "hubs", "grid"]
                actions["auto_hologram_target"] = {"name": loc["name"], "state": loc["state"], "lat": loc["lat"], "lon": loc["lon"], "category": "district"}
                actions["summary"] = f"Switch to Bihar 38 Districts 3D & highlight {loc['name']}."
            else:
                actions["highlight_layers"] = ["outer", "states", "land_corridors", "grid"]
                actions["auto_hologram_target"] = {"name": loc["name"], "state": loc["state"], "lat": loc["lat"], "lon": loc["lon"], "category": "land_suitability"}
                actions["summary"] = f"Build live Copernicus 90m DEM 3D hologram for {loc['name']}."
            return actions

    # 5. Pan-India Best Land -> Highlight Land Corridors + Build Live Bihta / Bengaluru 3D Hologram
    if top_id == "doc_india_best_land_corridors" or ("land" in q_norm or "zameen" in q_norm or "jagah" in q_norm or "flat" in q_norm or "जमीन" in q_low):
        if "patna" in q_norm or "behen" in q_norm or "sister" in q_norm:
            actions["view_mode"] = "terrain"
            actions["fly_to"] = KNOWN_LOCATIONS["bihta"]
            actions["highlight_layers"] = ["states", "hubs", "grid", "dem"]
            actions["summary"] = "Focus Patna 3D DEM on Bihta/Danapur Safe Zone S1 Ridge (ULSI 89.4–91.5)."
        else:
            loc = KNOWN_LOCATIONS["bengaluru"]
            actions["view_mode"] = "auto_hologram"
            actions["fly_to"] = loc
            actions["auto_hologram_target"] = {"name": "Bengaluru Deccan Ridge (Sample National S1 Corridor)", "state": "Karnataka", "lat": loc["lat"], "lon": loc["lon"], "category": "land_suitability"}
            actions["highlight_layers"] = ["outer", "states", "land_corridors", "hubs", "grid"]
            actions["summary"] = "Highlight Pan-India High-Resilience Land Corridors & generate live 90m DEM 3D hologram."
        return actions

    # 6. Bihar Districts Hierarchy
    if top_id == "doc_states_bihar_districts_hierarchy" or ("bihar" in q_norm and ("district" in q_norm or "zila" in q_norm or "jila" in q_norm or "जिला" in q_low)):
        actions["view_mode"] = "bihar"
        actions["highlight_layers"] = ["states", "bihar_districts", "hubs", "grid"]
        actions["summary"] = "Switch to 3D Bihar 38-District Extruded Map View."
        return actions

    # 7. Default Patna DEM topics
    if top_id in {"doc_sar_physics", "doc_copernicus_dem", "doc_modis_lst", "doc_agro_farming", "doc_danapur_cantt", "doc_bailey_road", "doc_boring_road", "doc_kankarbagh", "doc_rajendra_nagar", "doc_bihta_corridor"}:
        actions["view_mode"] = "terrain"
        actions["highlight_layers"] = ["states", "hubs", "grid", "dem"]
        actions["summary"] = "Inspect Patna Copernicus 30m DEM + Sentinel-1 SAR 3D Surface."
        return actions

    # 8. Arbitrary user-typed address / real-view trigger
    custom_place = _extract_custom_address(query)
    if custom_place:
        actions["view_mode"] = "auto_hologram"
        actions["auto_hologram_target"] = {"name": custom_place, "state": "India", "lat": None, "lon": None, "category": "custom_address"}
        actions["highlight_layers"] = ["outer", "states", "grid"]
        actions["summary"] = f"Resolve address & drape real satellite imagery over 90m DEM 3D for {custom_place}."
        return actions

    return actions
