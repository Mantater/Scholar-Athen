from .models import UploadedPaper, Citation
from .pipeline import pipeline_run
from .CitationFormatter import CitationFormatter

def process_paper(paper_id, settings_dict=None, top_k=3):
    """
    Fetches an uploaded paper by ID, runs the processing pipeline
    with settings from `settings_dict`, and stores the extracted citations in the DB.
    """
    paper = UploadedPaper.objects.get(id=paper_id)

    citation_style = settings_dict.get("citation_style", "harvard") if settings_dict else "harvard"
    export_type = settings_dict.get("export_type", "csv") if settings_dict else "csv"

    _, ext = paper.file.name.rsplit(".", 1)
    doc_type = ext.lower()

    results_dict = pipeline_run(
        paper.file.path,
        doc_type,
        top_k=top_k,
        export_type=export_type,
        citation_style=citation_style
    )

    all_results = results_dict.get("results", [])

    # Raise an exception if no results were returned
    if not all_results:
        raise RuntimeError("No citations were generated. Possibly the LLM API limit has been reached.")

    # Clear previous citations
    paper.citations.all().delete()

    # Save new results
    formatter = CitationFormatter()
    for idx, para_result in enumerate(all_results, start=1):
        for paper_data in para_result.get("papers", []):
            citation_text = formatter.format(paper_data, style=citation_style)

            Citation.objects.create(
                paper=paper,
                paragraph_number=idx,
                paragraph_text=para_result.get("paragraph", ""),
                title=paper_data.get("title", ""),
                authors=", ".join(paper_data.get("authors", [])),
                year=paper_data.get("year", ""),
                harvard_citation=citation_text,
                link=paper_data.get("link", ""),
                relevance=paper_data.get("relevance", 0)
            )
