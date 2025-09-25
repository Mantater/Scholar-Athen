import fitz  # PyMuPDF
import docx  # python-docx
import os

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

def main():
    filename = "EJ1172284"
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