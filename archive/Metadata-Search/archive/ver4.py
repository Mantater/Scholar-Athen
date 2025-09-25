import arxiv
import streamlit as st
import pandas as pd

# --- Page Config ---
st.set_page_config(
    page_title="Scholar Athen",
    page_icon="🏛️",
    layout="wide",
)

# --- Custom CSS Styling ---
st.markdown("""
<style>
    /* Global font + spacing */
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', sans-serif;
    }

    /* Title box */
    .title-box {
        background: linear-gradient(90deg, #4CAF50 0%, #2E7D32 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
    }

    /* Search bar section */
    .search-box {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }

    /* Dataframe table tweaks */
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 10px;
    }

    /* Pagination bar */
    .pagination {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)


# --- Title ---
st.markdown("<div class='title-box'><h1>Scholar Athen</h1><p>Explore the world of STEM research</p></div>", unsafe_allow_html=True)

# --- Search Box ---
st.markdown("<div class='search-box'>", unsafe_allow_html=True)
query = st.text_input("🔎 Enter your search term:")
page_size = st.number_input("Results per page:", 5, 50, 10, step=5)
st.markdown("</div>", unsafe_allow_html=True)


# --- Fetch results ---
@st.cache_data
def fetch_results(query, max_results=200):
    client = arxiv.Client(page_size=50, delay_seconds=3)
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    return list(client.results(search))


if query:
    results = fetch_results(query, max_results=200)
    total = len(results)

    # --- Pagination state ---
    if "page" not in st.session_state:
        st.session_state.page = 0

    start = st.session_state.page * page_size
    end = start + page_size
    current_papers = results[start:end]

    # --- Convert to DataFrame ---
    df = pd.DataFrame([{
        "No.": i + 1 + start,
        "Title": r.title,
        "Authors": ", ".join(a.name for a in r.authors),
        "Published": r.published.strftime("%Y-%m-%d"),
        "Summary": r.summary[:300] + "...",  # shorten for readability
        "PDF": r.pdf_url
    } for i, r in enumerate(current_papers)])

    st.dataframe(df, use_container_width=True)

    # --- Pagination Bar ---
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)

    nav_left, nav_right = st.columns([3,1])
    with nav_left:
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("⬅️ Previous") and st.session_state.page > 0:
                st.session_state.page -= 1
        with col2:
            if st.button("Next ➡️") and end < total:
                st.session_state.page += 1

    with nav_right:
        st.markdown(
            f"<p><b>Page {st.session_state.page+1} of {(total-1)//page_size + 1}</b></p>",
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)
