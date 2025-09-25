import re
import spacy

nlp = spacy.load("en_core_web_sm")

class ParagraphCleaner:
    def __init__(self, paragraphs, min_words=10):
        self.paragraphs = paragraphs
        self.min_words = min_words

    def clean(self):
        return [self._clean(p) for p in self.paragraphs if self._clean(p)]

    def _clean(self, text):
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        doc = nlp(text)
        sentences = [s.text.strip() for s in doc.sents]
        sentences = [s for s in sentences if len(s.split()) >= self.min_words]
        return ' '.join(sentences)
