import fitz
import docx
import os

class TextExtractor:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.doc_type = os.path.splitext(filepath)[1].lower()[1:]  # 'pdf' or 'docx'

    def extract(self):
        if self.doc_type == 'pdf':
            return self._extract_pdf()
        elif self.doc_type == 'docx':
            return self._extract_docx()
        else:
            raise ValueError(f"Unsupported file type: {self.doc_type}")

    def _extract_pdf(self):
        doc = fitz.open(self.filepath)
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        lines = text.split("\n")
        paras, buffer = [], ""
        for line in lines:
            line = line.strip()
            if not line:
                if buffer:
                    paras.append(buffer.strip())
                    buffer = ""
                continue
            if line.endswith("-"):
                buffer += line[:-1]
            elif line.endswith((".", "?", "!")):
                buffer += " " + line
                paras.append(buffer.strip())
                buffer = ""
            else:
                buffer += " " + line
        if buffer:
            paras.append(buffer.strip())
        return paras

    def _extract_docx(self):
        doc = docx.Document(self.filepath)
        return [p.text.strip() for p in doc.paragraphs if p.text.strip()]
