import arxiv
import streamlit as st

# --- Page Config ---
st.set_page_config(
    page_title="Scholar Athen",
    page_icon="🏛️",
    layout="wide",
)

# --- Custom CSS ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Georgia', 'Times New Roman', serif;
    }

    /* Title before search */
    .main-title {
        font-size: 40px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Header bar */
    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1E3A8A;
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    .header-bar h1 {
        margin: 0;
        font-size: 28px;
        font-weight: bold;
    }

    /* Paper card */
    .paper {
        background-color: #f9f9f9;
        border-left: 4px solid #1E3A8A;
        padding: 15px;
        margin: 12px 0;
        border-radius: 6px;
    }
    .paper h3 {
        margin: 0 0 5px 0;
        font-size: 20px;
        color: #1E3A8A;
    }
    .paper .authors {
        font-style: italic;
        font-size: 14px;
        margin-bottom: 4px;
        color: black;
    }
    .paper .date {
        font-size: 13px;
        color: gray;
        margin-bottom: 8px;
    }
    .paper a {
        color: #2563EB;
        text-decoration: none;
        font-weight: bold;
    }

    /* Pagination */
    .pagination {
        text-align: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)


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


# --- Search State ---
if "page" not in st.session_state:
    st.session_state.page = 0

query = st.text_input("Enter your search term:")

if not query:
    # --- Before search ---
    st.markdown("<div class='main-title'>Scholar Athen</div>", unsafe_allow_html=True)
    st.write("Enter a keyword above to search for research papers.")
else:
    # --- After search header (title + search bar) ---
    left, right = st.columns([3,2])
    with left:
        st.markdown("<div class='header-bar'><h1>Scholar Athen</h1></div>", unsafe_allow_html=True)
    with right:
        query = st.text_input("Search again:", value=query)

    # --- Results ---
    results = fetch_results(query, max_results=200)
    total = len(results)
    page_size = 15

    start = st.session_state.page * page_size
    end = start + page_size
    current_papers = results[start:end]

    for i, r in enumerate(current_papers, start=start + 1):
        st.markdown(f"""
        <div class="paper">
            <h3>{i}. {r.title}</h3>
            <div class="authors">{", ".join(a.name for a in r.authors)}</div>
            <div class="date">Published: {r.published.strftime("%Y-%m-%d")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Short + expandable summary
        short_summary = r.summary[:300] + ("..." if len(r.summary) > 300 else "")
        with st.expander(f"🔎 Summary (click to expand)"):
            st.write(r.summary)

        st.markdown(f"[📄 Read PDF]({r.pdf_url})")

    # --- Pagination ---
    st.markdown("<div class='pagination'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if st.button("⬅️ Previous") and st.session_state.page > 0:
            st.session_state.page -= 1
    with col3:
        if st.button("Next ➡️") and end < total:
            st.session_state.page += 1
    with col2:
        st.write(f"Page {st.session_state.page+1} of {(total-1)//page_size + 1}")
    st.markdown("</div>", unsafe_allow_html=True)
