from django.db import models

# Create your models here.
class UploadedPaper(models.Model):
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Citation(models.Model):
    paper = models.ForeignKey(UploadedPaper, on_delete=models.CASCADE, related_name="citations")
    title = models.TextField()
    authors = models.TextField()
    year = models.CharField(max_length=10)
    harvard_citation = models.TextField()
    link = models.URLField()
    relevance = models.FloatField(null=True, blank=True)
    matched_text = models.TextField(null=True, blank=True)  # phrase from doc
