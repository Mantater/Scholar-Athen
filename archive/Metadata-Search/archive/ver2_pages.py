import arxiv
from tabulate import tabulate

# Client with custom page size
client = arxiv.Client(
    page_size=5,       # how many results per fetch
    delay_seconds=3    # polite delay
)

# Define search (no max_results here!)
search = arxiv.Search(
    query="quantum computing",
    sort_by=arxiv.SortCriterion.SubmittedDate
)

# Generator for results
results = client.results(search)

# Pagination state
buffer = []
current_index = 0

def show_page(start):
    chunk = buffer[start:start+5]
    if not chunk:
        return False

    headers = ["Title", "DOI", "Authors", "Published", "Summary", "PDF URL"]
    table = []
    for result in chunk:
        table.append([
            result.title,
            result.doi if result.doi else "N/A",   # Handle missing DOIs
            ", ".join(str(author) for author in result.authors),
            result.published.strftime("%Y-%m-%d"),
            result.summary[:200] + "..." if len(result.summary) > 200 else result.summary,
            result.pdf_url
        ])
    print(tabulate(table, headers=headers, tablefmt="fancy_grid"))
    return True

while True:
    # If we don’t have enough results in buffer → fetch more
    while len(buffer) < current_index + 5:
        try:
            buffer.append(next(results))
        except StopIteration:
            break

    # Show page
    if not show_page(current_index):
        print("No more results.")
        break

    # User navigation
    cmd = input("\nEnter command [n = next, p = previous, q = quit]: ").strip().lower()
    if cmd == "n":
        current_index += 5
    elif cmd == "p" and current_index >= 5:
        current_index -= 5
    elif cmd == "q":
        break
    else:
        print("Invalid command.")
