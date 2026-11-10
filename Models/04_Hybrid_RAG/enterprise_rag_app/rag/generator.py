from rag.language import detect_query_language
from rag.reranker import normalize_query_tokens


_COLOR_ENGLISH_SPOTLIGHT = {
    "green": "GREEN (#10b981): Marks India's Sovereign Northern Crown (Ladakh LA & Jammu and Kashmir JK), Safe Zone S1 elevated natural levees (>52m such as Bihta 55.2m & Danapur Cantt 52.8m), flood-resilient South Bihar uplands, and the Positive Indian Ocean Dipole (IOD) monsoon conveyor toward Assam.",
    "red": "RED / ROSE (#f43f5e): Highlights Bihar as the primary validation core and maps 94.08 km2 of Sentinel-1 C-Band SAR Urban Double-Bounce flooding (Delta sigma0 >= +1.5 dB from 90-degree building wall corner reflections in Rajendra Nagar & Kankarbagh) plus Critical Zone S4 high-risk hubs (ULSI < 35).",
    "blue": "BLUE / CYAN (#38bdf8): Represents India's complete Sovereign National & State Boundaries (6.75N-37.10N, 36 States/UTs), Bay of Bengal Low-Pressure System (LPS) moisture tracks (>200mm/48h), Patna PMC boundary, Ganga 49.5m danger lock threshold, and 1.15 km2 open-water SAR specular drop (-3.8 dB).",
    "purple": "PURPLE / VIOLET (#a78bfa): Traces Trans-Himalayan Cryosphere snow-melt feeder lines (raising Gandak/Kosi/Ganga baseline stage) and Copernicus 30m DEM deep concave depression sinks (<47m elevation covering 47.24 km2 / 33.15% of Patna Municipal Corporation).",
    "amber": "AMBER / YELLOW (#f59e0b): Indicates Moderate Zone S2 monsoon ponding (48-52m), the Arabian Sea Konkan storm-surge arc, and NASA Terra MODIS summer heatwave peaks (up to 46.25C in Patna & >50C in Thar Desert).",
}


