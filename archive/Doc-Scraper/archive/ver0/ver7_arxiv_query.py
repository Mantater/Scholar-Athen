import requests
import xml.etree.ElementTree as ET

# -----------------------------
# Search arXiv
# -----------------------------
def search_arxiv(query: str, max_results: int = 20):
    """
    Queries the arXiv API using the provided search query and fetches candidate papers
    with additional metadata for citation formatting.

    Parameters:
        query (str): Query string (keywords + summary) formatted for arXiv search.
        max_results (int, optional): Maximum number of papers to fetch. Default is 20.

    Returns:
        list[dict]: List of papers with keys:
                    'title', 'link', 'summary', 'authors' (list), 'year'
    """
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    response = requests.get(url)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    results = []

    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        link = entry.find("{http://www.w3.org/2005/Atom}id").text
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        
        # Extract authors
        authors = []
        for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
            name = author.find("{http://www.w3.org/2005/Atom}name").text
            authors.append(name.strip())
        
        # Extract published year
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        year = published[:4] if published else "n.d."

        results.append({
            "title": title.strip(),
            "link": link.strip(),
            "summary": summary.strip(),
            "authors": authors,
            "year": year
        })
    return results

# -----------------------------
# Main Test
# ----------------------------
if __name__ == "__main__":
    # Example query (from previous sub-step)
    query = ("quantum+computing+exponentially+faster+stable+qubits+Quantum+computing+aims+to+solve+"
             "certain+computational+problems+exponentially+faster+than+classical+computers+through+advancements+"
             "in+stable+qubits+and+errorcorrection+techniques")

    # Fetch papers
    papers = search_arxiv(query)

    # Print first few results
    for i, paper in enumerate(papers, 1):
        authors = ", ".join(paper['authors'])
        year = paper['year']
        print(f"{i}. {paper['title']} ({year})")
        print(f"   Authors: {authors}")
        print(f"   Link: {paper['link']}")
        print(f"   Summary: {paper['summary'][:200]}...")  # First 200 chars
        print()
