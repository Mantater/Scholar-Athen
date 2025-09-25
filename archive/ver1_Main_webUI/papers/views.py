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

    if request.method == "POST" and "upload_file" in request.POST:
        form = UploadPaperForm(request.POST, request.FILES)
        if form.is_valid():
            paper = form.save()
            try:
                # Process the paper with the settings
                process_paper(paper.id, settings_dict=settings_dict)
                # Redirect to viewer page after success
                return redirect("viewer", paper.id)
            except Exception as e:
                # Encode the error message for URL
                query_string = urlencode({"error": str(e)})
                # Build the URL for viewer page with query string
                url = reverse("viewer", args=[paper.id]) + f"?{query_string}"
                # Redirect to viewer page with error message
                return redirect(url)
            
    return render(request, "papers/dashboard.html", {
        "form": form,
        "papers": papers,
        "settings": settings_dict
    })

def viewer_view(request, paper_id):
    """
    Display a paper and its citations.
    Handles export requests based on format.
    Also shows error messages if passed via query string.
    """
    paper = get_object_or_404(UploadedPaper, id=paper_id)
    citations = paper.citations.all()

    # Check for error message from upload processing
    error_message = request.GET.get("error")  # None if no error

    # Handle export requests
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

    # Render the viewer page with optional error_message
    return render(request, "papers/viewer.html", {
        "paper": paper,
        "citations": citations,
        "error_message": error_message  # Will show box if not None
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
