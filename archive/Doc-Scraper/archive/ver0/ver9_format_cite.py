import re
import requests
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime

# -----------------------------
# Build arXiv Query
# -----------------------------
def build_arxiv_query(ranked_keywords: list[tuple[str, float]], summary: str, top_n_keywords: int = 5) -> str:
    """
    Combine top-ranked keywords and paragraph summary into a single query string for arXiv search.

    Parameters:
        ranked_keywords (list[tuple[str, float]]): List of (keyword, relevance) tuples.
        summary (str): Paragraph summary.
        top_n_keywords (int, optional): How many top keywords to include. Default is 5.

    Returns:
        str: Clean query string suitable for arXiv search.
    """
    keywords = [kw for kw, score in ranked_keywords[:top_n_keywords]]
    combined_text = " ".join(keywords) + " " + summary
    combined_text = re.sub(r"[^a-zA-Z0-9\s]", "", combined_text)
    query = "+".join(combined_text.split())
    return query

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
        authors = [author.find("{http://www.w3.org/2005/Atom}name").text.strip()
                for author in entry.findall("{http://www.w3.org/2005/Atom}author")]

        # Extract published year
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        year = published[:4] if published else "n.d."

        # Extract DOI if present
        doi_elem = entry.find("{http://arxiv.org/schemas/atom}doi")
        doi = doi_elem.text.strip() if doi_elem is not None else None

        results.append({
            "title": title.strip(),
            "link": link.strip(),
            "summary": summary.strip(),
            "authors": authors,
            "year": year,
            "doi": doi
        })
    
    return results

# -----------------------------
# Rank papers by semantic relevance
# -----------------------------
# Load SBERT model (can be reused for multiple paragraphs)
model = SentenceTransformer('all-MiniLM-L6-v2')

def rank_papers_by_relevance(paragraph_summary: str, papers: list[dict], top_k: int = 3):
    """
    Rank candidate papers by semantic relevance to a paragraph summary using SBERT embeddings.

    Parameters:
        paragraph_summary (str): Paragraph summary text.
        papers (list[dict]): List of papers with 'title', 'link', 'summary'.
        top_k (int, optional): Number of top papers to return. Default is 3.

    Returns:
        list[dict]: Top papers with additional 'relevance' key (0-100%).
    """
    if not papers:
        return []

    para_emb = model.encode(paragraph_summary)
    paper_embs = model.encode([paper['summary'] for paper in papers])

    similarities = []
    for idx, paper_emb in enumerate(paper_embs):
        sim = np.dot(para_emb, paper_emb) / (np.linalg.norm(para_emb) * np.linalg.norm(paper_emb))
        similarities.append((idx, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)

    top_papers = []
    for idx, sim in similarities[:top_k]:
        paper = papers[idx].copy()
        paper['relevance'] = round(sim * 100, 2)
        top_papers.append(paper)

    return top_papers

# -----------------------------
# Harvard citation formatter
# -----------------------------
def format_harvard(paper):
    """
    Format a paper dictionary into Harvard citation style.

    Rules implemented:
      - 1-3 authors: list all authors
      - 4+ authors: first author + 'et al.'
      - Online-only paper with DOI: include DOI, no access date
      - Online-only paper without DOI: include URL and accessed date

    Parameters:
        paper (dict): Paper dictionary with keys:
                      'authors', 'year', 'title', 'link', optional 'doi'.

    Returns:
        str: Formatted Harvard citation string.
    """
    authors_list = paper.get('authors', [])
    year = paper.get('year', 'n.d.')
    title = paper.get('title', 'No title')
    link = paper.get('link', '')
    doi = paper.get('doi', None)
    accessed = datetime.now().strftime("%d %b %Y")

    # Format authors
    num_authors = len(authors_list)
    if num_authors == 0:
        authors_str = ""
    elif num_authors == 1:
        authors_str = f"{authors_list[0].split()[-1]}, {authors_list[0].split()[0][0]}."
    elif num_authors == 2:
        a1, a2 = [a.split() for a in authors_list[:2]]
        authors_str = f"{a1[-1]}, {a1[0][0]}. and {a2[-1]}, {a2[0][0]}."
    elif num_authors == 3:
        a1, a2, a3 = [a.split() for a in authors_list[:3]]
        authors_str = f"{a1[-1]}, {a1[0][0]}., {a2[-1]}, {a2[0][0]} and {a3[-1]}, {a3[0][0]}."
    else:
        first_author = authors_list[0].split()
        authors_str = f"{first_author[-1]}, {first_author[0][0]}. et al."

    # Harvard citation
    if doi:
        citation = f"{authors_str} ({year}) '{title}', arXiv. doi:{doi}."
    else:
        citation = f"{authors_str} ({year}) '{title}', arXiv. Available at: {link} (Accessed: {accessed})."

    return citation

# -----------------------------
# Main Test
# -----------------------------
if __name__ == "__main__":
    ranked_keywords = [
        ('quantum computing', 0.95),
        ('exponentially faster', 0.9),
        ('stable qubits', 0.85),
        ('error-correction', 0.85),
        ('computational problems', 0.8)
    ]

    summary = ("Quantum computing aims to solve certain computational problems exponentially faster "
               "than classical computers through advancements in stable qubits and error-correction techniques.")

    # Step 1: Build arXiv query
    query = build_arxiv_query(ranked_keywords, summary)
    print("Generated arXiv Query:")
    print(query)
    print()

    # Step 2: Fetch candidate papers
    papers = search_arxiv(query)
    print(f"Fetched {len(papers)} papers from arXiv.\n")

    # Step 3: Rank papers by semantic relevance
    top_papers = rank_papers_by_relevance(summary, papers)

    # Step 4: Print top 3 papers with Harvard citation
    print("Top 3 Relevant Papers:\n")
    for i, paper in enumerate(top_papers, 1):
        authors = ", ".join(paper['authors'])
        year = paper['year']
        relevance = paper['relevance']

        print(f"{i}. {paper['title']} ({relevance:.3g}%)")
        print(f"   Authors: {authors}")
        print(f"   Link: {paper['link']}")
        print(f"   Summary: {paper['summary'][:200]}...")  # First 200 chars
        
        # Print Harvard citation
        citation = format_harvard(paper)
        print(f"\n   Harvard Citation: {citation}\n")