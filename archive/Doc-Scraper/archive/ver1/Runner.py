import os
from datetime import datetime
from Extractor import TextExtractor
from Cleaner import ParagraphCleaner
from LLMClient import LLMClient
from QueryAPI import ArxivSearcher
from SemanticRanker import SemanticRanker
from CitationFormatter import CitationFormatter

# -----------------------------
# Core Paper Processing Pipeline
# -----------------------------
class PaperPipeline:
    def __init__(self, filepath, doc_type, existing_results=None):
        self.filepath = filepath
        self.doc_type = doc_type
        self.extractor = TextExtractor(filepath)
        self.llm = LLMClient()
        self.searcher = ArxivSearcher()
        self.ranker = SemanticRanker()
        self.formatter = CitationFormatter()
        self.existing_results = existing_results  # if we only want to generate citations

    def run(self, top_k=3, only_citation_styles=None):
        """
        If `existing_results` is provided, only generate citations.
        """
        if self.existing_results:
            # Only update citations
            for para_result in self.existing_results:
                for paper in para_result["papers"]:
                    paper["citations"] = {}
                    for style in only_citation_styles or ["harvard", "apa", "mla", "chicago", "ieee"]:
                        if style == "harvard":
                            paper["citations"]["harvard"] = self.formatter.harvard(paper)
                        elif style == "apa":
                            paper["citations"]["apa"] = self.formatter.apa(paper)
                        elif style == "mla":
                            paper["citations"]["mla"] = self.formatter.mla(paper)
                        elif style == "chicago":
                            paper["citations"]["chicago"] = self.formatter.chicago(paper)
                        elif style == "ieee":
                            paper["citations"]["ieee"] = self.formatter.ieee(paper)
            return self.existing_results

        # Normal pipeline
        paras = self.extractor.extract()
        cleaner = ParagraphCleaner(paras)
        cleaned_paras = cleaner.clean()
        if not cleaned_paras:
            print("No paragraphs extracted after cleaning.")
            return []

        keywords, summaries = self.llm.extract_keywords_and_summary(cleaned_paras)
        all_results = []

        for idx, para in enumerate(cleaned_paras):
            para_results = {"paragraph": para, "papers": []}
            ranked_kw = self.llm.rank_keywords(para, keywords[idx])
            query = self.searcher.build_query(ranked_kw, summaries[idx])
            papers = self.searcher.search(query)
            top_papers = self.ranker.rank(summaries[idx], papers, top_k=top_k)

            for paper in top_papers:
                paper_result = {
                    "title": paper["title"],
                    "authors": paper["authors"],
                    "year": paper["year"],
                    "link": paper["link"],
                    "relevance": paper["relevance"],
                    "citations": {}
                }
                for style in only_citation_styles or ["harvard"]:
                    if style == "harvard":
                        paper_result["citations"]["harvard"] = self.formatter.harvard(paper)
                    elif style == "apa":
                        paper_result["citations"]["apa"] = self.formatter.apa(paper)
                    elif style == "mla":
                        paper_result["citations"]["mla"] = self.formatter.mla(paper)
                    elif style == "chicago":
                        paper_result["citations"]["chicago"] = self.formatter.chicago(paper)
                    elif style == "ieee":
                        paper_result["citations"]["ieee"] = self.formatter.ieee(paper)
                para_results["papers"].append(paper_result)

            all_results.append(para_results)

        return all_results

# -----------------------------------
# Interactive Runner for User Input
# -----------------------------------
class InteractivePipelineRunner:
    def __init__(self, docs_folder="docs"):
        """
        Initializes the interactive runner.
        docs_folder: folder where input files are stored
        """
        self.docs_folder = docs_folder

    def choose_file(self):
        """Prompt user to choose a file and type (PDF or DOCX)."""
        filename = input("Enter the base filename (without extension): ").strip()
        doc_type_input = input("Select file type:\n1: PDF\n2: DOCX\nChoice: ").strip()
        doc_type = "pdf" if doc_type_input == "1" else "docx" if doc_type_input == "2" else None
        if not doc_type:
            print("Invalid selection. Exiting.")
            return None, None

        file_path = os.path.join(self.docs_folder, f"archive\Doc-Scraper\docs\{filename}.{doc_type}")
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None, None
        return file_path, doc_type

    def choose_top_k(self):
        """Prompt user to select how many top papers per paragraph to fetch."""
        try:
            k = int(input("Enter number of top papers per paragraph (default 3): ").strip() or "3")
            return max(1, k)
        except ValueError:
            print("Invalid number. Using default 3.")
            return 3

    def choose_citation_styles(self):
        """
        Allow user to choose citation styles to display.
        Default is all styles if nothing is selected.
        """
        styles = ["harvard", "apa", "mla", "chicago", "ieee"]
        print("Available citation styles:")
        for i, style in enumerate(styles, 1):
            print(f"{i}: {style.upper()}")
        selected = input("Select styles to display (comma-separated numbers, default all): ").strip()
        if not selected:
            return styles
        chosen = []
        for num in selected.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(styles):
                    chosen.append(styles[idx])
            except ValueError:
                continue
        return chosen or styles

    def run_pipeline(self):
        """Main interactive pipeline execution."""
        print("=== Scholar Athen Research Citation Pipeline ===\n")

        file_path, doc_type = self.choose_file()
        if not file_path:
            return

        top_k = self.choose_top_k()
        selected_styles = self.choose_citation_styles()

        # Initialize pipeline
        pipeline = PaperPipeline(file_path, doc_type)
        print("\nProcessing document...")
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
    runner = InteractivePipelineRunner()
    runner.run_pipeline()
