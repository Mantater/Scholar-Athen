from django.shortcuts import render
import arxiv
import math

def fetch_results(query, max_results=200):
    client = arxiv.Client(page_size=50, delay_seconds=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    return list(client.results(search))

def index(request):
    query = request.GET.get('query', '').strip()
    page_size = 15
    page = request.GET.get('page', 1)

    try:
        page = int(page)
        if page < 1:
            page = 1
    except ValueError:
        page = 1

    papers = []
    total = 0

    if query:
        results = fetch_results(query)
        total = len(results)
        max_page = max(1, math.ceil(total / page_size))

        # Clamp page to max_page
        if page > max_page:
            page = max_page

        start_index = (page - 1) * page_size
        page_results = results[start_index:start_index + page_size]

        papers = [{
            'title': r.title,
            'authors': [a.name for a in r.authors],
            'published': r.published.strftime("%Y-%m-%d"),
            'doi': r.doi,
            'summary': r.summary,
            'pdf_url': r.pdf_url,
        } for r in page_results]
    else:
        start_index = 0
        max_page = 1  # no results yet

    context = {
        'query': query,
        'papers': papers,
        'page': page,
        'page_size': page_size,
        'total': total,
        'start_index': start_index,
        'max_page': max_page,
    }

    return render(request, 'search/index.html', context)
