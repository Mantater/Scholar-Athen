import arxiv
import streamlit as st

# ---------- Page config ----------
st.set_page_config(page_title="Scholar Athen", page_icon="🏛️", layout="wide")

# ---------- Styles ----------
st.markdown("""
<style>
  html, body, [class*="css"] { font-family: 'Georgia','Times New Roman',serif; }

  .main-title { font-size: 40px; font-weight: 700; text-align: center; margin: 8px 0 18px; }
  .hint { text-align:center; color:#666; margin-bottom: 24px; }

  /* Blue header band (after search) */
  .header-band {
    background:#1E3A8A; color:#fff;
    padding:12px 18px; border-radius:10px; margin-bottom:20px;
  }
  .header-title { font-size:26px; font-weight:700; margin:0; }

  /* Paper card */
  .paper {
    background:#f9f9f9;
    border-left:4px solid #1E3A8A;
    padding:14px;
    margin:12px 0;
    border-radius:8px;
  }
  .paper h3 { margin:0 0 6px 0; font-size:20px; color:#1E3A8A; }
  .authors { font-style:italic; font-size:14px; margin-bottom:4px; color: black;}
  .date { font-size:13px; color:grey ; margin-bottom:8px;}
  .summary { font-size:15px; margin-bottom:8px; color: black; }
  .pdf a { color:#2563EB; text-decoration:none; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ---------- Data fetch ----------
@st.cache_data
def fetch_results(query, max_results=200):
    client = arxiv.Client(page_size=50, delay_seconds=3)
    search = arxiv.Search(query=query, max_results=max_results,
                          sort_by=arxiv.SortCriterion.SubmittedDate)
    return list(client.results(search))

# ---------- State ----------
if "query" not in st.session_state: st.session_state.query = ""
if "page" not in st.session_state:  st.session_state.page = 0

# ---------- BEFORE SEARCH ----------
if not st.session_state.query:
    st.markdown("<div class='main-title'>Scholar Athen</div>", unsafe_allow_html=True)
    with st.form("landing_search"):
        q = st.text_input("Search research papers", placeholder="e.g. quantum computing, graph neural networks")
        submitted = st.form_submit_button("Search")
        if submitted:
            st.session_state.query = (q or "").strip()
            st.session_state.page = 0
            st.rerun()
    st.markdown("<div class='hint'>Type a query and press <b>Search</b> to begin.</div>", unsafe_allow_html=True)

# ---------- AFTER SEARCH ----------
else:
    # Blue header band containing title (left) and search bar (right)
    with st.container():
        st.markdown("<div class='header-band'>", unsafe_allow_html=True)
        col1, col2 = st.columns([3,2])
        with col1:
            st.markdown("<p class='header-title'>Scholar Athen</p>", unsafe_allow_html=True)
        with col2:
            with st.form("header_search", clear_on_submit=False):
                q2 = st.text_input("Search", value=st.session_state.query,
                                   label_visibility="collapsed",
                                   placeholder="Refine search…")
                resubmit = st.form_submit_button("Search")
            if resubmit:
                st.session_state.query = (q2 or "").strip()
                st.session_state.page = 0
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Fetch & paginate (fixed 15 per page)
    results = fetch_results(st.session_state.query, max_results=200)
    total = len(results)
    page_size = 15

    max_page = (max(total - 1, 0)) // page_size
    st.session_state.page = min(max(st.session_state.page, 0), max_page)

    start = st.session_state.page * page_size
    end = start + page_size
    current_papers = results[start:end]

    # Render papers as cards (everything inside the card)
    # --- Display papers like feed ---
    for i, r in enumerate(current_papers, start=start + 1):
        st.markdown(f"""
        <div class="paper">
            <h3>{i}. {r.title}</h3>
            <div class="authors">{", ".join(a.name for a in r.authors)}</div>
            <div class="date">Published: {r.published.strftime("%Y-%m-%d")}</div>
            <div class="summary">{r.summary[:500]}...</div>
            <a href="{r.pdf_url}" target="_blank">📄 Read PDF</a>
        </div>
        """, unsafe_allow_html=True)

    # Bottom-center pagination
    spacer_l, center, spacer_r = st.columns([2,3,2])
    with center:
        c1, c2, c3 = st.columns([1,1,1])
        with c1:
            if st.button("⬅️ Previous", disabled=(st.session_state.page <= 0)):
                st.session_state.page -= 1
                st.rerun()
        with c3:
            if st.button("Next ➡️", disabled=(st.session_state.page >= max_page)):
                st.session_state.page += 1
                st.rerun()
        with c2:
            st.markdown(f"<div style='text-align:center;font-weight:600;'>Page {st.session_state.page+1} of {max_page+1}</div>", unsafe_allow_html=True)
