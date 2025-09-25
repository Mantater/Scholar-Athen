import requests
import xml.etree.ElementTree as ET
import re

class ArxivSearcher:
    def build_query(self, ranked_keywords, summary, top_n=5):
        kws = [kw for kw, _ in ranked_keywords[:top_n]]
        combined = " ".join(kws) + " " + summary
        combined = re.sub(r"[^a-zA-Z0-9\s]", "", combined)
        return "+".join(combined.split())

    def search(self, query, max_results=20):
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
        resp = requests.get(url)
        resp.raise_for_status()
        root = ET.fromstring(resp.text)
        results = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            title = entry.find("{http://www.w3.org/2005/Atom}title").text
            link = entry.find("{http://www.w3.org/2005/Atom}id").text
            summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
            authors = [a.find("{http://www.w3.org/2005/Atom}name").text.strip() for a in entry.findall("{http://www.w3.org/2005/Atom}author")]
            year = entry.find("{http://www.w3.org/2005/Atom}published").text[:4]
            results.append({"title": title.strip(), "link": link.strip(), "summary": summary.strip(), "authors": authors, "year": year})
        return results
