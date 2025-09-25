import fitz  # PyMuPDF for PDF text extraction
import docx  # python-docx for DOCX text extraction
import os

def extract_pdf_text(pdf_path):
    """
    Extracts text from a PDF file and returns a list of paragraphs.
    - Uses PyMuPDF (fitz).
    - Splits text by double newlines (\n\n), which often indicate paragraph breaks.
    - Strips empty whitespace so only real content remains.
    """
    doc = fitz.open(pdf_path)
    paragraphs = []
    for page in doc:
        # Extract page text as plain text
        text = page.get_text("text")
        # Split by double newlines → approximate paragraphs
        page_paras = [para.strip() for para in text.split("\n\n") if para.strip()]
        paragraphs.extend(page_paras)
    return paragraphs

def extract_docx_text(docx_path):
    """
    Extracts text from a DOCX file and returns a list of paragraphs.
    - python-docx preserves actual paragraph structure.
    - Strips out empty/whitespace-only paragraphs.
    """
    doc = docx.Document(docx_path)
    return [para.text.strip() for para in doc.paragraphs if para.text.strip()]

def main():
    """
    Main program entry point.
    - Asks user to select file type (PDF or DOCX).
    - Builds filename (default: EJ1172284).
    - Extracts paragraphs and prints them, numbered.
    """
    filename = "EJ1172284"  # Base name (without extension)
    select = int(input("Select file type to extract (1: PDF, 2: DOCX): "))

    sum = 0

    # --- Handle PDF ---
    if select == 1:
        pdf_file = f"archive\Doc-Scraper\docs\{filename}.pdf"
        if os.path.exists(pdf_file):
            print(f"\nExtracting from PDF: {pdf_file}\n")
            pdf_paras = extract_pdf_text(pdf_file)
            # Print each paragraph with numbering
            for i, para in enumerate(pdf_paras, 1):
                print(f"Paragraph {i}:\n{para}\n")

            sum = len(pdf_paras)
            print(f"Total paragraphs extracted: {sum}\n")
        else:
            print(f"PDF file not found: {pdf_file}")

    # --- Handle DOCX ---
    elif select == 2:
        docx_file = f"archive\Doc-Scraper\docs\{filename}.docx"
        if os.path.exists(docx_file):
            print(f"\nExtracting from DOCX: {docx_file}\n")
            docx_paras = extract_docx_text(docx_file)
            # Print each paragraph with numbering
            for i, para in enumerate(docx_paras, 1):
                print(f"Paragraph {i}:\n{para}\n")

            sum = len(docx_paras)
            print(f"Total paragraphs extracted: {sum}\n")
        else:
            print(f"DOCX file not found: {docx_file}")

if __name__ == "__main__":
    main()
