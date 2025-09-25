import requests
import xml.etree.ElementTree as ET

def search_arxiv(query, max_results=5):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    response = requests.get(url)
    root = ET.fromstring(response.text)
    
    results = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        link = entry.find("{http://www.w3.org/2005/Atom}id").text
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        results.append({
            "title": title.strip(),
            "link": link.strip(),
            "summary": summary.strip()
        })
    return results

if __name__ == "__main__":
    papers = search_arxiv("quantum computing", max_results=3)
    for i, paper in enumerate(papers, 1):
        print(f"{i}. {paper['title']}")
        print(f"   Link: {paper['link']}")
        print(f"   Summary: {paper['summary'][:200]}...")  # first 200 chars
        print()