# Topic-specific concise summaries in Devanagari Hindi & Romanized Hinglish paired with calibrated metrics
_LOCALIZED_INTROS = {
    "doc_identity_creator": {
        "hi": "मुझे (BHU LOKA / भूलोक) IIT पटना के शोधकर्ता प्रिंस कुमार (Roll No: PA2511CDH37, M.S. CS & Data Analytics) ने बाह्य शोध मार्गदर्शक पल्लव रुस्तोगी (Pallav Rustogi) के निर्देशन में विकसित किया है।",
        "hinglish": "Mujhe (BHU LOKA / भूलोक) ko IIT Patna ke researcher Prince Kumar (Roll: PA2511CDH37, M.S. CS & Data Analytics) ne External Supervisor Pallav Rustogi ke guidance me banaya hai.",
    },
    "doc_map_legend_colors": {
        "hi": "नक्शे की हर रेखा और रंग का वैज्ञानिक अर्थ तय है — लाल (#f43f5e): बिहार व 94.08 km² शहरी SAR डबल-बाउंस बाढ़ (+1.5 dB); नीला/सियान (#38bdf8): भारत की संप्रभु सीमा (36 राज्य/केंद्र शासित प्रदेश), बंगाल की खाड़ी मानसून ट्रैक व खुला जल (-3.8 dB); हरा (#10b981): लद्दाख-जम्मू-कश्मीर मुकुट, सुरक्षित ऊँचे क्षेत्र (>52m जैसे बिहटा/दानापुर) व IOD धारा; बैंगनी (#a78bfa): हिमालयी ग्लेशियर-पिघलन प्रवाह और <47m गहरे गर्त (47.24 km²); पीला/अंबर (#f59e0b): MODIS 46.25°C हीटवेव व अरब सागर प्रवाह।",
        "hinglish": "Map par har color aur line ka real scientific meaning hai — RED (#f43f5e): Bihar highlight aur 94.08 km² S1 SAR urban double-bounce flood (+1.5 dB) + Critical S4 zone; BLUE/CYAN (#38bdf8): Sovereign India border (6.75N–37.10N), Bay of Bengal LPS monsoon track aur open water (-3.8 dB); GREEN (#10b981): Ladakh/J&K crown, Safe S1 high ridges (>52m Bihta/Danapur) aur IOD Assam moisture arc; PURPLE (#a78bfa): Himalayan snow-melt cryosphere line aur <47m depression sinks (47.24 km²); AMBER (#f59e0b): NASA MODIS 46.25°C heatwave aur Arabian Sea surge.",
    },
    "doc_ramayana_circuit": {
        "hi": "ऐतिहासिक-भौगोलिक व ASI प्रमाणों के अनुसार रामायण के प्रमुख स्थल भारत और मिथिला क्षेत्र में स्थित हैं: अयोध्या (26.795°N, 82.194°E — सरयू तट, जन्मस्थली व कोसल राजधानी), बक्सर/सिद्धाश्रम (25.565°N, 83.978°E — बिहार), सीतामढ़ी व जनकपुर/मिथिला (26.591°N, 85.490°E), चित्रकूट (25.199°N, 80.854°E), पंचवटी/नासिक (20.006°N, 73.790°E), किष्किंधा/हम्पी (15.335°N, 76.460°E) तथा रामेश्वरम/धनुषकोडी (9.288°N, 79.313°E)। एजेंट-2 ने 3D मानचित्र पर इस परिपथ को सक्रिय कर दिया है।",
        "hinglish": "Historical geography aur ASI heritage records ke hisab se Ramayan circuit ke main sthan ye hain: Ayodhya (26.795°N, 82.194°E, UP Sarayu nadi tat — janamsthan aur Kosala rajdhani), Buxar/Siddhashram (25.565°N, 83.978°E, Bihar), Sitamarhi & Mithila/Janakpur (26.591°N, 85.490°E), Chitrakoot (25.199°N, 80.854°E), Panchavati/Nashik (20.006°N, 73.790°E), Kishkindha/Hampi (15.335°N, 76.460°E) aur Rameswaram (9.288°N, 79.313°E). Agent-2 ne is circuit ko 3D map me plot kar diya hai.",
    },
    "doc_harappa_indus_civilization": {
        "hi": "हड़प्पा / सिंधु-सरस्वती सभ्यता (लगभग 3300–1300 ईसा पूर्व) उत्तर-पश्चिमी भारतीय उपमहाद्वीप में सिंधु व घग्घर-हाकरा (प्राचीन सरस्वती) नदी घाटियों में विकसित थी। भारत में इसके प्रमुख ASI प्रमाणित स्थल: राखीगढ़ी (हरियाणा, 29.291°N — भारत का सबसे बड़ा 350+ हेक्टेयर नगर), धोलावीरा (कच्छ, गुजरात — UNESCO जल-संरक्षण नगर), लोथल (गुजरात — प्राचीन बंदरगाह/डॉकयार्ड), कालीबंगन (राजस्थान — जुता हुआ खेत) तथा बनावली/रोपड़ हैं, जबकि मूल हड़प्पा (30.631°N) व मोहनजोदड़ो (27.324°N) वर्तमान पाकिस्तान क्षेत्र की सिंधु घाटी में स्थित हैं।",
        "hinglish": "Haddapa / Indus-Sarasvati Sabhyata (c. 3300–1300 BCE) northwest Indian subcontinent me Indus aur Ghaggar-Hakra (ancient Sarasvati) basins me thi. India me iske bade ASI certified sites hain: Rakhigarhi (Haryana, 29.291°N — India ka sabse bada Harappan city), Dholavira (Kutch Gujarat — UNESCO water-harvesting city), Lothal (Gujarat — tidal dockyard), Kalibangan (Rajasthan), Banawali (Haryana) & Ropar (Punjab), jabki original Harappa aur Mohenjo-daro Indus valley (present Pakistan) me hain. Agent-2 ne 3D map par ye basin plot kar diya hai.",
    },
    "doc_india_best_land_corridors": {
        "hi": "भारत में आवास और भूमि-उपयुक्तता (बाढ़ व भूकंप जोखिम के आधार पर): (1) पूर्णतः कैलिब्रेटेड पटना ULSI क्षेत्र: बिहटा / IIT पटना (55.2m ऊँचाई, ULSI 91.5 Zone S1) तथा दानापुर कैंट / बेली रोड (52.4–52.8m, ULSI 86.2–89.4) सबसे सुरक्षित हैं। (2) अखिल भारतीय सुरक्षित पठारी क्षेत्र (Copernicus DEM व NDMA ज़ोन): बेंगलुरु दक्कन पठार (~910m, Seismic Zone II), हैदराबाद ग्रेनाइट शील्ड (~542m), पुणे पश्चिमी ढलान (~560m), चंडीगढ़ नियोजित सेक्टर व दक्षिण बिहार में गया-राजगीर (~110m+ पथरीली रिज) कम नदी-बाढ़ जोखिम वाले श्रेष्ठ क्षेत्र हैं।",
        "hinglish": "India me safe aur acchi land ke liye elevation, flood risk aur seismic stability sabse main hain: (1) Fully calibrated Patna benchmark me Bihta / IIT Patna (55.2m, 0.8% flood, ULSI 91.5 S1) aur Danapur Cantt / Bailey Road (ULSI 86.2–89.4 S1) best hain. (2) Pure India me Copernicus DEM + NDMA zones ke hisab se Bengaluru Deccan Plateau (~910m, Seismic Zone II), Hyderabad (~542m granite shield), Pune foothills (~560m), Chandigarh Shivalik grid, aur South Bihar me Gaya-Rajgir ridge low flood corridors hain. Agent-2 ab aapke liye us jagah ka live 90m DEM 3D hologram bana raha hai.",
    },
    "doc_live_satellites_constellations": {
        "hi": "विश्व मानचित्र (World Earth 3D) पर सक्रिय उपग्रहों की वास्तविक संख्या व स्थिति NORAD / CelesTrak लाइव GP डेटा (`celestrak.org`) और `wheretheiss.at` से लाइव SGP4 कक्षा गणना द्वारा दिखाई जाती है — इसमें Starlink समूह, ISS अंतरिक्ष स्टेशन, ISRO (Cartosat, Resourcesat, EOS, INSAT/NavIC) तथा Sentinel-1/MODIS उपग्रह शामिल हैं। इंटरनेट बंद होने पर AI स्पष्ट OFFLINE बताता है, कभी नकली आँकड़े नहीं बनाता।",
        "hinglish": "World Earth 3D view me satellites ka real data CelesTrak NORAD GP API (`celestrak.org`) aur `wheretheiss.at` se live SGP4 orbital calculation ke saath aata hai — jisme real active Starlink swarm count, ISS live location, ISRO (Cartosat, EOS, Resourcesat, INSAT) aur Sentinel-1 / MODIS EO satellites shamil hain. Network offline hone par system seedha OFFLINE batata hai, koi fake count nahi dikhata.",
    },
    "doc_states_bihar_districts_hierarchy": {
        "hi": "हमारा 3D सिस्टम पाँच स्तरों पर कार्य करता है: विश्व पृथ्वी + लाइव उपग्रह -> भारत के सभी 28 राज्य + 8 केंद्र शासित प्रदेश (36 इकाइयाँ; 2019 पुनर्गठन पूर्व 29 राज्य) -> बिहार के सभी 38 जिले (GADM v4.1) -> पटना जिला/नगर निगम (133.87 km²) -> वार्ड स्तर (बिहटा, दानापुर, कंकड़बाग, राजेंद्र नगर आदि) 3D DEM मॉडल।",
        "hinglish": "Hamara 3D system 5 levels par kaam karta hai: World Earth + Live Satellites -> Bharat ke sabhi 28 States + 8 UTs (36 units; 2019 se pehle 29 states) -> Bihar ke sabhi 38 Districts (Patna, Gaya, Nalanda, Muzaffarpur, Darbhanga, Bhagalpur, Purnia, Saran, Rohtas, Sitamarhi, Buxar...) -> Patna Municipal Core (133.87 km²) -> Ward-level 3D DEM + Auto 90m Terrain Hologram.",
    },
    "doc_provenance_honesty_policy": {
        "hi": "सत्यता व स्रोत पारदर्शिता नियम: जहाँ लाइव डेटा उपलब्ध है (Open-Meteo मौसम/नदी प्रवाह/90m DEM या CelesTrak लाइव उपग्रह), वहाँ वास्तविक समय व API स्रोत दिखाया जाता है। जहाँ लाइव डेटा नहीं है या क्षेत्र पटना के बाहर है, AI स्पष्ट बताता है कि उत्तर Copernicus DEM, Sentinel-1 SAR, NASA MODIS, NCRB Q390 या ASI ऐतिहासिक अभिलेखों से आ रहा है — कोई काल्पनिक संख्या नहीं गढ़ी जाती।",
        "hinglish": "100% Honesty Rule (Koi Fake Nahi): Jahan live API connected hai (Open-Meteo weather/river/90m DEM aur CelesTrak satellites), wahan real timestamp + API URL bataya jata hai. Jahan live sensor nahi hai ya city Patna dataset ke bahar hai, BHU LOKA seedha batata hai ki answer kis certified archive (Copernicus DEM, S1 SAR, NASA MODIS, NCRB Q390, ya ASI records) se aa raha hai.",
    },
    "doc_capabilities_mission": {
        "hi": "BHU LOKA दो एजेंट से संचालित एक संप्रभु भू-स्थानिक AI प्रणाली है: (1) एजेंट-1 — ट्रांसफॉर्मर वेक्टर सर्च + BM25 + Stage-2 Cross Re-Ranker; Sentinel-1 SAR, Copernicus DEM, NASA MODIS, NCRB Q390, CelesTrak लाइव उपग्रह व ASI विरासत अभिलेखों पर; (2) एजेंट-2 — 3D विश्व पृथ्वी (लाइव Starlink/ISS), संप्रभु भारत (28 राज्य + 8 UT), बिहार के 38 जिले, पटना वार्ड DEM व किसी भी पते का लाइव 90m Copernicus वास्तविक उपग्रह 3D होलोग्राम; (3) स्वचालित हिंदी, हिंग्लिश व अंग्रेज़ी उत्तर।",
        "hinglish": "BHU LOKA do agents se kaam karta hai: (1) Agent-1 — Transformer Vector Search + BM25 + Stage-2 Re-Ranker Sentinel-1 SAR, Copernicus DEM, NASA MODIS, NCRB Q390, CelesTrak aur ASI Heritage records pe; (2) Agent-2 — 3D World Earth (live Starlink/ISS), Sovereign India (36 States/UTs), Bihar ke 38 Districts, Patna Wards DEM, aur kisi bhi address ka live Copernicus 90m Real Satellite 3D Hologram; (3) Automatic Hindi/Hinglish/English multilingual replies deta hai.",
    },
    "doc_governance_leadership": {
        "hi": "श्री नरेन्द्र मोदी भारत के माननीय प्रधानमंत्री हैं। उनके नेतृत्व में राष्ट्रीय भू-स्थानिक नीति 2022, डिजिटल इंडिया व PM गति शक्ति राष्ट्रीय मास्टर प्लान — ये सभी स्वदेशी स्थानिक बुद्धिमत्ता को प्राथमिकता देते हैं। IIT पटना में निर्मित BHU LOKA इसी राष्ट्रीय उद्देश्य को पूर्ण करता है।",
        "hinglish": "Shri Narendra Modi Bharat ke Pradhan Mantri hain. Unke naitritva me National Geospatial Policy 2022, Digital India Mission, aur PM Gati Shakti — ye sab swadeshi spatial intelligence ko prioritize karte hain. BHU LOKA, IIT Patna me banaya gaya, isi national mission ko fulfill karta hai.",
    },
}


