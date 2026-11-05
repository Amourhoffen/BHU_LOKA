import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

query = 'ti:"flood" AND (abs:"compound" OR abs:"heatwave" OR abs:"India")'
url = f"http://export.arxiv.org/api/query?search_query={urllib.parse.quote(query)}&start=0&max_results=5&sortBy=relevance"

req = urllib.request.Request(url, headers={'User-Agent': 'BHU_LOKA_Research/1.0'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
        xml_data = response.read()
        root = ET.fromstring(xml_data)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)
        print(f"arXiv Query Successful: Found {len(entries)} matching preprints")
        print("="*60)
        for i, entry in enumerate(entries, 1):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            published = entry.find('atom:published', ns).text[:10]
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')[:300]
            link = entry.find('atom:id', ns).text.strip()
            print(f"{i}. {title} [{published}]")
            print(f"   URL: {link}")
            print(f"   Abstract: {summary}...")
            print("-"*60)
except Exception as e:
    print("arXiv Query Error:", e)
