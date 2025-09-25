from django import forms
from .models import UploadedPaper

class UploadPaperForm(forms.ModelForm):
    class Meta:
        model = UploadedPaper
        fields = ["file"]

class SettingsForm(forms.Form):
    min_words = forms.IntegerField(initial=10)
    citation_style = forms.ChoiceField(
        choices=[("harvard", "Harvard"), ("apa", "APA"), ("mla", "MLA")]
    )
