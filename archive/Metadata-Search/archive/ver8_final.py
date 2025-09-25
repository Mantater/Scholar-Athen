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
  .doi { font-size:13px; color:grey ; margin-bottom:8px;}
  .summary { font-size:15px; margin-bottom:8px; color: black; }
  .pdf a { color:#2563EB; text-decoration:none; font-weight:600; }
  
  /* Align button and input height */
  div.stTextInput>div>input { height:36px; font-size:16px; }
  div.stButton>button { height:36px; font-size:16px; margin-top:0px; }
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
    # Blue header band
    st.markdown(
        """
        <div style="
            background:#1E3A8A;
            padding:16px;
            border-radius:10px;
            margin-bottom:20px;
            text-align:center;
        ">
            <h1 style='color:white; margin:0; font-size:35px;'>Scholar Athen</h1>
        </div>
        """, unsafe_allow_html=True
    )

    # Centered search bar with button on the right - FIXED VERSION
    with st.form("landing_search", clear_on_submit=False):
        input_col, button_col = st.columns([7,1])
        with input_col:
            q = st.text_input(
            "Search for papers",  # non-empty label
            placeholder="e.g. quantum computing, graph neural networks",
            label_visibility="collapsed"
            )
        with button_col:
            # Add some spacing to align the button properly
            st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Search")
        
        if submitted:
            st.session_state.query = (q or "").strip()
            st.session_state.page = 0
            st.rerun()

    st.markdown(
        "<div style='text-align:center; color:grey ; margin-top:12px;'>Type a query and press <b>Search</b> to begin.</div>",
        unsafe_allow_html=True
    )

# ---------- AFTER SEARCH ----------
else:
    # Blue header band
    st.markdown(
        """
        <div style="
            background:#1E3A8A;
            padding:16px;
            border-radius:10px;
            margin-bottom:20px;
            text-align:center;
        ">
            <h1 style='color:white; margin:0; font-size:35px;'>Scholar Athen</h1>
        </div>
        """, unsafe_allow_html=True
    )

    # Centered search bar with button on the right (same as before search)
    with st.form("header_search", clear_on_submit=False):
        input_col, button_col = st.columns([7,1])
        with input_col:
            q2 = st.text_input(
            "Refine search",  # non-empty label
            value=st.session_state.query,
            placeholder="Refine search…",
            label_visibility="collapsed"
            )
        with button_col:
            # Small div to help vertical alignment
            st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)
            resubmit = st.form_submit_button("Search")
        
        if resubmit:
            st.session_state.query = (q2 or "").strip()
            st.session_state.page = 0
            st.rerun()

    # Fetch results
    results = fetch_results(st.session_state.query, max_results=200)
    total = len(results)
    page_size = 15

    # Pagination
    start = st.session_state.page * page_size
    end = start + page_size
    current_papers = results[start:end]

    # Render each paper as a card
    for i, r in enumerate(current_papers, start=start + 1):
        doi_text = f"(DOI: {r.doi})" if r.doi else ""
        st.markdown(f"""
            <div class="paper">
                <h3>{i}. {r.title}</h3>
                <div class="authors">{', '.join(a.name for a in r.authors)}</div>
                <div class="date">Published: {r.published.strftime('%Y-%m-%d')}</div>
                <div class="doi">{doi_text}</div>
                <div class="summary">{r.summary[:500]}...</div>
                <div class="pdf"><a href="{r.pdf_url}" target="_blank">📄 Read PDF</a></div>
            </div>
        """, unsafe_allow_html=True)

    # Bottom-center pagination
    spacer_l, center, spacer_r = st.columns([2,3,2])
    with center:
        prev_col, page_col, next_col = st.columns([1,2,1])
        with prev_col:
            if st.button("&#x276E;", key="prev"):  # Unicode left arrow
                st.session_state.page -= 1
                st.rerun()
        with page_col:
            st.markdown(
                f"<div style='text-align:center;font-weight:600;'>Page {st.session_state.page+1} of {(total-1)//page_size +1}</div>",
                unsafe_allow_html=True
            )
        with next_col:
            if st.button("&#x276F;", key="next"):  # Unicode right arrow
                st.session_state.page += 1
                st.rerun()
