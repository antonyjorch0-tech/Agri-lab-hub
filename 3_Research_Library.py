from urllib.parse import quote_plus

import requests
import streamlit as st

from utils.ui import hero, note, setup

setup("Research Library")
hero("Research Library", "Search published research, then open the paper or find a free copy.")

HEADERS = {"User-Agent": "AgriLabHub/1.0 (student research tool)"}


def _openalex_key():
    try:
        return st.secrets.get("OPENALEX_API_KEY")
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def search_openalex(query, n, oa_only, from_year, key=None):
    filters = []
    if oa_only:
        filters.append("is_oa:true")
    if from_year:
        filters.append(f"from_publication_date:{from_year}-01-01")
    params = {"search": query, "per-page": n}
    if filters:
        params["filter"] = ",".join(filters)
    if key:
        params["api_key"] = key
    r = requests.get("https://api.openalex.org/works", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        names = [a["author"]["display_name"] for a in w.get("authorships", []) if a.get("author")]
        src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        out.append({"title": w.get("title") or w.get("display_name") or "Untitled", "year": w.get("publication_year"),
                    "authors": ", ".join(names[:3]) + (" et al." if len(names) > 3 else ""), "venue": src,
                    "cited": w.get("cited_by_count"), "oa_url": (w.get("open_access") or {}).get("oa_url"),
                    "link": w.get("doi") or w.get("id")})
    return out


@st.cache_data(ttl=3600, show_spinner=False)
def search_crossref(query, n, from_year):
    params = {"query": query, "rows": n,
              "select": "title,author,issued,container-title,DOI,URL,is-referenced-by-count"}
    if from_year:
        params["filter"] = f"from-pub-date:{from_year}"
    r = requests.get("https://api.crossref.org/works", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    out = []
    for w in r.json().get("message", {}).get("items", []):
        names = [f"{a.get('given', '')} {a.get('family', '')}".strip() for a in w.get("author", [])]
        parts = (w.get("issued", {}).get("date-parts") or [[None]])[0]
        out.append({"title": (w.get("title") or ["Untitled"])[0], "year": parts[0] if parts else None,
                    "authors": ", ".join(names[:3]) + (" et al." if len(names) > 3 else ""),
                    "venue": (w.get("container-title") or [None])[0], "cited": w.get("is-referenced-by-count"),
                    "oa_url": None, "link": f"https://doi.org/{w['DOI']}" if w.get("DOI") else w.get("URL")})
    return out


query = st.text_input("What are you researching?", placeholder="For example machine learning rubber yield forecasting Sri Lanka")
tab_search, tab_sites = st.tabs(["Search papers", "Other sources"])

with tab_search:
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    source = c1.radio("Database", ["OpenAlex", "Crossref"], horizontal=True)
    n = c2.slider("Results", 5, 25, 10)
    from_year = c3.number_input("From year (0 = any)", 0, 2026, 0)
    oa_only = c4.checkbox("Open access only", disabled=(source == "Crossref"))
    if st.button("Search", type="primary", disabled=not query.strip()):
        try:
            with st.spinner(f"Searching {source}..."):
                if source == "OpenAlex":
                    st.session_state["lib_results"] = search_openalex(query.strip(), n, oa_only, int(from_year) or None, _openalex_key())
                else:
                    st.session_state["lib_results"] = search_crossref(query.strip(), n, int(from_year) or None)
        except requests.HTTPError as e:
            st.session_state.pop("lib_results", None)
            st.error(f"{source} returned an error ({e.response.status_code}). Try again shortly, or use the Other sources tab.")
        except requests.RequestException:
            st.session_state.pop("lib_results", None)
            st.error(f"Could not reach {source}. Check your connection or use the Other sources tab.")
    results = st.session_state.get("lib_results")
    if results is not None:
        if not results:
            st.info("No papers found. Try fewer or broader keywords.")
        for r in results:
            title = r["title"].replace("[", "(").replace("]", ")")
            with st.container(border=True):
                st.markdown(f"**[{title}]({r['link']})**" if r["link"] else f"**{title}**")
                meta = [x for x in (r["authors"], r["venue"], str(r["year"]) if r["year"] else None,
                                    f"Cited {r['cited']} times" if r["cited"] is not None else None) if x]
                st.caption(" | ".join(meta))
                if r["oa_url"]:
                    st.markdown(f"[Free full text]({r['oa_url']})")
        if results:
            note("Whether you can read the full text depends on the publisher and the authors. "
                 "Use the free full text link when it appears, or request a copy from the authors.")

with tab_sites:
    if not query.strip():
        st.info("Type your topic above and these buttons will open the search on each site.")
    q = quote_plus(query.strip())
    sites = [("Google Scholar", f"https://scholar.google.com/scholar?q={q}", "Articles, theses, books and citations"),
             ("ResearchGate", f"https://www.researchgate.net/search?q={q}", "Researchers and requests for full text"),
             ("Semantic Scholar", f"https://www.semanticscholar.org/search?q={q}", "AI-assisted paper discovery"),
             ("CORE", f"https://core.ac.uk/search?q={q}", "Open-access papers from repositories"),
             ("PubMed", f"https://pubmed.ncbi.nlm.nih.gov/?term={q}", "Biomedical and life-science literature"),
             ("DOAJ", "https://doaj.org/", "Open-access journals and articles")]
    for i in range(0, len(sites), 3):
        cols = st.columns(3)
        for col, (name, url, desc) in zip(cols, sites[i:i + 3]):
            with col:
                st.markdown(f"**{name}**")
                st.caption(desc)
                st.link_button(f"Open {name}", url)
