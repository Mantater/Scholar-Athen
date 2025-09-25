from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .forms import UploadPaperForm, SettingsForm
from .models import UploadedPaper, Citation
from .tasks import process_paper
import csv

def upload_view(request):
    if request.method == "POST":
        form = UploadPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save()
            try:
                # Run pipeline
                result = process_paper(paper.id)

                # Check if citations were returned
                if not result.get("citations"):
                    return render(
                        request,
                        "papers/error.html",
                        {
                            "error_message": (
                                "No citations could be generated for this paper. "
                                "Please try a different file or review your content."
                            )
                        },
                    )

            except Exception as e:
                # Debug log
                print("DEBUG: error caught in upload_view:", str(e))

                # Handle specific errors
                if "token max" in str(e).lower():
                    return render(
                        request,
                        "papers/error.html",
                        {"error_message": "Token limit reached. Please try again later."},
                    )
                else:
                    return render(
                        request,
                        "papers/error.html",
                        {"error_message": str(e)},
                    )

            # If everything is fine, go to viewer
            return redirect("viewer", paper.id)

    else:
        form = UploadPaperForm()

    return render(request, "papers/upload.html", {"form": form})

def viewer_view(request, paper_id):
    paper = get_object_or_404(UploadedPaper, id=paper_id)
    citations = paper.citations.all()
    return render(request, "papers/viewer.html", {"paper": paper, "citations": citations})

def export_view(request, paper_id, fmt):
    paper = get_object_or_404(UploadedPaper, id=paper_id)
    citations = paper.citations.all()

    if fmt == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=citations.csv"
        writer = csv.writer(response)
        writer.writerow(["Title", "Authors", "Year", "Citation", "Link", "Relevance"])
        for c in citations:
            writer.writerow([c.title, c.authors, c.year, c.harvard_citation, c.link, c.relevance])
        return response

    elif fmt == "bibtex":
        response = HttpResponse(content_type="text/plain")
        response["Content-Disposition"] = "attachment; filename=citations.bib"
        for i, c in enumerate(citations, 1):
            response.write(f"@article{{cite{i},\n  title={{{c.title}}},\n  author={{{c.authors}}},\n  year={{{c.year}}},\n  url={{{c.link}}}\n}}\n\n")
        return response

    elif fmt == "pdf":
        # TODO: generate summary PDF (reportlab)
        pass

def settings_view(request):
    return render(request, 'papers/settings.html')