import fitz  # PyMuPDF
import docx  # python-docx
import spacy
import re
import os


# -----------------------------
# Text Extraction
# -----------------------------
def extract_pdf_text(pdf_path):
    """
    Extracts text paragraphs from a PDF file.

    Parameters:
        pdf_path (str): Path to the PDF file.

    Returns:
        list[str]: A list of reconstructed paragraphs as strings.
    """
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"

    # Split into lines
    lines = text.split("\n")
    paragraphs = []
    buffer = ""

    for line in lines:
        line = line.strip()
        if not line:
            if buffer:  # flush paragraph
                paragraphs.append(buffer.strip())
                buffer = ""
            continue

        # Handle hyphenated words
        if line.endswith("-"):
            buffer += line[:-1]
        elif line.endswith((".", "?", "!")):
            buffer += " " + line
            paragraphs.append(buffer.strip())
            buffer = ""
        else:
            buffer += " " + line

    if buffer:
        paragraphs.append(buffer.strip())

    return paragraphs

def extract_docx_text(docx_path):
    """
    Extracts text paragraphs from a DOCX file.
    
    Parameters:
        docx_path (str): Path to the DOCX file.
    
    Returns:
        list[str]: A list of non-empty paragraphs as strings.
    """
    doc = docx.Document(docx_path)  # Open the DOCX file
    
    # Collect each paragraph's text, strip leading/trailing spaces,
    # and skip empty paragraphs (so no blank lines are included).
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

# -----------------------------
# Paragraph handeling
# -----------------------------
def para_processing(filename, doc_type):
    """
    Extracts, cleans, and filters paragraphs from a file.

    Parameters:
        filename (str): Base name of the file (without extension).
        doc_type (str): File type to process ("pdf" or "docx").

    Returns:
        list[str]: Cleaned paragraphs from the file.
    """
    cleaned_paras = []
    file = f"archive\Doc-Scraper\docs\{filename}.{doc_type}"

    if not os.path.exists(file):
        print(f"{doc_type.upper()} file not found: {file}")
        return []

    print(f"\nExtracting from {doc_type.upper()}: {file}\n")

    # Select extraction method
    if doc_type == "pdf":
        file_paras = extract_pdf_text(file)
    elif doc_type == "docx":
        file_paras = extract_docx_text(file)
    else:
        raise ValueError(f"Unsupported file type: {doc_type}")

    # Clean and filter
    for i, para in enumerate(file_paras, 1):
        cleaned_text = clean_paragraph_spacy(para)
        if cleaned_text:
            cleaned_paras.append(cleaned_text)

    print(f"\nCleaned: {len(cleaned_paras)} / {len(file_paras)}\n")
    return cleaned_paras

# -----------------------------
# Cleaning data
# -----------------------------

# Load small English model
nlp = spacy.load("en_core_web_sm")

def clean_paragraph_spacy(text, min_words=10, remove_short=True):
    """
    Cleans a paragraph using spaCy:
    - Removes extra spaces, line breaks, HTML tags
    - Splits into sentences using spaCy
    - Optionally removes very short sentences
    
    Parameters:
        text (str): Input paragraph
        min_words (int): Minimum words to keep a sentence
        remove_short (bool): Whether to remove very short sentences

    Returns:
        str: Cleaned paragraph
    """
    # 1. Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # 2. Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 3. Use spaCy to split into sentences
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents]
    
    # 4. Optionally filter very short sentences
    if remove_short:
        sentences = [s for s in sentences if len(s.split()) >= min_words]
    
    # 5. Join back into a single paragraph
    return ' '.join(sentences)

# -----------------------------
# Main
# -----------------------------
def main():
    filename = "EJ1172284"
    select = int(input("Select file type to extract (1: PDF, 2: DOCX): "))

    # --- Handle PDF ---
    if select == 1:
        para_processing(filename, "pdf")
        
    # --- Handle DOCX ---
    elif select == 2:
        para_processing(filename, "docx")

if __name__ == "__main__":
    main()
