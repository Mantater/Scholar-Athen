from .Extractor import TextExtractor
from .Cleaner import ParagraphCleaner
from .LLMClient import LLMClient
from .QueryAPI import ArxivSearcher
from .SemanticRanker import SemanticRanker
from .CitationFormatter import CitationFormatter
from django.conf import settings
import io, csv
from fpdf import FPDF

def pipeline_run(file_path, doc_type, top_k=3, export_type=None, citation_style="harvard"):
    """
    Runs the full paper processing pipeline using class-based components.

    Args:
        file_path (str): Path to the uploaded paper.
        doc_type (str): "pdf" or "docx".
        top_k (int): Number of top papers to return per paragraph.
        export_type (str): One of "json", "csv", "bibtex", "pdf". If None, only returns results.
        citation_style (str): One of "harvard", "apa", "mla", "chicago", "bibtex".

    Returns:
        dict: {
            "results": list of dict per paragraph,
            "export": exported content or None
        }
    """
    citation_style = citation_style.get("citation_style", "harvard") if isinstance(citation_style, dict) else citation_style

    # Step 1-2: Extract and clean paragraphs
    extractor = TextExtractor(file_path, doc_type)
    paragraphs = extractor.extract()
    if not paragraphs:
        return {"results": [], "export": None}

    cleaner = ParagraphCleaner(paragraphs)
    cleaned_paragraphs = cleaner.clean()
    if not cleaned_paragraphs:
        return {"results": [], "export": None}

    # Step 3-4: LLM extraction & ranking
    llm_client = LLMClient()
    keywords_dict, summaries_dict = llm_client.extract_keywords_and_summary(cleaned_paragraphs)

    # Detect empty LLM output (likely due to API limit)
    if not keywords_dict or all(len(kw) == 0 for kw in keywords_dict.values()):
        raise RuntimeError("The LLM request could not be completed because the API limit has been reached.")

    searcher = ArxivSearcher()
    ranker = SemanticRanker()
    formatter = CitationFormatter()

    all_results = []

    for idx, para in enumerate(cleaned_paragraphs):
        paragraph_result = {"paragraph": para, "papers": []}
        ranked_keywords = llm_client.rank_keywords(para, keywords_dict[idx])
        query = searcher.build_query(ranked_keywords, summaries_dict[idx])
        papers = searcher.search(query)
        top_papers = ranker.rank(summaries_dict[idx], papers, top_k=top_k)

        for paper in top_papers:
            citation_text = CitationFormatter.format(paper, style=citation_style)
            paper_result = {
                "title": paper["title"],
                "authors": paper["authors"],
                "year": paper["year"],
                "link": paper["link"],
                "relevance": paper["relevance"],
                "citation": citation_text
            }
            paragraph_result["papers"].append(paper_result)

        all_results.append(paragraph_result)

    # -----------------------------
    # Export handling
    # -----------------------------
    export_content = None

    if export_type:
        export_type = export_type.lower()
        if export_type == "json":
            export_content = all_results

        elif export_type == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Paragraph", "Title", "Authors", "Year", "Link", "Relevance", "Citation"])
            for para_result in all_results:
                for paper in para_result["papers"]:
                    writer.writerow([
                        para_result["paragraph"],
                        paper["title"],
                        ", ".join(paper["authors"]),
                        paper["year"],
                        paper["link"],
                        paper["relevance"],
                        paper["citation"]
                    ])
            export_content = output.getvalue()

        elif export_type == "bibtex":
            bib_entries = []
            for para_result in all_results:
                for paper in para_result["papers"]:
                    bib_entries.append(formatter.bibtex(paper))
            export_content = "\n\n".join(bib_entries)

        elif export_type == "pdf":
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for para_result in all_results:
                pdf.multi_cell(0, 5, f"Paragraph: {para_result['paragraph']}\n")
                for paper in para_result["papers"]:
                    pdf.multi_cell(0, 5, f"{paper['citation']}\n")
                pdf.ln(5)
            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            export_content = pdf_output

        else:
            raise ValueError(f"Unsupported export_type: {export_type}")

    return {"results": all_results, "export": export_content}
