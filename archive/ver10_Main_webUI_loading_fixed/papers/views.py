from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.utils.http import urlencode
import csv
import json
from fpdf import FPDF
from collections import defaultdict
import threading  # for background processing
from .forms import UploadPaperForm, SettingsForm
from .models import UploadedPaper, UserSettings
from .tasks import process_paper

# --- Helper to run paper processing asynchronously ---
def process_paper_async(paper_id, settings_dict):
    """Process paper in background thread with proper error handling and file cleanup"""
    def wrapper():
        paper = None
        try:
            paper = UploadedPaper.objects.get(id=paper_id)
            process_paper(paper_id, settings_dict=settings_dict)
        except Exception as e:
            # If processing fails, delete the paper and its file
            if paper:
                try:
                    # Delete the actual file from storage
                    if paper.file and paper.file.path:
                        import os
                        if os.path.exists(paper.file.path):
                            os.remove(paper.file.path)
                except Exception as file_delete_error:
                    print(f"Error deleting file: {file_delete_error}")
                
                # Delete the paper record from database
                paper.delete()
                
    thread = threading.Thread(target=wrapper)
    thread.daemon = True
    thread.start()

def dashboard_view(request):
    """
    Handles upload and export on a single page.
    After upload, redirects user to the loading page.
    Any errors during upload are shown on dashboard.
    """
    papers = UploadedPaper.objects.all().order_by("-uploaded_at")
    form = UploadPaperForm()

    settings_dict = request.session.get('settings', {"citation_style": "harvard", "export_type": "csv"})
    last_clicked_id = request.session.get("last_clicked_id")

    if request.method == "POST" and "upload_file" in request.POST:
        form = UploadPaperForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate file type before saving
            uploaded_file = request.FILES['file']
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension not in ['pdf', 'docx']:
                query_string = urlencode({"error": "Only PDF and DOCX files are supported."})
                url = reverse("dashboard") + f"?{query_string}"
                return redirect(url)
            
            try:
                paper = form.save(commit=False)
                paper.processing = True
                paper.save()

                # Start processing in background
                process_paper_async(paper.id, settings_dict=settings_dict)

                # Redirect to loading page immediately
                return redirect("loading_page", paper_id=paper.id)
                
            except Exception as e:
                # If initial save fails, show error without saving paper
                query_string = urlencode({"error": f"Upload failed: {str(e)}"})
                url = reverse("dashboard") + f"?{query_string}"
                return redirect(url)

    return render(request, "papers/dashboard.html", {
        "form": form,
        "papers": papers,
        "settings": settings_dict,
        "last_clicked_id": last_clicked_id,
        "error": request.GET.get("error"),
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
    Display a paper and its citations grouped by paragraph.
    Handles export requests based on format.
    """
    paper = get_object_or_404(UploadedPaper, id=paper_id)
    request.session["last_clicked_id"] = paper.id
    citations = paper.citations.all().order_by("paragraph_number")
    error_message = request.GET.get("error")

    # --- Export handling ---
    export_type = request.GET.get("export")
    if export_type:
        if export_type == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="citations.csv"'
            writer = csv.writer(response)
            writer.writerow(["Title", "Authors", "Year", "Citation", "Link", "Relevance"])
            for c in citations:
                writer.writerow([c.title, c.authors, c.year, c.harvard_citation, c.link, int(c.relevance)])
            return response

        elif export_type == "json":
            data = []
            for c in citations:
                data.append({
                    "title": c.title,
                    "authors": c.authors,
                    "year": c.year,
                    "citation": c.harvard_citation,
                    "link": c.link,
                    "relevance": int(c.relevance),
                })
            response = HttpResponse(json.dumps(data, indent=2), content_type="application/json")
            response["Content-Disposition"] = 'attachment; filename="citations.json"'
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
            pdf_bytes = pdf.output(dest='S').encode('latin1')
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response['Content-Disposition'] = 'attachment; filename="citations.pdf"'
            return response

    # --- Group citations by paragraph ---
    paragraphs_dict = defaultdict(list)
    for c in citations:
        paragraphs_dict[c.paragraph_number].append(c)

    paragraphs = []
    for idx, para_num in enumerate(sorted(paragraphs_dict.keys()), 1):
        para_citations = paragraphs_dict[para_num]
        para_text = para_citations[0].paragraph_text or ""
        paragraphs.append({
            "number": para_num,  # Paragraph 1, 2, 3...
            "text": para_text,
            "citations": para_citations,
            "count": len(para_citations)
        })

    # --- User settings ---
    if request.user.is_authenticated:
        user_settings, _ = UserSettings.objects.get_or_create(user=request.user)
        settings_dict = {
            "citation_style": user_settings.citation_style or "harvard",
            "export_type": user_settings.export_type or "csv",
        }
    else:
        settings_dict = request.session.get('settings', {"citation_style": "harvard", "export_type": "csv"})

    return render(request, "papers/viewer.html", {
        "paper": paper,
        "paragraphs": paragraphs,
        "error_message": error_message,
        "settings": settings_dict
    })

def loading_page(request, paper_id):
    """
    Loading page that only redirects if processing is complete or errored
    """
    paper = get_object_or_404(UploadedPaper, id=paper_id)

    # Only redirect if processing is definitely complete or errored
    if not paper.processing and (paper.citations.exists() or paper.error_message):
        params = {}
        if paper.error_message:
            params["error"] = paper.error_message
        url = reverse("viewer_detail", args=[paper.id])
        if params:
            url += "?" + urlencode(params)
        return redirect(url)

    return render(request, "papers/loading.html", {"paper": paper})

def check_processing_status(request, paper_id):
    """AJAX endpoint to check if paper processing is complete"""
    try:
        paper = UploadedPaper.objects.get(id=paper_id)
        
        if paper.error_message:
            return JsonResponse({
                'status': 'error',
                'error': paper.error_message
            })
        elif paper.citations.exists():
            return JsonResponse({
                'status': 'complete',
                'redirect_url': reverse('viewer_detail', args=[paper.id])
            })
        elif paper.processing:
            return JsonResponse({
                'status': 'processing'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'error': 'Processing failed unexpectedly'
            })
            
    except UploadedPaper.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Paper not found'
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
