from .models import UploadedPaper, Citation
from .pipeline import pipeline_run

def process_paper(paper_id):
    paper = UploadedPaper.objects.get(id=paper_id)
    try:
        # your usual pipeline call
        results = pipeline_run(paper.file.path, "pdf")
        # save results into your Citation model
        for r in results:
            Citation.objects.create(
                paper=paper,
                title=r["title"],
                authors=r["authors"],
                year=r["year"],
                harvard_citation=r["citation"],
                link=r["link"],
                relevance=r["relevance"]
            )
    except Exception as e:
        # propagate the exception so upload_view can catch it
        raise e
