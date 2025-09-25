from datetime import datetime

class CitationFormatter:
    
    @staticmethod
    def harvard(paper):
        """Harvard style citation"""
        authors_str = CitationFormatter._format_authors(paper.get('authors', []))
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'No title')
        link = paper.get('link', '')
        accessed = datetime.now().strftime("%d %b %Y")
        return f"{authors_str} ({year}) '{title}', arXiv. Available at: {link} (Accessed: {accessed})."

    @staticmethod
    def apa(paper):
        """APA style citation"""
        authors_str = CitationFormatter._format_authors_apa(paper.get('authors', []))
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'No title')
        link = paper.get('link', '')
        return f"{authors_str} ({year}). {title}. arXiv. {link}"

    @staticmethod
    def mla(paper):
        """MLA style citation"""
        authors_str = CitationFormatter._format_authors_mla(paper.get('authors', []))
        title = paper.get('title', 'No title')
        year = paper.get('year', 'n.d.')
        link = paper.get('link', '')
        accessed = datetime.now().strftime("%d %b %Y")
        return f"{authors_str}. \"{title}.\" arXiv, {year}. Web. Accessed {accessed}. {link}."

    @staticmethod
    def chicago(paper):
        """Chicago style citation"""
        authors_str = CitationFormatter._format_authors(paper.get('authors', []))
        title = paper.get('title', 'No title')
        year = paper.get('year', 'n.d.')
        link = paper.get('link', '')
        accessed = datetime.now().strftime("%B %d, %Y")
        return f"{authors_str}. \"{title}.\" arXiv, {year}. Accessed {accessed}. {link}."

    @staticmethod
    def ieee(paper, number=1):
        """IEEE style citation"""
        authors_list = paper.get('authors', [])
        authors_str = ', '.join([a.split()[-1] + ' ' + a.split()[0][0] + '.' for a in authors_list])
        title = paper.get('title', 'No title')
        year = paper.get('year', 'n.d.')
        link = paper.get('link', '')
        return f"[{number}] {authors_str}, \"{title},\" arXiv, {year}. {link}"
    
    @staticmethod
    def bibtex(paper):
        """BibTeX entry"""
        authors_str = ' and '.join(paper.get('authors', []))
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'No title')
        link = paper.get('link', '')
        citation_key = ''.join(e for e in title if e.isalnum())[:20] + year  # Simple key
        return f"@misc{{{citation_key},\n  author = {{{authors_str}}},\n  title = {{{title}}},\n  year = {{{year}}},\n  howpublished = {{arXiv}},\n  note = {{Available at: {link}}}\n}}"

    # -----------------------
    # Helper functions
    # -----------------------
    @staticmethod
    def format(paper, style="harvard"):
        """
        Returns citation text in the given style.
        Defaults to Harvard if style is invalid.
        """
        if style in ["harvard", "apa", "mla", "chicago", "bibtex"]:
            return getattr(CitationFormatter, style)(paper)
        return CitationFormatter.harvard(paper)
    
    @staticmethod
    def _format_authors(authors_list):
        n = len(authors_list)
        if n == 0:
            return ""
        elif n == 1:
            a = authors_list[0].split()
            return f"{a[-1]}, {a[0][0]}."
        elif n == 2:
            a1, a2 = [a.split() for a in authors_list[:2]]
            return f"{a1[-1]}, {a1[0][0]}. and {a2[-1]}, {a2[0][0]}."
        elif n == 3:
            a1, a2, a3 = [a.split() for a in authors_list[:3]]
            return f"{a1[-1]}, {a1[0][0]}., {a2[-1]}, {a2[0][0]} and {a3[-1]}, {a3[0][0]}."
        else:
            a1 = authors_list[0].split()
            return f"{a1[-1]}, {a1[0][0]}. et al."

    @staticmethod
    def _format_authors_apa(authors_list):
        """APA: Lastname, F. M., & Lastname, F. M."""
        if not authors_list:
            return ""
        formatted = []
        for a in authors_list[:7]:  # APA lists max 7 authors, et al. if more
            parts = a.split()
            formatted.append(f"{parts[-1]}, {' '.join([p[0]+'.' for p in parts[:-1]])}")
        if len(authors_list) > 7:
            formatted.append("et al.")
        return ', & '.join(formatted)

    @staticmethod
    def _format_authors_mla(authors_list):
        """MLA: Lastname, Firstname"""
        if not authors_list:
            return ""
        formatted = []
        for a in authors_list:
            parts = a.split()
            formatted.append(f"{parts[-1]}, {' '.join(parts[:-1])}")
        return ', '.join(formatted)
