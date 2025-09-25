import fitz  # PyMuPDF
import docx
import spacy
import requests
import json
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import numpy as np

# -----------------------------
# Load spaCy and SBERT models once
# -----------------------------
nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('all-MiniLM-L6-v2')

# -----------------------------
# Load API key
# -----------------------------
load_dotenv(dotenv_path="OR_RPA_KEY.env")
API_KEY = os.getenv("ResearchPaper_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-9b-v2:free"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

# -----------------------------
# File text extraction
# -----------------------------
def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"

    lines = text.split("\n")
    paragraphs, buffer = [], ""
    for line in lines:
        line = line.strip()
        if not line:
            if buffer:
                paragraphs.append(buffer.strip())
                buffer = ""
            continue
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
    doc = docx.Document(docx_path)
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

# -----------------------------
# Paragraph cleaning
# -----------------------------
def clean_paragraph_spacy(text, min_words=10, remove_short=True):
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    if remove_short:
        sentences = [s for s in sentences if len(s.split()) >= min_words]
    return ' '.join(sentences)

def para_processing(filename, doc_type):
    file = f"{filename}.{doc_type}"
    if not os.path.exists(file):
        return []
    if doc_type == "pdf":
        paras = extract_pdf_text(file)
    else:
        paras = extract_docx_text(file)
    cleaned = [clean_paragraph_spacy(p) for p in paras if clean_paragraph_spacy(p)]
    return cleaned

# -----------------------------
# Call LLM
# -----------------------------
def call_llm(prompt):
    """
    Calls the LLM API with the given prompt.
    Raises Exception("Token max reached") if the daily token limit is hit.
    """
    response = requests.post(
        API_URL,
        json={"prompt": prompt, "max_tokens": 10},  # adjust as needed
        headers={"Authorization": f"Bearer {API_KEY}"}
    )

    # Check for HTTP errors
    if response.status_code == 401:
        # Invalid or missing API key
        raise Exception("Token max reached")
    elif response.status_code != 200:
        if "token" in response.text.lower():
            raise Exception("Token max reached")
        else:
            raise Exception(f"LLM API error: {response.text}")

    # Parse JSON safely
    data = response.json()
    if "error" in data and "token" in data["error"].lower():
        raise Exception("Token max reached")

    # Return the text content
    return data["choices"][0]["message"]["content"].strip()

def extract_keywords_and_summary(paragraphs: list[str], get_summary=True):
    keywords_per_paragraph = {}
    summary_per_paragraph = {} if get_summary else None
    for idx, para in enumerate(paragraphs):
        prompt = f"""
        Extract keywords and {'a summary' if get_summary else ''} from the paragraph below.
        Respond ONLY in valid JSON inside a ```json ... ``` code block, with this structure:
        {{
            "keywords": ["keyword1", "keyword2", ...],
            "summary": "short summary here"
        }}
        Paragraph:
        {para}
        """
        llm_text = call_llm(prompt)
        llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()
        try:
            llm_json = json.loads(llm_text_clean)
            keywords_per_paragraph[idx] = llm_json.get("keywords", [])
            if get_summary:
                summary_per_paragraph[idx] = llm_json.get("summary", None)
        except json.JSONDecodeError:
            keywords_per_paragraph[idx] = []
            if get_summary:
                summary_per_paragraph[idx] = ""
    return keywords_per_paragraph, summary_per_paragraph

# -----------------------------
# Rank keywords
# -----------------------------
def rank_keywords_llm(paragraph: str, keywords: list[str]) -> list[tuple[str, float | None]]:
    prompt = f"""
    Rank the following keywords by relevance to the paragraph.
    Paragraph: {paragraph}
    Keywords: {keywords}
    Respond ONLY in JSON: {{"ranked_keywords":[{{"keyword":"example","relevance":0.95}}]}}
    """
    llm_text = call_llm(prompt)
    llm_text_clean = re.sub(r"```json|```", "", llm_text, flags=re.IGNORECASE).strip()
    try:
        llm_json = json.loads(llm_text_clean)
        return [(kw["keyword"], kw["relevance"]) for kw in llm_json["ranked_keywords"]]
    except json.JSONDecodeError:
        return [(kw, None) for kw in keywords]

# -----------------------------
# arXiv search
# -----------------------------
def build_arxiv_query(ranked_keywords: list[tuple[str, float]], summary: str, top_n_keywords=5) -> str:
    keywords = [kw for kw, _ in ranked_keywords[:top_n_keywords]]
    combined = " ".join(keywords) + " " + summary
    combined = re.sub(r"[^a-zA-Z0-9\s]", "", combined)
    return "+".join(combined.split())

def search_arxiv(query: str, max_results=20):
    url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results={max_results}"
    resp = requests.get(url)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    results = []
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        link = entry.find("{http://www.w3.org/2005/Atom}id").text
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        authors = [a.find("{http://www.w3.org/2005/Atom}name").text.strip()
                   for a in entry.findall("{http://www.w3.org/2005/Atom}author")]
        published = entry.find("{http://www.w3.org/2005/Atom}published").text
        year = published[:4] if published else "n.d."
        results.append({"title": title.strip(), "link": link.strip(),
                        "summary": summary.strip(), "authors": authors, "year": year})
    return results

# -----------------------------
# Semantic ranking
# -----------------------------
def rank_papers_by_relevance(paragraph_summary: str, papers: list[dict], top_k=3):
    if not papers:
        return []
    para_emb = model.encode(paragraph_summary)
    paper_embs = model.encode([p['summary'] for p in papers])
    sims = [(i, np.dot(para_emb, pe)/(np.linalg.norm(para_emb)*np.linalg.norm(pe))) for i, pe in enumerate(paper_embs)]
    sims.sort(key=lambda x: x[1], reverse=True)
    top_papers = []
    for idx, sim in sims[:top_k]:
        paper = papers[idx].copy()
        paper['relevance'] = round(sim*100, 2)
        top_papers.append(paper)
    return top_papers

# -----------------------------
# Harvard citation
# -----------------------------
def format_harvard(paper):
    authors_list = paper.get('authors', [])
    year = paper.get('year', 'n.d.')
    title = paper.get('title', 'No title')
    link = paper.get('link', '')
    accessed = datetime.now().strftime("%d %b %Y")
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
    citation = f"{authors_str} ({year}) '{title}', arXiv. Available at: {link} (Accessed: {accessed})."
    return citation

# -----------------------------
# Wrapper for Django task
# -----------------------------
def pipeline_run(file_path, doc_type):
    filename = os.path.splitext(file_path)[0]
    cleaned_paras = para_processing(filename, doc_type)
    if not cleaned_paras:
        return []
    keywords, summaries = extract_keywords_and_summary(cleaned_paras)
    results = []
    for idx, para in enumerate(cleaned_paras):
        ranked = rank_keywords_llm(para, keywords[idx])
        query = build_arxiv_query(ranked, summaries[idx])
        papers = search_arxiv(query)
        top_papers = rank_papers_by_relevance(summaries[idx], papers)
        for paper in top_papers:
            results.append({
                "title": paper['title'],
                "authors": paper['authors'],
                "year": paper['year'],
                "citation": format_harvard(paper),
                "link": paper['link'],
                "relevance": paper['relevance'],
                "matched_text": para
            })
    return results
