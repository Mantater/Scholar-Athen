import fitz  # PyMuPDF
import docx  # python-docx
import spacy
import requests
import json
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import re
import os

#%% Text extraction and cleaning

# -----------------------------
# Text Extraction
# -----------------------------
def extract_pdf_text(pdf_path):
    """
    Extracts text paragraphs from a PDF file.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        list[str]: A list of reconstructed paragraphs as strings.
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"

    # Split into lines
    lines = text.split("\n")
    paragraphs = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:  # flush paragraph
                paragraphs.append(buffer.strip())
                buffer = ""
            continue

        # Handle hyphenated words
        if line.endswith("-"):
            buffer += line[:-1]
        elif line.endswith((".", "?", "!")):
            buffer += " " + line
            paragraphs.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + line

    if buffer:
        paragraphs.append(buffer.strip())

    return paragraphs

def extract_docx_text(docx_path):
    """
    Extracts text paragraphs from a DOCX file.
    
    Parameters:
        docx_path (str): Path to the DOCX file.
    
    Returns:
        list[str]: A list of non-empty paragraphs as strings.
    """
    doc = docx.Document(docx_path)  # Open the DOCX file
    
    # Collect each paragraph's text, strip leading/trailing spaces,
    # and skip empty paragraphs (so no blank lines are included).
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

# -----------------------------
# Paragraph handeling
# -----------------------------
def para_processing(filename, doc_type):
    """
    Extracts, cleans, and filters paragraphs from a file.

    Parameters:
        filename (str): Base name of the file (without extension).
        doc_type (str): File type to process ("pdf" or "docx").

    Returns:
        list[str]: Cleaned paragraphs from the file.
    """
    print(f"[INFO] Starting paragraph processing for {filename}.{doc_type}")
    cleaned_paras = []
    file = f"archive\Doc-Scraper\docs\{filename}.{doc_type}"

    if not os.path.exists(file):
        print(f"[ERROR] {doc_type.upper()} file not found: {file}")
        return []

    print(f"[INFO] Extracting paragraphs from {file} ...")
    if doc_type == "pdf":
        file_paras = extract_pdf_text(file)
    elif doc_type == "docx":
        file_paras = extract_docx_text(file)
    else:
        raise ValueError(f"[ERROR] Unsupported file type: {doc_type}")

    print(f"[INFO] Extracted {len(file_paras)} paragraphs. Cleaning...")
    for i, para in enumerate(file_paras, 1):
        cleaned_text = clean_paragraph_spacy(para)
        if cleaned_text:
            cleaned_paras.append(cleaned_text)
        if i % 5 == 0 or i == len(file_paras):
            print(f"[INFO] Processed {i}/{len(file_paras)} paragraphs")

    print(f"[INFO] Finished cleaning: {len(cleaned_paras)} paragraphs remain.\n")
    return cleaned_paras

# -----------------------------
# Cleaning data
# -----------------------------
# Load small English model
nlp = spacy.load("en_core_web_sm")

def clean_paragraph_spacy(text, min_words=10, remove_short=True):
    """
    Cleans a paragraph using spaCy:
    - Removes extra spaces, line breaks, HTML tags
    - Splits into sentences using spaCy
    - Optionally removes very short sentences
    
    Parameters:
        text (str): Input paragraph
        min_words (int): Minimum words to keep a sentence
        remove_short (bool): Whether to remove very short sentences

    Returns:
        str: Cleaned paragraph
    """
    # 1. Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # 2. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. Use spaCy to split into sentences
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # 4. Optionally filter very short sentences
    if remove_short:
        sentences = [s for s in sentences if len(s.split()) >= min_words]
    
    # 5. Join back into a single paragraph
    return ' '.join(sentences)

#%% Run LLM to extract keywords and summaries

# -----------------------------
# Config
# -----------------------------
load_dotenv(dotenv_path=r"api_keys\api_key.env")
API_KEY = os.getenv("OR_RPA_KEY")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2:free"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# -----------------------------
# Calling the LLM API
# -----------------------------
def call_llm(prompt: str) -> str:
    """
    Sends a prompt to the LLM model and retrieves the response text.

    Parameters:
        prompt (str): The input text prompt to send to the LLM.

    Returns:
        str: The LLM response content as a string.
    """
    data = {"model": MODEL_NAME, "messages": [{"role": "user", "content": prompt}]}
    response = requests.post(API_URL, headers=headers, json=data)
    response_json = response.json()
    llm_text = response_json["choices"][0]["message"]["content"].strip()
    return llm_text


# -----------------------------
# Extracting keywords and summaries
# -----------------------------
def extract_keywords_and_summary(paragraphs, get_summary=True, retry_on_fail=True):
    """
    Extracts keywords and optional summaries from a list of paragraphs using an LLM.
    Returns dictionaries mapping paragraph indices to extracted values.

    Parameters:
        paragraphs (list[str]): List of paragraph strings to process.
        get_summary (bool, optional): Whether to generate summaries. Default is True.
        retry_on_fail (bool, optional): Retry once with stricter prompt if JSON parsing fails. Default is True.

    Returns:
        tuple:
            dict[int, list[str]]: Keywords per paragraph, keyed by paragraph index.
            dict[int, str] | None: Summaries per paragraph, or None if get_summary is False.
    """
    print("[INFO] Extracting keywords and summaries from paragraphs using LLM...")
    keywords_per_paragraph = {}
    summary_per_paragraph = {} if get_summary else None

    for idx, paragraph in enumerate(paragraphs):
        print(f"[INFO] Processing paragraph {idx} ...")
        prompt = f"""
        Extract keywords and {'a summary' if get_summary else ''} from the paragraph below.
        Respond ONLY in valid JSON inside a ```json ... ``` code block, with this structure:

        {{
            "keywords": ["keyword1", "keyword2", ...],
            "summary": "short summary here"
        }}

        Paragraph:
        {paragraph}
        """

        llm_text = call_llm(prompt)
        print(f"[DEBUG] Raw LLM response for paragraph {idx}: {llm_text[:100]}...")  # show first 100 chars
        llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()

        try:
            llm_json = json.loads(llm_text_clean)
            keywords_per_paragraph[idx] = llm_json.get("keywords", [])
            if get_summary:
                summary_per_paragraph[idx] = llm_json.get("summary", None)
        except json.JSONDecodeError:
            print(f"[WARN] Failed JSON parse for paragraph {idx}")
            if retry_on_fail:
                print(f"[INFO] Retrying paragraph {idx} with stricter prompt...")
                prompt_retry = f"""
                RESPOND ONLY in JSON, STRICTLY following this format (no extra text):

                {{
                    "keywords": ["keyword1", "keyword2", ...],
                    "summary": "short summary here"
                }}

                Paragraph:
                {paragraph}
                """
                llm_text = call_llm(prompt_retry)
                llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()
                try:
                    llm_json = json.loads(llm_text_clean)
                    keywords_per_paragraph[idx] = llm_json.get("keywords", [])
                    if get_summary:
                        summary_per_paragraph[idx] = llm_json.get("summary", None)
                    continue
                except json.JSONDecodeError:
                    print(f"[ERROR] Retry failed for paragraph {idx}, using heuristic fallback")
            sentences = paragraph.split(".")
            keywords_per_paragraph[idx] = [s.strip().split()[0] for s in sentences if s.strip() != ""][:8]
            if get_summary:
                summary_per_paragraph[idx] = sentences[0].strip() if sentences else None

        print(f"[INFO] Paragraph {idx} keywords: {keywords_per_paragraph[idx]}")
        if get_summary:
            print(f"[INFO] Paragraph {idx} summary: {summary_per_paragraph[idx][:60]}...")  # first 60 chars

    return keywords_per_paragraph, summary_per_paragraph

# -----------------------------
# Rank Keywords by Relevance (LLM)
# -----------------------------
def rank_keywords_llm(paragraph: str, keywords: list[str]) -> list[tuple[str, float | None]]:
    """
    Ranks keywords by their relevance to a paragraph using an LLM.

    Parameters:
        paragraph (str): The paragraph text for context.
        keywords (list[str]): The list of extracted keywords.

    Returns:
        list[tuple[str, float | None]]: Ranked keywords with relevance scores.
            If parsing fails, relevance is returned as None.
    """
    prompt = f"""
    Rank the following keywords by their relevance to the paragraph.

    Paragraph:
    {paragraph}

    Keywords:
    {keywords}

    Respond ONLY in JSON with this format:
    {{
        "ranked_keywords": [
            {{"keyword": "example", "relevance": 0.95}},
            {{"keyword": "example2", "relevance": 0.85}}
        ]
    }}
    """

    llm_text = call_llm(prompt)
    llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()

    try:
        llm_json = json.loads(llm_text_clean)
        ranked = [(kw["keyword"], kw["relevance"]) for kw in llm_json["ranked_keywords"]]
        return ranked
    except json.JSONDecodeError:
        print("⚠️ Failed to parse JSON. Returning unranked keywords.")
        return [(kw, None) for kw in keywords]

#%% Fetch paper info from arXiv
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

#%% Main

# -----------------------------
# Full Pipeline
# -----------------------------
def pipeline(filename, doc_type):
    """
    Full pipeline: extract paragraphs, keywords/summaries, query arXiv, rank papers,
    and print top 3 Harvard-style citations with relevance for each paragraph.

    Parameters:
        filename (str): Base name of the file (without extension).
        doc_type (str): File type to process ("pdf" or "docx").

    Returns:
        None. Prints results directly.
    """
    print(f"[INFO] Starting full pipeline for {filename}.{doc_type}\n")
    cleaned_paras = para_processing(filename, doc_type)
    if not cleaned_paras:
        print("[ERROR] No paragraphs extracted.")
        return

    keywords, summaries = extract_keywords_and_summary(cleaned_paras, get_summary=True)

    for idx, paragraph in enumerate(cleaned_paras):
        print(f"\n[INFO] Processing paragraph {idx} for arXiv search and ranking...")
        if not keywords[idx]:
            print(f"[WARN] Paragraph {idx}: No keywords found.")
            continue

        ranked = rank_keywords_llm(paragraph, keywords[idx])
        print(f"[INFO] Ranked keywords: {ranked}")

        query = build_arxiv_query(ranked, summaries[idx])
        print(f"[INFO] arXiv query: {query}")

        papers = search_arxiv(query)
        print(f"[INFO] Found {len(papers)} candidate papers")

        top_papers = rank_papers_by_relevance(summaries[idx], papers)
        print(f"[INFO] Top {len(top_papers)} papers ranked by semantic relevance:")

        for i, paper in enumerate(top_papers, 1):
            citation = format_harvard(paper)
            print(f"  {i}. {citation} ({paper['relevance']:.3g}%)")

    print("\n[INFO] Pipeline finished.\n")

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    filename = "EJ1172284"
    select = int(input("Select file type to extract (1: PDF, 2: DOCX): "))

    # --- Handle PDF ---
    if select == 1:
        pipeline(filename, "pdf")
        
    # --- Handle DOCX ---
    elif select == 2:
        pipeline(filename, "docx")