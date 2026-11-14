"""
BHU LOKA (bhuloka) - Automated Scientific Paper Fact Extractor & BibTeX Auditor
Extracts verified verbatim evidence, page numbers, bibliographic front-matter,
and BibTeX-to-PDF consistency checks directly from local PDFs.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pypdf


DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
MONOGRAPH_RE = re.compile(r"MoES/IMD/[^\r\n]+")
STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "over", "under", "using",
    "based", "study", "case", "area", "areas", "approach", "model", "urban",
    "multi", "hazard", "assessment", "towards", "across", "data",
}


def resolve_papers_dir(explicit_dir: Optional[str] = None) -> Path:
    if explicit_dir:
        p = Path(explicit_dir).expanduser().resolve()
        if p.is_dir():
            return p
        raise FileNotFoundError(f"Specified --papers-dir does not exist: {explicit_dir}")

    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent.parent / "Research_Papers",
        Path.cwd() / "Research_Papers",
        Path.cwd() / "Bhu Loka - भूलोक" / "Research_Papers",
    ]
    for base in (script_dir, Path.cwd().resolve()):
        for ancestor in [base] + list(base.parents)[:5]:
            candidates.append(ancestor / "Research_Papers")
            candidates.append(ancestor / "Bhu Loka - भूलोक" / "Research_Papers")

    for cand in candidates:
        if cand.is_dir() and any(f.suffix.lower() == ".pdf" for f in cand.iterdir()):
            return cand.resolve()

    raise FileNotFoundError("Could not locate Research_Papers/ directory automatically; pass --papers-dir.")


def list_pdfs(papers_dir: Path) -> List[Path]:
    return sorted([p for p in papers_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"])


def find_paper_file(paper_query: str, papers_dir: Path) -> Optional[Path]:
    direct = Path(paper_query)
    if direct.is_file():
        return direct.resolve()
    pdfs = list_pdfs(papers_dir)
    q = paper_query.lower()
    exact_stem = [p for p in pdfs if p.stem.lower() == q or p.name.lower() == q]
    if exact_stem:
        return exact_stem[0]
    partial = [p for p in pdfs if q in p.name.lower()]
    if partial:
        return partial[0]
    # Fallback: match against Page 1-2 visible author/title text (handles files named after editors, e.g. MAUSAM)
    q_sp = spaceless(q)
    for p in pdfs:
        try:
            reader = pypdf.PdfReader(str(p))
            p1_p2 = "\n".join((reader.pages[i].extract_text() or "") for i in range(min(2, len(reader.pages))))
            if q in p1_p2.lower() or (q_sp and q_sp in spaceless(p1_p2)):
                return p
        except Exception:
            continue
    return None


def dehyphenate(text: str) -> str:
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"\s+", " ", text).strip()


def spaceless(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def clean_doi(raw: str) -> str:
    return raw.strip().rstrip(".,;:)\\]}>")


def is_issn_doi(doi: str) -> bool:
    return "(issn)" in doi.lower()


def parse_page_spec(spec: Optional[str], total_pages: int) -> List[int]:
    if not spec:
        return list(range(total_pages))
    indices: List[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start = max(1, int(start_s))
            end = min(total_pages, int(end_s))
            for p in range(start, end + 1):
                if p - 1 not in indices:
                    indices.append(p - 1)
        else:
            p = int(part)
            if 1 <= p <= total_pages and (p - 1) not in indices:
                indices.append(p - 1)
    return sorted(indices)


def extract_pdf_frontmatter(pdf_path: Path) -> Dict:
    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    page_texts: List[str] = []
    for idx in range(min(3, total_pages)):
        page_texts.append(reader.pages[idx].extract_text() or "")

    p1 = page_texts[0] if len(page_texts) > 0 else ""
    p2 = page_texts[1] if len(page_texts) > 1 else ""
    p3 = page_texts[2] if len(page_texts) > 2 else ""

    raw_meta = dict(reader.metadata or {})
    xmp = {
        "title": str(raw_meta.get("/Title") or "").strip(),
        "author": str(raw_meta.get("/Author") or "").strip(),
        "subject": str(raw_meta.get("/Subject") or "").strip(),
        "doi": str(raw_meta.get("/doi") or raw_meta.get("/WPS-ARTICLEDOI") or "").strip(),
    }

    visible_text = "\n".join(page_texts)
    doi_pool = "\n".join([visible_text, xmp["subject"], xmp["doi"], str(raw_meta.get("/WPS-ARTICLEDOI") or "")])
    all_dois: List[str] = []
    for m in DOI_RE.findall(doi_pool):
        c = clean_doi(m)
        if c not in all_dois:
            all_dois.append(c)
    article_dois = [d for d in all_dois if not is_issn_doi(d)]

    monograph_codes = list(dict.fromkeys(MONOGRAPH_RE.findall(visible_text)))

    p1_lines = [l.strip() for l in p1.splitlines() if l.strip()]
    p2_lines = [l.strip() for l in p2.splitlines() if l.strip()]

    # Detect potentially stale XMP title if non-empty and shares almost no words with Page 1+2 visible text
    xmp_stale = False
    if xmp["title"]:
        t_words = [w for w in re.findall(r"[a-z]{4,}", xmp["title"].lower()) if w not in STOPWORDS]
        vis_sp = spaceless(visible_text)
        if t_words:
            hits = sum(1 for w in t_words if w in vis_sp)
            if hits / len(t_words) < 0.25:
                xmp_stale = True

    author_header_blob = "\n".join(p1_lines[:24] + p2_lines[:15])
    # Restrict Page 2 contribution to short header/title lines (skips long Page 2 abstract prose in papers like MAUSAM)
    p2_title_cands = [l for l in p2_lines[:8] if len(l) <= 75 and not l.lower().startswith(("abstract", "recent ", "circulation"))]
    title_block_text = "\n".join(
        p1_lines[:16]
        + p2_title_cands
        + [pdf_path.name]
        + ([] if xmp_stale else [xmp["title"]])
    )

    return {
        "path": pdf_path,
        "filename": pdf_path.name,
        "total_pages": total_pages,
        "p1_lines": p1_lines,
        "p2_lines": p2_lines,
        "visible_p1_p3": visible_text,
        "header_blob": author_header_blob,
        "spaceless_visible": spaceless(visible_text),
        "spaceless_header": spaceless(author_header_blob),
        "spaceless_title_block": spaceless(title_block_text),
        "xmp": xmp,
        "xmp_stale": xmp_stale,
        "article_dois": article_dois,
        "all_dois": all_dois,
        "monograph_codes": monograph_codes,
    }


def print_metadata(info: Dict) -> None:
    print("=" * 78)
    print(f"FILE        : {info['filename']} ({info['total_pages']} pages)")
    print(f"ARTICLE DOIs: {', '.join(info['article_dois']) if info['article_dois'] else 'None detected on pages 1-3 / XMP'}")
    if info["monograph_codes"]:
        print(f"MONOGRAPH ID: {', '.join(info['monograph_codes'])}")
    print("XMP METADATA:")
    print(f"  /Title    : {info['xmp']['title'] or '(none)'}" + (" [WARNING: STALE XMP - disagrees with Page 1-3 text]" if info["xmp_stale"] else ""))
    print(f"  /Author   : {info['xmp']['author'] or '(none)'}")
    print(f"  /Subject  : {info['xmp']['subject'] or '(none)'}")
    print("VISIBLE PAGE 1 TOP LINES:")
    for idx, line in enumerate(info["p1_lines"][:22], 1):
        print(f"  P1.{idx:02d}: {line[:150]}")
    if info["p2_lines"]:
        print("VISIBLE PAGE 2 TOP LINES:")
        for idx, line in enumerate(info["p2_lines"][:12], 1):
            print(f"  P2.{idx:02d}: {line[:150]}")
    print("=" * 78)


def extract_facts(
    pdf_path: Path,
    query_term: Optional[str] = None,
    terms: Optional[List[str]] = None,
    match_all: bool = False,
    regex_pattern: Optional[str] = None,
    page_spec: Optional[str] = None,
    context_lines: int = 2,
    max_matches: int = 5,
) -> None:
    reader = pypdf.PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    target_pages = parse_page_spec(page_spec, total_pages)
    matches_found: List[Dict] = []

    compiled_re = re.compile(regex_pattern, re.IGNORECASE) if regex_pattern else None
    mode_desc = (
        f"regex /{regex_pattern}/"
        if regex_pattern
        else (f"terms {terms} ({'AND' if match_all else 'OR'})" if terms else f"query '{query_term}'")
    )

    print(f"\nScanning: {pdf_path.name} ({total_pages} pages, checking {len(target_pages)} pages)")
    print(f"Search  : {mode_desc}")
    print("=" * 78)

    for page_idx in target_pages:
        raw_text = reader.pages[page_idx].extract_text() or ""
        if not raw_text:
            continue

        lines = [l.rstrip() for l in raw_text.splitlines()]
        for i, line in enumerate(lines):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            raw_ctx = " ".join(l.strip() for l in lines[start:end] if l.strip())
            dehyph_line = dehyphenate(line)
            dehyph_ctx = dehyphenate(raw_ctx)

            matched_mode: Optional[str] = None
            if compiled_re:
                if compiled_re.search(line) or compiled_re.search(dehyph_line):
                    matched_mode = "regex"
            elif terms:
                clean_terms = [t.strip() for t in terms if t.strip()]
                low_line = dehyph_line.lower()
                low_ctx = dehyph_ctx.lower()
                sp_ctx = spaceless(dehyph_ctx)
                if match_all:
                    if clean_terms[0].lower() in low_line and all(t.lower() in low_ctx for t in clean_terms):
                        matched_mode = "terms-all"
                    elif spaceless(clean_terms[0]) in spaceless(dehyph_line) and all(spaceless(t) in sp_ctx for t in clean_terms):
                        matched_mode = "terms-all (spaceless-fallback)"
                else:
                    if any(t.lower() in low_line for t in clean_terms):
                        matched_mode = "terms-any"
                    elif any(spaceless(t) in spaceless(dehyph_line) for t in clean_terms):
                        matched_mode = "terms-any (spaceless-fallback)"
            elif query_term:
                q_low = query_term.lower()
                if q_low in line.lower() or q_low in dehyph_line.lower():
                    matched_mode = "exact"
                elif spaceless(query_term) and spaceless(query_term) in spaceless(dehyph_line):
                    matched_mode = "spaceless-fallback"

            if matched_mode:
                matches_found.append(
                    {
                        "page": page_idx + 1,
                        "mode": matched_mode,
                        "line": line.strip(),
                        "context": raw_ctx,
                    }
                )
                if len(matches_found) >= max_matches:
                    break
        if len(matches_found) >= max_matches:
            break

    if not matches_found:
        print(f"No direct occurrence found for {mode_desc}.")
        return

    for idx, match in enumerate(matches_found, 1):
        print(f"\n[EVIDENCE #{idx}] -> Page {match['page']} | Match Mode: {match['mode']}")
        print("Verbatim Context:")
        print(f'"{match["context"]}"')
        print("-" * 78)


# ---------------------------------------------------------------------------
# BibTeX Parsing & Automated Verification Against Local PDFs
# ---------------------------------------------------------------------------

def clean_latex_str(val: str) -> str:
    val = re.sub(r"\\['\"`^~=.uvHc]\{?([A-Za-z])\}?", r"\1", val)
    val = val.replace(r"\&", "&").replace("~", " ")
    val = re.sub(r"[{}]", "", val)
    return re.sub(r"\s+", " ", val).strip()


def parse_bibtex_file(bib_path: Path) -> List[Dict]:
    text = bib_path.read_text(encoding="utf-8", errors="replace")
    entries: List[Dict] = []
    pos = 0
    n = len(text)
    header_re = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,")

    while pos < n:
        m = header_re.search(text, pos)
        if not m:
            break
        etype = m.group(1).lower()
        ekey = m.group(2).strip()
        line_no = text[: m.start()].count("\n") + 1
        brace_depth = 1
        idx = m.end()
        while idx < n and brace_depth > 0:
            ch = text[idx]
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
            idx += 1
        body = text[m.end() : idx - 1] if brace_depth == 0 else text[m.end() :]
        pos = idx

        fields: Dict[str, str] = {}
        fpos = 0
        blen = len(body)
        while fpos < blen:
            fm = re.search(r"(\w+)\s*=\s*", body[fpos:])
            if not fm:
                break
            fname = fm.group(1).lower()
            vstart = fpos + fm.end()
            while vstart < blen and body[vstart].isspace():
                vstart += 1
            if vstart >= blen:
                break
            if body[vstart] == "{":
                depth = 1
                j = vstart + 1
                while j < blen and depth > 0:
                    if body[j] == "{":
                        depth += 1
                    elif body[j] == "}":
                        depth -= 1
                    j += 1
                raw_val = body[vstart + 1 : j - 1]
                fpos = j
            elif body[vstart] == '"':
                j = vstart + 1
                while j < blen and not (body[j] == '"' and body[j - 1] != "\\"):
                    j += 1
                raw_val = body[vstart + 1 : j]
                fpos = j + 1
            else:
                j = vstart
                while j < blen and body[j] not in ",\r\n":
                    j += 1
                raw_val = body[vstart:j]
                fpos = j
            fields[fname] = clean_latex_str(raw_val)

        entries.append({"type": etype, "key": ekey, "line": line_no, "fields": fields})
    return entries


def parse_bib_authors(author_field: str) -> List[Tuple[str, str]]:
    """Return list of (surname, primary_given_name) tuples."""
    if not author_field:
        return []
    parts = [p.strip() for p in re.split(r"\s+and\s+", author_field, flags=re.IGNORECASE) if p.strip()]
    parsed: List[Tuple[str, str]] = []
    for p in parts:
        if "," in p:
            last, first = [x.strip() for x in p.split(",", 1)]
            given_tokens = re.findall(r"[A-Za-z]{3,}", first)
            surname_tokens = re.findall(r"[A-Za-z]{2,}", last)
            surname = surname_tokens[-1] if surname_tokens else last
            given = given_tokens[0] if given_tokens else ""
            parsed.append((surname, given))
        else:
            tokens = re.findall(r"[A-Za-z]{2,}", p)
            if tokens:
                surname = tokens[-1]
                given = tokens[0] if len(tokens) > 1 and len(tokens[0]) >= 3 else ""
                parsed.append((surname, given))
    return parsed


def match_bib_to_pdf(entry: Dict, pdf_records: List[Dict]) -> Optional[Dict]:
    fields = entry["fields"]
    bib_doi = clean_doi(fields.get("doi", "")).lower()
    bib_authors = parse_bib_authors(fields.get("author", ""))
    first_surname = bib_authors[0][0].lower() if bib_authors else ""
    title_words = [w for w in re.findall(r"[a-z]{5,}", fields.get("title", "").lower()) if w not in STOPWORDS]
    bib_number = fields.get("number", "")

    best_score = 0
    best_rec: Optional[Dict] = None

    for rec in pdf_records:
        score = 0
        if bib_doi and any(bib_doi == d.lower() for d in rec["article_dois"]):
            score += 8
        if bib_number and len(bib_number) >= 6 and spaceless(bib_number) in rec["spaceless_visible"]:
            score += 5
        fname_sp = spaceless(rec["filename"])
        title_hits = sum(1 for w in title_words if w in rec["spaceless_title_block"] or w in rec["spaceless_visible"]) if title_words else 0
        title_ratio = (title_hits / len(title_words)) if title_words else 0.0

        if first_surname and len(first_surname) >= 4:
            if first_surname in fname_sp:
                score += 5
            elif first_surname in rec["spaceless_header"] and (title_ratio >= 0.25 or "moes/imd" in bib_number.lower()):
                score += 5
        if first_surname == "westen" and "west" in fname_sp:
            score += 3
        if title_words and title_ratio >= 0.45:
            score += 4
        if score > best_score:
            best_score = score
            best_rec = rec

    return best_rec if best_score >= 5 else None


def audit_bibtex(bib_path: Path, papers_dir: Path) -> int:
    entries = parse_bibtex_file(bib_path)
    pdf_paths = list_pdfs(papers_dir)
    pdf_records = [extract_pdf_frontmatter(p) for p in pdf_paths]

    print(f"BibTeX Audit: {bib_path} ({len(entries)} entries vs {len(pdf_records)} PDFs in {papers_dir})")
    print("=" * 78)

    mismatches_total = 0

    for entry in entries:
        key = entry["key"]
        fields = entry["fields"]
        rec = match_bib_to_pdf(entry, pdf_records)

        if rec is None:
            print(f"[NO_LOCAL_PDF] @{entry['type']}{{{key}}} (line {entry['line']}) -- Cannot verify against local Research_Papers/.")
            continue

        issues: List[str] = []
        notes: List[str] = []

        # 1. Title token coverage vs actual title block (Page 1-2 header + filename + non-stale XMP Title)
        title_words = [w for w in re.findall(r"[a-z]{4,}", fields.get("title", "").lower()) if w not in STOPWORDS]
        if title_words:
            missing_tw = [w for w in title_words if w not in rec["spaceless_title_block"]]
            ratio = (len(title_words) - len(missing_tw)) / len(title_words)
            if ratio < 0.70:
                issues.append(f"Title mismatch ({ratio:.0%} overlap in header/title; unverified words: {', '.join(missing_tw[:6])})")

        # 2. Author audit (verify against Page 1-2 header lines only; handle initials like C.J. van Westen)
        bib_authors = parse_bib_authors(fields.get("author", ""))
        header_sp = rec["spaceless_header"]
        visible_sp = rec["spaceless_visible"]
        has_author_header = bool(bib_authors and spaceless(bib_authors[0][0]) in header_sp)
        if bib_authors and has_author_header:
            bad_surnames = [s for s, _ in bib_authors if spaceless(s) not in header_sp and spaceless(s) not in visible_sp]
            bad_given = []
            for s, g in bib_authors:
                if not g or len(g) < 3:
                    continue
                s_sp = spaceless(s)
                g_sp = spaceless(g)
                if s_sp in header_sp and g_sp not in header_sp:
                    # Allow initial match when PDF uses initials (e.g., C.J. van Westen, P.D. Safai)
                    if re.search(rf"{g_sp[0]}[a-z]{{0,2}}{s_sp}", header_sp) or re.search(rf"\b{g_sp[0]}\s*\.", rec["header_blob"], re.IGNORECASE):
                        continue
                    bad_given.append(f"{g} {s}")
            if bad_surnames:
                issues.append(f"Unverified co-author surname(s) not in PDF header: {', '.join(bad_surnames)}")
            if bad_given:
                issues.append(f"Author given-name mismatch vs PDF header: {', '.join(bad_given)}")
        elif bib_authors:
            notes.append("Author block absent from downloaded PDF front excerpt; verified DOI/title/venue metadata.")

        # 3. DOI check
        bib_doi = clean_doi(fields.get("doi", ""))
        if rec["article_dois"]:
            if bib_doi:
                if not any(bib_doi.lower() == d.lower() for d in rec["article_dois"]):
                    issues.append(f"DOI mismatch: bib has '{bib_doi}', PDF has '{rec['article_dois'][0]}'")
            else:
                notes.append(f"PDF contains DOI '{rec['article_dois'][0]}' (currently omitted in .bib)")

        # 4. Year / Volume / Pages / Monograph Number
        bib_year = fields.get("year", "").strip()
        full_sp = visible_sp + spaceless(rec["xmp"]["subject"]) + spaceless(rec["filename"])
        if bib_year and bib_year not in full_sp:
            issues.append(f"Year '{bib_year}' not found in PDF front-matter/XMP/filename")

        bib_vol = fields.get("volume", "").strip()
        if bib_vol and bib_vol.lower() not in rec["visible_p1_p3"].lower() and bib_vol.lower() not in rec["xmp"]["subject"].lower():
            # Allow GRL volume in subject
            issues.append(f"Volume '{bib_vol}' not found in PDF Pages 1-3 or XMP Subject")

        bib_pages = fields.get("pages", "").strip()
        if bib_pages:
            start_pg = re.split(r"[-–—]+", bib_pages)[0].strip().lower()
            if start_pg and start_pg not in full_sp:
                issues.append(f"Pages/article ID '{bib_pages}' not found in PDF front-matter or XMP")

        bib_num = fields.get("number", "").strip()
        if entry["type"] == "techreport" and bib_num:
            if spaceless(bib_num) not in visible_sp:
                issues.append(f"Report number '{bib_num}' disagrees with PDF (found: {', '.join(rec['monograph_codes']) or 'different code'})")

        bib_journal = fields.get("journal", "").strip()
        if bib_journal:
            j_words = [w for w in re.findall(r"[a-z]{4,}", bib_journal.lower()) if w not in {"journal", "international", "quarterly", "geography", "geophysics", "online", "library"}]
            j_src = visible_sp + spaceless(rec["xmp"]["subject"]) + spaceless(rec["filename"])
            if j_words and not any(w in j_src for w in j_words):
                issues.append(f"Journal '{bib_journal}' disagrees with PDF venue/XMP Subject ('{rec['xmp']['subject'] or rec['filename']}')")

        if issues:
            mismatches_total += 1
            print(f"[MISMATCH] @{entry['type']}{{{key}}} (line {entry['line']}) <-> {rec['filename']}")
            for iss in issues:
                print(f"  - {iss}")
            for nt in notes:
                print(f"  * Note: {nt}")
        else:
            status = "VERIFIED" if not notes else "VERIFIED_WITH_NOTE"
            print(f"[{status}] @{entry['type']}{{{key}}} (line {entry['line']}) <-> {rec['filename']}")
            for nt in notes:
                print(f"  * Note: {nt}")

    print("=" * 78)
    print(f"Summary: {mismatches_total} matched entries with metadata/citation mismatches.")
    return 1 if mismatches_total > 0 else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract verified paper quotes, metadata, and BibTeX audits from PDFs")
    parser.add_argument("--paper", help="Partial or full name/path of the PDF")
    parser.add_argument("--query", help="Word or phrase to search")
    parser.add_argument("--terms", help="Comma-separated terms to search")
    parser.add_argument("--match-all", action="store_true", help="Require all --terms to match in the same snippet window")
    parser.add_argument("--regex", help="Regex pattern to search")
    parser.add_argument("--pages", help="1-based page slice (e.g. '1-3,10')")
    parser.add_argument("--context-lines", type=int, default=2, help="Context lines before/after matching line")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of matches")
    parser.add_argument("--metadata", action="store_true", help="Extract bibliographic front-matter from Page 1-3 + XMP")
    parser.add_argument("--list", action="store_true", help="List available PDFs in Research_Papers/")
    parser.add_argument("--audit-bib", help="Verify a .bib file against local PDFs in Research_Papers/")
    parser.add_argument("--papers-dir", help="Explicit Research_Papers directory path")

    args = parser.parse_args()
    papers_dir = resolve_papers_dir(args.papers_dir)

    if args.list:
        pdfs = list_pdfs(papers_dir)
        print(f"Research Papers Directory: {papers_dir} ({len(pdfs)} PDFs)")
        for p in pdfs:
            info = extract_pdf_frontmatter(p)
            doi_str = info["article_dois"][0] if info["article_dois"] else "no DOI in p1-3/XMP"
            print(f" - {p.name} ({info['total_pages']}p | {doi_str})")
        return

    if args.audit_bib:
        bib_path = Path(args.audit_bib).resolve()
        if not bib_path.is_file():
            print(f"Error: BibTeX file not found: {bib_path}")
            sys.exit(1)
        rc = audit_bibtex(bib_path, papers_dir)
        sys.exit(rc)

    if not args.paper:
        parser.error("Provide --paper, --list, or --audit-bib.")

    pdf_path = find_paper_file(args.paper, papers_dir)
    if not pdf_path:
        print(f"Error: Could not find paper matching '{args.paper}' in {papers_dir}")
        for p in list_pdfs(papers_dir):
            print(" -", p.name)
        sys.exit(1)

    if args.metadata:
        print_metadata(extract_pdf_frontmatter(pdf_path))
        if not (args.query or args.terms or args.regex):
            return

    if not (args.query or args.terms or args.regex):
        parser.error("Provide --query, --terms, --regex, or --metadata.")

    terms_list = [t.strip() for t in args.terms.split(",")] if args.terms else None
    extract_facts(
        pdf_path,
        query_term=args.query,
        terms=terms_list,
        match_all=args.match_all,
        regex_pattern=args.regex,
        page_spec=args.pages,
        context_lines=args.context_lines,
        max_matches=args.limit,
    )


if __name__ == "__main__":
    main()