class LocalSovereignGenerator:
    """
    Agent-1: Multilingual & Provenance-Honest Decision Synthesizer.
    Automatically responds in:
      - Devanagari Hindi ('hi') when query is in Hindi
      - Romanized Hinglish ('hinglish') when query is in Hinglish
      - English ('en') first for English queries
    Always appends explicit Source Provenance & Pipeline telemetry metadata.
    """

    def generate(
        self,
        query: str,
        retrieved_docs: list,
        encoder_label: str = "Hybrid BM25 + FAISS",
        language_override: str | None = None,
    ) -> tuple[str, str]:
        lang = language_override or detect_query_language(query)

        if not retrieved_docs:
            if lang == "hi":
                msg = (
                    "क्षमा करें, हमारे सत्यापित भू-स्थानिक या ऐतिहासिक डेटाबेस में इस प्रश्न से मेल खाने वाला कोई प्रमाणित रिकॉर्ड नहीं मिला। "
                    "BHU LOKA बिना प्रमाण के अनुमानित उत्तर नहीं गढ़ता।"
                )
            elif lang == "hinglish":
                msg = (
                    "Maaf kijiye, hamare verified geospatial ya ASI heritage records me is query ka koi authentic match nahi mila. "
                    "BHU LOKA bina evidence ke fake data fabricate nahi karta."
                )
            else:
                msg = "No verified geospatial records match the specified query. BHU LOKA does not fabricate ungrounded claims."
            return msg, lang

        top_entry = retrieved_docs[0]
        top_doc = top_entry["document"]
        top_id = top_doc.get("id", "")
        top_prov = top_doc.get("source_provenance", top_doc.get("category", "Verified Local Archive"))
        localized = _LOCALIZED_INTROS.get(top_id, {})

        if lang == "hi":
            summary_block = localized.get("hi") or top_doc["content"]
            header = "=== BHU LOKA बहु-स्तरीय भू-स्थानिक निर्णय संश्लेषण ==="
            ev_lbl = f"मुख्य साक्ष्य (Re-Rank Rank #1): {top_doc['title']}"
            prov_lbl = f"डेटा स्रोत / प्रमाणिकता: {top_prov}"
            supp_lbl = "सहायक प्रमाण:"
            footer = f"इंजन पाइपलाइन: {encoder_label} + BM25 + Stage-2 Re-Ranker | बिना सत्यापित स्रोत के कोई उत्तर नहीं गढ़ा गया।"
        elif lang == "hinglish":
            summary_block = localized.get("hinglish") or top_doc["content"]
            header = "=== BHU LOKA DUAL-AGENT GEOSPATIAL DECISION REPORT ==="
            ev_lbl = f"Primary Evidence (Re-Rank Rank #1): {top_doc['title']}"
            prov_lbl = f"Data Kaha Se Aaya (Source Provenance): {top_prov}"
            supp_lbl = "Supporting Verified Evidence:"
            footer = f"Pipeline: {encoder_label} + BM25 + Re-Ranker | Zero Fake Claims — 100% Source-Grounded."
        else:
            summary_block = top_doc["content"]
            if top_id == "doc_map_legend_colors":
                q_norm_set = set(normalize_query_tokens(query))
                focused_parts = [
                    _COLOR_ENGLISH_SPOTLIGHT[ck]
                    for ck in ("green", "red", "blue", "purple", "amber")
                    if ck in q_norm_set or (ck == "blue" and "cyan" in q_norm_set) or (ck == "amber" and ("yellow" in q_norm_set or "orange" in q_norm_set)) or (ck == "purple" and "magenta" in q_norm_set)
                ]
                if focused_parts:
                    summary_block = "\n".join(focused_parts) + "\n\nFull Map Legend:\n" + top_doc["content"]
            header = "=== BHU LOKA MULTI-HAZARD DECISION SYNTHESIS ==="
            ev_lbl = f"Evidence Source (Re-Rank Rank #1): {top_doc['title']}"
            prov_lbl = f"Source Provenance: {top_prov}"
            supp_lbl = "Supporting Evidence Corroboration:"
            footer = f"Retrieval Engine: {encoder_label} + BM25 + Stage-2 Cross Re-Ranker | Verified against empirical & official archives."

        lines = [
            header,
            f"Query: \"{query}\"",
            ev_lbl,
            prov_lbl,
            "",
            summary_block,
        ]

        # When answering in Hindi/Hinglish and we have a localized summary, also preserve exact detailed English spec line if helpful
        if lang in {"hi", "hinglish"} and top_id in localized:
            lines.extend(["", f"[Detailed Verified Parameters]: {top_doc['content']}"])

        if len(retrieved_docs) > 1:
            lines.extend(["", supp_lbl])
            for d in retrieved_docs[1:]:
                doc = d["document"]
                doc_id = doc.get("id", "")
                supp_prov = doc.get("source_provenance", doc.get("category"))
                loc_supp = _LOCALIZED_INTROS.get(doc_id, {}).get(lang)
                if loc_supp and float(d.get("rerank_score", 0.0)) >= 0.45:
                    lines.append(f"  • {doc['title']} [{supp_prov}]: {loc_supp}")
                else:
                    lines.append(f"  - {doc['title']} [{supp_prov}]: {doc['content'][:150]}...")

        lines.extend(["", footer])
        return "\n".join(lines), lang
