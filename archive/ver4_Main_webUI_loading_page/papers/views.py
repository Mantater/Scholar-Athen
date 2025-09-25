from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from .forms import UploadPaperForm, SettingsForm
from .models import UploadedPaper, UserSettings
from .tasks import process_paper
from django.urls import reverse
from django.utils.http import urlencode
import csv
import io
from fpdf import FPDF

def dashboard_view(request):
    """
    Handles upload and export on a single page.
    After upload, redirects user to the viewer page.
    If error occurs during processing, shows error on viewer page.
    """
    papers = UploadedPaper.objects.all().order_by("-uploaded_at")
    form = UploadPaperForm()

    # Get settings from session or user
    if request.user.is_authenticated:
        user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
        settings_dict = {
            "citation_style": user_settings.citation_style or "harvard",
            "export_type": user_settings.export_type or "csv",
        }
    else:
        settings_dict = request.session.get('settings', {"citation_style": "harvard", "export_type": "csv"})

    # Remember the last clicked paper ID from session
    last_clicked_id = request.session.get("last_clicked_id")

    if request.method == "POST" and "upload_file" in request.POST:
        form = UploadPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save()
            try:
                process_paper(paper.id, settings_dict=settings_dict)
                return redirect("loading_page", paper_id=paper.id)
            except Exception as e:
                query_string = urlencode({"error": str(e)})
                url = reverse("viewer_detail", args=[paper.id]) + f"?{query_string}"
                return redirect(url)

    return render(request, "papers/dashboard.html", {
        "form": form,
        "papers": papers,
        "settings": settings_dict,
        "last_clicked_id": last_clicked_id,
    })

def viewer_default_view(request):
    """
    Default viewer page when no paper_id is provided.
    If a last-clicked paper exists in session, go there first.
    Otherwise, show the most recent uploaded one.
    If none exist, show a 'no papers uploaded' page.
    """
    last_clicked_id = request.session.get("last_clicked_id")
    if last_clicked_id and UploadedPaper.objects.filter(id=last_clicked_id).exists():
        return redirect("viewer_detail", paper_id=last_clicked_id)

    papers = UploadedPaper.objects.all().order_by("-uploaded_at")
    if papers.exists():
        return redirect("viewer_detail", paper_id=papers.first().id)

    return render(request, "papers/viewer_default.html")

def viewer_view(request, paper_id):
    """
    Display a paper and its citations.
    Handles export requests based on format.
    Also shows error messages if passed via query string.
    """
    paper = get_object_or_404(UploadedPaper, id=paper_id)

    # Save last clicked paper in session
    request.session["last_clicked_id"] = paper.id

    citations = paper.citations.all()
    error_message = request.GET.get("error")

    export_type = request.GET.get("export")
    if export_type:
        if export_type == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="citations.csv"'
            writer = csv.writer(response)
            writer.writerow(["Title", "Authors", "Year", "Citation", "Link", "Relevance"])
            for c in citations:
                writer.writerow([c.title, c.authors, c.year, c.harvard_citation, c.link, c.relevance])
            return response

        elif export_type == "bibtex":
            response = HttpResponse(content_type="text/plain")
            response["Content-Disposition"] = 'attachment; filename="citations.bib"'
            for i, c in enumerate(citations, 1):
                response.write(
                    f"@article{{cite{i},\n  title={{{c.title}}},\n  author={{{c.authors}}},\n  year={{{c.year}}},\n  url={{{c.link}}}\n}}\n\n"
                )
            return response

        elif export_type == "pdf":
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Arial", size=12)
            for c in citations:
                pdf.multi_cell(0, 5, f"{c.harvard_citation}\n")
            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            pdf_output.seek(0)
            response = HttpResponse(pdf_output, content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="citations.pdf"'
            return response

    return render(request, "papers/viewer.html", {
        "paper": paper,
        "citations": citations,
        "error_message": error_message
    })

def settings_view(request):
    if request.user.is_authenticated:
        settings, _ = UserSettings.objects.get_or_create(user=request.user)
    else:
        settings = None

    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            if settings:
                settings.citation_style = form.cleaned_data['citation_style']
                settings.export_type = form.cleaned_data['export_type']
                settings.save()
            else:
                request.session['settings'] = form.cleaned_data
            return redirect("settings")
    else:
        if settings:
            initial = {"citation_style": settings.citation_style, "export_type": settings.export_type}
        else:
            initial = request.session.get('settings', {})

        form = SettingsForm(initial=initial)

    return render(request, "papers/settings.html", {"form": form})

def loading_page(request, paper_id):
    """
    Temporary loading page while paper is being processed.
    Polls until citations are ready, then redirects to viewer.
    """
    paper = get_object_or_404(UploadedPaper, id=paper_id)

    # If citations already processed, skip loading page
    if paper.citations.exists():
        return redirect("viewer_detail", paper_id=paper_id)

    return render(request, "papers/loading.html", {"paper": paper})
