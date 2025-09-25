from django import forms
from .models import UploadedPaper

class UploadPaperForm(forms.ModelForm):
    class Meta:
        model = UploadedPaper
        fields = ["file"]

class SettingsForm(forms.Form):

    citation_style = forms.ChoiceField(
        label="Citation format",
        choices=[
            ("harvard", "Harvard"),
            ("apa", "APA"),
            ("mla", "MLA"),
            ("chicago", "Chicago"),
            ("bibtex", "BibTeX"),
        ],
        initial="harvard"
    )

    export_type = forms.ChoiceField(
        label="Export as",
        choices=[
            ("csv", "CSV"),
            ("json", "JSON"),
            ("bibtex", "BibTeX"),
            ("pdf", "PDF"),
        ],
        initial="csv"
    )
