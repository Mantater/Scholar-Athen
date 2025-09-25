import re

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
    # Take top N keywords
    keywords = [kw for kw, score in ranked_keywords[:top_n_keywords]]

    # Combine keywords and summary
    combined_text = " ".join(keywords) + " " + summary

    # Clean text: remove non-alphanumeric characters (keep spaces)
    combined_text = re.sub(r"[^a-zA-Z0-9\s]", "", combined_text)

    # Replace spaces with '+' for URL encoding
    query = "+".join(combined_text.split())

    return query

# -----------------------------
# Main Test
# -----------------------------
if __name__ == "__main__":
    # Example: Paragraph 2
    ranked_keywords_2 = [
        ('quantum computing', 0.95),
        ('exponentially faster', 0.9),
        ('stable qubits', 0.85),
        ('error-correction', 0.85),
        ('computational problems', 0.8)
    ]

    summary_2 = ("Quantum computing aims to solve certain computational problems exponentially faster "
                 "than classical computers through advancements in stable qubits and error-correction techniques.")

    # Build query
    query = build_arxiv_query(ranked_keywords_2, summary_2)
    
    print("Generated arXiv Query:")
    print(query)
