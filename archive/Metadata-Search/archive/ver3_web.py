import arxiv
import streamlit as st
import pandas as pd

st.title("Scholar Athen - STEM Research Paper Search")
query = st.text_input("Enter your search term:")

@st.cache_data
def fetch_results(query, max_results=100):
    client = arxiv.Client(page_size=50, delay_seconds=3)
    search = arxiv.Search(query=query, max_results=max_results,
                          sort_by=arxiv.SortCriterion.SubmittedDate)
    return list(client.results(search))

if query:
    results = fetch_results(query, max_results=100)
    total = len(results)

    page_size = st.number_input("Results per page:", 5, 50, 10, step=5)
    if "page" not in st.session_state:
        st.session_state.page = 0

    start = st.session_state.page * page_size
    end = start + page_size
    current_papers = results[start:end]

    # --- Build DataFrame with DOI ---
    df = pd.DataFrame([{
        "No.": i + 1 + start,
        "Title": r.title,
        "DOI": r.doi if r.doi else "N/A",   # <- added DOI
        "Authors": ", ".join(a.name for a in r.authors),
        "Published": r.published.strftime("%Y-%m-%d"),
        "Summary": r.summary,
        "PDF": r.pdf_url
    } for i, r in enumerate(current_papers)])

    st.dataframe(df, use_container_width=True)

    # --- Navigation bar ---
    nav_left, nav_right = st.columns([3,1])

    with nav_left:
        prev_clicked, next_clicked = st.columns([1,1])
        with prev_clicked:
            if st.button("⬅️ Previous"):
                if st.session_state.page > 0:
                    st.session_state.page -= 1
        with next_clicked:
            if st.button("Next ➡️"):
                if (st.session_state.page + 1) * page_size < total:
                    st.session_state.page += 1

    with nav_right:
        st.markdown(
            f"<div style='text-align:right; font-weight:bold;'>Page {st.session_state.page+1} of {(total-1)//page_size + 1}</div>",
            unsafe_allow_html=True
        )
