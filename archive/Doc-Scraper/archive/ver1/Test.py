import os
from Runner import PaperPipeline
from CitationFormatter import CitationFormatter

def main():
    print("=== Scholar Athen Research Citation Pipeline ===\n")

    # Ask for file input
    filename = input("Enter the base filename (without extension): ").strip()
    doc_type_input = input("Select file type (1: PDF, 2: DOCX): ").strip()
    
    if doc_type_input == "1":
        doc_type = "pdf"
    elif doc_type_input == "2":
        doc_type = "docx"
    else:
        print("Invalid selection. Exiting.")
        return

    file_path = os.path.join("docs", f"archive\Doc-Scraper\docs\{filename}.{doc_type}")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Ask for number of top papers per paragraph
    try:
        top_k = int(input("Enter number of top papers per paragraph (default 3): ").strip() or "3")
        top_k = max(1, top_k)
    except ValueError:
        top_k = 3

    # Ask for citation styles
    styles = ["harvard", "apa", "mla", "chicago", "ieee"]
    print("Available citation styles:")
    for i, style in enumerate(styles, 1):
        print(f"{i}: {style.upper()}")
    selected_styles_input = input("Select styles to display (comma-separated numbers, default all): ").strip()
    
    if selected_styles_input:
        selected_styles = []
        for num in selected_styles_input.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(styles):
                    selected_styles.append(styles[idx])
            except ValueError:
                continue
        if not selected_styles:
            selected_styles = styles
    else:
        selected_styles = styles

    # Output what the user chose
    print("\n=== Your Selections ===")
    print(f"File: {file_path}")
    print(f"Top papers per paragraph: {top_k}")
    print(f"Citation styles: {', '.join([s.upper() for s in selected_styles])}")
    print("=======================\n")

    # Initialize pipeline
    pipeline = PaperPipeline(file_path, doc_type)
    
    print("Processing document...")
    results = pipeline.run(top_k=top_k)

    if not results:
        print("No results found or document could not be processed.")
        return

    # Display results
    for idx, para_result in enumerate(results, 1):
        print(f"\n--- Paragraph {idx} ---")
        print("Original Text:", para_result['paragraph'][:200], "...\n")  # truncated for display

        for i, paper in enumerate(para_result['papers'], 1):
            print(f"Paper {i}:")
            print("Title:", paper['title'])
            print("Authors:", ", ".join(paper['authors']))
            print("Year:", paper['year'])
            print("Relevance: {:.2f}%".format(paper['relevance']))
            if "harvard" in selected_styles:
                print("Harvard:", CitationFormatter.harvard(paper))
            if "apa" in selected_styles:
                print("APA:", CitationFormatter.apa(paper))
            if "mla" in selected_styles:
                print("MLA:", CitationFormatter.mla(paper))
            if "chicago" in selected_styles:
                print("Chicago:", CitationFormatter.chicago(paper))
            if "ieee" in selected_styles:
                print("IEEE:", CitationFormatter.ieee(paper, number=i))
            print("Link:", paper['link'])
            print("-" * 60)


if __name__ == "__main__":
    main()
