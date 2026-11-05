"""
BHU LOKA (भूलोक) - Automated Scientific Paper Fact Extractor
Purpose: Extracts exact text matches, page numbers, and paragraphs from research papers
to guarantee zero extrapolation and 100% evidence-based answers.
"""

import os
import sys
import argparse
import pypdf

def find_paper_file(paper_query, papers_dir):
    files = [f for f in os.listdir(papers_dir) if f.lower().endswith('.pdf')]
    matches = [f for f in files if paper_query.lower() in f.lower()]
    if matches:
        return os.path.join(papers_dir, matches[0])
    return None

def extract_facts(pdf_path, query_term, max_matches=5):
    reader = pypdf.PdfReader(pdf_path)
    total_pages = len(reader.pages)
    matches_found = []
    
    print(f"\nScanning: {os.path.basename(pdf_path)} ({total_pages} pages)")
    print(f"Target Query: '{query_term}'")
    print("=" * 70)
    
    for page_idx in range(total_pages):
        text = reader.pages[page_idx].extract_text()
        if not text:
            continue
            
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if query_term.lower() in line.lower():
                # Grab a snippet of 3 lines before and after for context
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = " ".join([l.strip() for l in lines[start:end]])
                matches_found.append({
                    'page': page_idx + 1,
                    'line': line.strip(),
                    'context': context
                })
                if len(matches_found) >= max_matches:
                    break
        if len(matches_found) >= max_matches:
            break
            
    if not matches_found:
        print(f"No direct text occurrence found for '{query_term}'.")
        return
        
    for idx, match in enumerate(matches_found, 1):
        print(f"\n[EVIDENCE #{idx}] -> Page {match['page']}")
        print(f"Exact Quote Context:")
        print(f'"{match["context"]}"')
        print("-" * 70)

def main():
    parser = argparse.ArgumentParser(description="Extract exact paper quotes by keyword")
    parser.add_argument("--paper", required=True, help="Partial or full name of the PDF")
    parser.add_argument("--query", required=True, help="Word or phrase to search")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of matches")
    
    args = parser.parse_args()
    
    # Resolve Research_Papers path relative to script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    papers_dir = os.path.join(project_root, "Research_Papers")
    
    pdf_path = find_paper_file(args.paper, papers_dir)
    if not pdf_path:
        print(f"Error: Could not find paper matching '{args.paper}' in {papers_dir}")
        print("Available papers:")
        for f in os.listdir(papers_dir):
            if f.endswith('.pdf'):
                print(" -", f)
        sys.exit(1)
        
    extract_facts(pdf_path, args.query, args.limit)

if __name__ == '__main__':
    main()

