from .models import UploadedPaper, Citation
from .pipeline import pipeline_run
from .CitationFormatter import CitationFormatter

def process_paper(paper_id, settings_dict=None, top_k=3):
    """
    Improved error handling for paper processing
    """
    try:
        paper = UploadedPaper.objects.get(id=paper_id)
    except UploadedPaper.DoesNotExist:
        raise RuntimeError("Paper not found")
        
    paper.processing = True
    paper.error_message = None
    paper.save()

    citation_style = settings_dict.get("citation_style", "harvard") if settings_dict else "harvard"
    export_type = settings_dict.get("export_type", "csv") if settings_dict else "csv"

    try:
        # Validate file exists
        if not paper.file or not paper.file.path:
            raise RuntimeError("File not found or corrupted")
            
        file_parts = paper.file.name.rsplit(".", 1)
        if len(file_parts) != 2:
            raise RuntimeError("Invalid file format")
            
        _, ext = file_parts
        doc_type = ext.lower()
        
        if doc_type not in ['pdf', 'docx']:
            raise RuntimeError(f"Unsupported file type: {doc_type}")

        results_dict = pipeline_run(
            paper.file.path,
            doc_type,
            top_k=top_k,
            export_type=export_type,
            citation_style=citation_style
        )

        all_results = results_dict.get("results", [])

        if not all_results:
            raise RuntimeError("No citations were generated. The document may not contain suitable content for citation extraction.")

        # Clear previous citations
        paper.citations.all().delete()

        # Save new results
        formatter = CitationFormatter()
        citations_created = 0
        
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
                citations_created += 1

        if citations_created == 0:
            raise RuntimeError("No citations could be saved to database")

        paper.processing = False
        paper.error_message = None
        paper.save()

    except Exception as e:
        paper.processing = False
        paper.error_message = str(e)
        paper.save()
        # Re-raise to be caught by async wrapper
        raise