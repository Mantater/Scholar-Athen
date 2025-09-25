import arxiv
import tabulate

# Construct the default API client
client = arxiv.Client()

search = arxiv.Search(
    query="quantum computing",
    max_results=5,
)

results = client.results(search)

headers = ["Title", "DOI", "Authors", "Published", "Summary", "PDF URL"]
table = []

for result in results:
    table.append([
        result.title,
        result.doi if result.doi else "N/A",  # ✅ DOI when available
        ", ".join(str(author) for author in result.authors),
        result.published.strftime("%Y-%m-%d"),
        result.summary[:200] + "..." if len(result.summary) > 200 else result.summary,  # shorten
        result.pdf_url
    ])

print(tabulate.tabulate(table, headers=headers))
