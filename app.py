"""Interactive companion to "A Conceptual Review of the Cross-National Accounting Literature".

Five views, chosen in the sidebar:
  1. Full network        - all 575 concepts and 683 relationships, colored by category or research stream
  2. Concept search      - ego network and relationship table for any concept matching a search term
  3. Category map        - the 16-category collapsed network (interactive Figure 6) with a threshold slider
  4. Discipline network  - the Political Science sub-network (interactive Figure 8), aggregated or individual
  5. Study lookup        - every sampled article testing a relationship whose concepts match a word or phrase
  6. All 262 studies     - the full reference list, APA style, searchable

Data files live in ./data and are produced by the accompanying notebook from the master coding file.
Network drawings use pyvis (vis.js) with the same conventions as the manuscript figures.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import networkx as nx
from pyvis.network import Network
import re
import textwrap

# ------------------------------------------------------------------ constants
ORANGE, BLUE_NODE, BLUE_EDGE, GREY = "#F5A623", "#AED6F1", "#5DADE2", "#7A7A7A"
EXT = ["Political Science", "Economics", "Sociology", "Psychology", "Communication"]
CAT_COLORS = {"Financial Reporting & Disclosure": "#1f77b4", "Tax & Financial Planning": "#2ca02c",
              "Market Participants & Information Environment": "#0b7a75", "Corporate Governance & Control": "#9467bd",
              "Market Characteristics & Outcomes": "#d62728", "Business Non-financial": "#17becf", "Business Financial": "#bcbd22",
              "Oversight & Regulation": "#e377c2", "Audit & Assurance": "#7f7f7f", "Banking & Financial Institutions": "#8c564b",
              "International Business & Cross-border Activities": "#aec7e8"}
for d in EXT:
    CAT_COLORS[d] = ORANGE
STREAM_COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#F5A623", "#aec7e8", "#98df8a", "#c5b0d5"]

st.set_page_config(page_title="Cross-national accounting research network", layout="wide")


# ------------------------------------------------------------------ data
@st.cache_data
def load_data():
    edges = pd.read_csv("data/edges.csv")
    nodes = pd.read_csv("data/nodes.csv")
    arts = pd.read_csv("data/article_relationships.csv")
    studies = pd.read_csv("data/studies.csv")
    G = nx.DiGraph()
    for r in nodes.itertuples():
        G.add_node(r.node, category=r.category, external=bool(r.external), stream=r.stream, degree=int(r.degree))
    for r in edges.itertuples():
        G.add_edge(r.source, r.target, weight=int(r.hypotheses))
    return edges, nodes, arts, studies, G


edges, nodes, arts, studies, G = load_data()
category = dict(zip(nodes["node"], nodes["category"]))
stream = dict(zip(nodes["node"], nodes["stream"]))
stream_names = sorted(s for s in set(stream.values()) if s[0].isdigit())
stream_color = {s: STREAM_COLORS[i % len(STREAM_COLORS)] for i, s in enumerate(stream_names)}


# ------------------------------------------------------------------ drawing helpers
def legend_html(entries, title=None):
    rows = []
    for kind, colour, label in entries:
        sw = (f'<span style="display:inline-block;width:13px;height:13px;border-radius:7px;background:{colour};vertical-align:middle;margin-right:7px"></span>'
              if kind == "node" else
              f'<span style="display:inline-block;width:26px;height:3px;background:{colour};vertical-align:middle;margin-right:7px"></span>')
        rows.append(f'<div style="margin:2px 0">{sw}{label}</div>')
    head = f'<div style="font-weight:600;margin-bottom:4px">{title}</div>' if title else ""
    return ('<div style="position:absolute;left:14px;bottom:14px;background:#fff;border:1px solid #ccc;border-radius:6px;'
            f'padding:8px 12px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#222;z-index:10">{head}{"".join(rows)}</div>')


def draw(nodes_spec, edges_spec, *, height=750, spring=25, legend=None, physics_off_after=True, label_wrap=None, font=13):
    """nodes_spec: dict node -> {color, size, label?, title?}; edges_spec: list of (u, v, {color, width, title?, dashes?})."""
    net = Network(height=f"{height}px", width="100%", directed=True, notebook=False, cdn_resources="in_line")
    net.barnes_hut()
    for n, a in nodes_spec.items():
        label = a.get("label", n)
        if label_wrap and label:
            label = "\n".join(textwrap.wrap(label, width=label_wrap))
        net.add_node(n, label=label, title=a.get("title", n), color=a["color"], size=a.get("size", 15), font={"size": font, "face": "Arial"})
    for u, v, a in edges_spec:
        net.add_edge(u, v, color=a["color"], width=a.get("width", 1.2), title=a.get("title", f"{u} \u2192 {v}"), dashes=a.get("dashes", False))
    net.set_options(f"""
    var options = {{
      "smooth": {{"type": "straightCross", "forceDirection": "none", "roundness": 0.1}},
      "interaction": {{"navigationButtons": true, "hover": true, "tooltipDelay": 100}},
      "edges": {{"arrows": {{"to": {{"enabled": true, "scaleFactor": 0.6}}}}}},
      "physics": {{"enabled": true, "solver": "forceAtlas2Based",
                   "forceAtlas2Based": {{"springLength": {spring}, "gravitationalConstant": -60}},
                   "minVelocity": 0.75,
                   "stabilization": {{"enabled": true, "iterations": 1500, "updateInterval": 50}}}}
    }}""")
    html = net.generate_html(notebook=False)
    if legend:
        html = html.replace("<body>", "<body>" + legend, 1)
    if physics_off_after:
        html = html.replace("</script>", "network.once('stabilizationIterationsDone', function(){ network.setOptions({physics:false}); });</script>", 1)
    components.html(html, height=height + 20, scrolling=False)


def node_title(n):
    d = G.nodes[n]
    return (f"{n}\nCategory: {d['category']}\nStream: {d['stream']}\n"
            f"As determinant: {G.out_degree(n)} relationships | As outcome: {G.in_degree(n)} relationships")


def relationship_table(sub):
    rows = []
    for u, v, d in sub.edges(data=True):
        a = arts[(arts.source == u) & (arts.target == v)]
        cites = "; ".join(a["citation"].tolist())
        rows.append({"Determinant": u, "Outcome": v, "Hypotheses": d["weight"], "Tested in": cites})
    return pd.DataFrame(rows).sort_values(["Hypotheses", "Determinant"], ascending=[False, True]).reset_index(drop=True)



def match_concepts(q, names):
    """Concepts whose name contains q, ranked: exact name first, then whole-word
    matches, then any substring. Case-insensitive."""
    q = q.strip().lower()
    if not q:
        return []
    import re as _re
    word = _re.compile(r"\b" + _re.escape(q) + r"\b")
    hits = [n for n in names if q in n.lower()]
    rank = lambda n: (0 if n.lower() == q else 1 if word.search(n.lower()) else 2, n.lower())
    return sorted(hits, key=rank)


def pick_concepts(q, matches, key):
    """Let the reader narrow a broad search to the concept(s) they meant.
    Defaults to the exact match when the search text is a full concept name."""
    exact = [n for n in matches if n.lower() == q.strip().lower()]
    if len(matches) == 1:
        return matches
    return st.multiselect(
        f"{len(matches)} concepts contain \u201c{q.strip()}\u201d. Show results for:",
        matches, default=exact or matches, key=key,
        help="Remove concepts to narrow the results; add them back to widen.")


TABLE_TIP = ("The magnifying glass in a table's top-right corner highlights matching cells "
             "without removing other rows. Use the search box and concept selector above to filter.")

# ------------------------------------------------------------------ sidebar
st.sidebar.title("Cross-national accounting research network")
view = st.sidebar.radio("View", ["Full network", "Concept search", "Category map (Figure 6)", "Discipline network (Figure 8)",
                                 "Study lookup", "All 262 studies", "About the data"])
st.sidebar.markdown("---")
st.sidebar.caption("575 concepts, 683 unique hypothesized relationships, 701 hypotheses, 262 articles in six journals, 1973 to 2022. "
                   "Arrows run from determinant (independent variable) to outcome (dependent variable). Hover a node or edge for details; drag to rearrange; scroll to zoom.")

# ================================================================== 1. full network
if view == "Full network":
    st.header("The full network")
    col1, col2, col3 = st.columns([2, 2, 3])
    color_by = col1.selectbox("Color nodes by", ["Thematic category", "Research stream"])
    min_deg = col2.slider("Hide concepts with fewer connections than", 1, 10, 1)
    show_labels = col3.checkbox("Show concept labels (slower; labels appear as you zoom in)", value=False)
    H = G.subgraph([n for n in G if G.degree(n) >= min_deg])
    if color_by == "Thematic category":
        colour = lambda n: CAT_COLORS[category[n]]
        leg = legend_html([("node", c, k) for k, c in CAT_COLORS.items() if k not in EXT] + [("node", ORANGE, "External discipline (five disciplines)")], "Category")
    else:
        colour = lambda n: stream_color.get(stream[n], "#d9d9d9")
        leg = legend_html([("node", stream_color[s], s) for s in stream_names] + [("node", "#d9d9d9", "Smaller communities and fragments")], "Research stream")
    ns = {n: {"color": colour(n), "size": 6 + 1.5 * G.degree(n), "label": n if show_labels else " ", "title": node_title(n)} for n in H}
    es = [(u, v, {"color": "#c8c8c8", "width": 0.6, "title": f"{u} \u2192 {v} ({d['weight']} hypothes{'is' if d['weight']==1 else 'es'})"}) for u, v, d in H.edges(data=True)]
    st.caption(f"Showing {H.number_of_nodes()} concepts and {H.number_of_edges()} relationships. The layout settles over a few seconds.")
    draw(ns, es, height=800, spring=8, legend=leg, font=11)

# ================================================================== 2. concept search
elif view == "Concept search":
    st.header("Concept search and ego networks")
    q = st.text_input("Search for a concept (any part of the name, case-insensitive)", "government")
    radius = st.radio("Neighborhood", ["Direct relationships only", "Two steps"], horizontal=True)
    matches = match_concepts(q, G.nodes())
    if not q.strip():
        st.info("Type part of a concept name, for example *IFRS*, *earnings*, or *government*.")
    elif not matches:
        st.warning("No concept name contains that text. Try a shorter fragment.")
    else:
        focal = set(pick_concepts(q, matches, key="concept_pick"))
        if not focal:
            st.info("Select at least one concept above.")
            st.stop()
        nbr = set(focal)
        for n in focal:
            nbr |= set(G.predecessors(n)) | set(G.successors(n))
        if radius == "Two steps":
            for n in list(nbr):
                nbr |= set(G.predecessors(n)) | set(G.successors(n))
        sub = G.subgraph(nbr).copy()
        ns = {n: {"color": ORANGE if n in focal else (BLUE_NODE if not G.nodes[n]["external"] else "#F8D9A0"),
                  "size": 26 if n in focal else 14, "title": node_title(n)} for n in sub}
        es = [(u, v, {"color": ORANGE if (u in focal or v in focal) else GREY, "width": 1.6 if (u in focal or v in focal) else 0.9,
                      "title": f"{u} \u2192 {v} ({d['weight']} hypothes{'is' if d['weight']==1 else 'es'})"}) for u, v, d in sub.edges(data=True)]
        leg = legend_html([("node", ORANGE, "Matching concept"), ("node", BLUE_NODE, "Accounting and finance concept"), ("node", "#F8D9A0", "External-discipline concept"),
                           ("edge", ORANGE, "Relationship involving a matching concept"), ("edge", GREY, "Other relationship in the neighborhood")])
        st.caption(f"{sub.number_of_nodes()} concepts and {sub.number_of_edges()} relationships in the neighborhood.")
        draw(ns, es, height=650, spring=40, legend=leg, label_wrap=24, font=14)
        st.subheader("Relationships involving the matching concepts")
        focal_edges = sub.edge_subgraph([(u, v) for u, v in sub.edges() if u in focal or v in focal])
        st.dataframe(relationship_table(focal_edges), use_container_width=True, hide_index=True)
        st.caption(TABLE_TIP)

# ================================================================== 3. category map
elif view == "Category map (Figure 6)":
    st.header("Category-level map of the network")
    st.write("All 575 concepts collapsed to their 16 categories (11 accounting and finance areas, 5 external disciplines), with relationships aggregated between them. "
             "Node size and edge width scale with the number of unique relationships. Within-category relationships are not drawn.")
    thr = st.slider("Show category pairs linked by at least this many relationships", 1, 10, 3)
    agg = {}
    for u, v, d in G.edges(data=True):
        cu, cv = category[u], category[v]
        if cu != cv:
            agg[(cu, cv)] = agg.get((cu, cv), 0) + 1
    kept = {k: w for k, w in agg.items() if w >= thr}
    involve = {}
    for (cu, cv), w in agg.items():
        involve[cu] = involve.get(cu, 0) + w
        involve[cv] = involve.get(cv, 0) + w
    cats = sorted(set(category.values()))
    ns = {c: {"color": ORANGE if c in EXT else BLUE_NODE, "size": 12 + 0.25 * involve.get(c, 0), "title": f"{c}\n{involve.get(c, 0)} between-category relationships"} for c in cats}
    def ecol(cu, cv):
        return ORANGE if (cu in EXT and cv not in EXT) else (BLUE_EDGE if (cv in EXT and cu not in EXT) else GREY)
    es = [(cu, cv, {"color": ecol(cu, cv), "width": 0.6 + 0.35 * w, "title": f"{cu} \u2192 {cv}: {w} relationships"}) for (cu, cv), w in kept.items()]
    leg = legend_html([("node", BLUE_NODE, "Accounting and finance category"), ("node", ORANGE, "External discipline"),
                       ("edge", ORANGE, "External discipline \u2192 accounting category"), ("edge", BLUE_EDGE, "Accounting category \u2192 external discipline"), ("edge", GREY, "Accounting category \u2192 accounting category")])
    st.caption(f"{len(kept)} of {len(agg)} category pairs shown, carrying {sum(kept.values())} of {sum(agg.values())} between-category relationships.")
    draw(ns, es, height=700, spring=180, legend=leg, label_wrap=22, font=14)

# ================================================================== 4. discipline network
elif view == "Discipline network (Figure 8)":
    st.header("Sub-network of an external discipline")
    disc = st.selectbox("Discipline", EXT, index=0)
    mode = st.radio("Show the discipline's concepts as", ["One aggregated node (as in Figure 8)", "Individual concepts"], horizontal=True)
    D = {n for n in G if category[n] == disc}
    nbr = set()
    for n in D:
        nbr |= set(G.predecessors(n)) | set(G.successors(n))
    sub = G.subgraph(D | nbr).copy()
    d_out = [(u, v) for u, v in sub.edges() if u in D and v not in D]
    d_in = [(u, v) for u, v in sub.edges() if v in D and u not in D]
    d_d = [(u, v) for u, v in sub.edges() if u in D and v in D]
    other = [(u, v) for u, v in sub.edges() if u not in D and v not in D]
    if mode.startswith("One"):
        ns = {disc: {"color": ORANGE, "size": 45, "title": f"{disc}: {len(D)} concepts"}}
        for n in nbr - D:
            ns[n] = {"color": BLUE_NODE if not G.nodes[n]["external"] else "#F8D9A0", "size": 14, "title": node_title(n)}
        seen = set(); es = []
        for u, v in d_out:
            if (disc, v) not in seen: es.append((disc, v, {"color": ORANGE, "width": 1.5})); seen.add((disc, v))
        for u, v in d_in:
            if (u, disc) not in seen: es.append((u, disc, {"color": BLUE_EDGE, "width": 1.8})); seen.add((u, disc))
        es += [(u, v, {"color": GREY, "width": 1.0}) for u, v in other]
        note = f"{len(d_d)} relationship(s) between two {disc} concepts are not drawn in the aggregated view."
    else:
        ns = {n: {"color": ORANGE if n in D else (BLUE_NODE if not G.nodes[n]["external"] else "#F8D9A0"), "size": 14 + 2 * sub.degree(n), "title": node_title(n)} for n in sub}
        es = ([(u, v, {"color": ORANGE, "width": 1.5}) for u, v in d_out] + [(u, v, {"color": BLUE_EDGE, "width": 1.8}) for u, v in d_in]
              + [(u, v, {"color": ORANGE, "width": 1.5, "dashes": True}) for u, v in d_d] + [(u, v, {"color": GREY, "width": 1.0}) for u, v in other])
        note = ""
    leg = legend_html([("node", ORANGE, f"{disc} concept"), ("node", BLUE_NODE, "Accounting and finance concept"), ("node", "#F8D9A0", "Other external-discipline concept"),
                       ("edge", ORANGE, f"{disc} determinant \u2192 outcome"), ("edge", BLUE_EDGE, f"Determinant \u2192 {disc} outcome"), ("edge", GREY, "Relationship among the other concepts")])
    st.caption(f"{len(D)} {disc} concepts; {len(d_out)} relationships with a {disc} determinant, {len(d_in)} with a {disc} outcome, {len(d_d)} internal to the discipline, "
               f"{len(other)} among the connected concepts. {note}")
    draw(ns, es, height=750, spring=30, legend=leg, font=13)

# ================================================================== 5. study lookup
elif view == "Study lookup":
    st.header("Which studies test a relationship involving a term?")
    q = st.text_input("Word or phrase (matched against determinant and outcome concept names)", "government")
    if q.strip():
        matches = match_concepts(q, sorted(set(arts.source) | set(arts.target)))
        if not matches:
            st.warning("No hypothesized relationship involves a concept containing that text.")
        else:
            chosen = pick_concepts(q, matches, key="study_pick")
            m = arts[arts.source.isin(chosen) | arts.target.isin(chosen)].copy()
            if m.empty:
                st.info("Select at least one concept above.")
            else:
                m["relationship"] = m["source"] + " \u2192 " + m["target"]
                # rows for the best-matching concept first, then by year
                order = {n: i for i, n in enumerate(matches)}
                m["_rank"] = [min(order.get(a, 99), order.get(b, 99)) for a, b in zip(m.source, m.target)]
                st.write(f"**{m['article_id'].nunique()} article{'s' if m['article_id'].nunique() != 1 else ''}** test "
                         f"**{m['relationship'].nunique()} distinct relationship{'s' if m['relationship'].nunique() != 1 else ''}** "
                         f"involving the selected concept{'s' if len(chosen) != 1 else ''} ({len(m)} hypothes{'is' if len(m) == 1 else 'es'}).")
                show = (m.sort_values(["_rank", "year", "citation"])
                         [["citation", "authors", "year", "journal", "title", "relationship", "doi"]].reset_index(drop=True))
                st.dataframe(show, use_container_width=True, hide_index=True,
                             column_config={"doi": st.column_config.LinkColumn("DOI", display_text="link"), "citation": "Study",
                                            "authors": "Authors", "year": "Year", "journal": "Journal", "title": "Title",
                                            "relationship": "Relationship"})
                st.caption(TABLE_TIP)
                st.download_button("Download these rows as CSV", show.to_csv(index=False).encode(),
                                   file_name=f"studies_{q.strip().replace(' ', '_')}.csv")

# ================================================================== 6. all studies
elif view == "All 262 studies":
    st.header("The 262 articles in the sample")
    st.write("Every article coded for the network, in APA style. Each entry notes how many hypotheses it contributes.")
    q = st.text_input("Filter by author, title, journal, or year", "")
    shown = studies if not q.strip() else studies[studies.apa.str.contains(q.strip(), case=False, regex=False)]
    if shown.empty:
        st.warning("No article matches that text.")
    else:
        if q.strip():
            st.caption(f"{len(shown)} of 262 articles match \u201c{q.strip()}\u201d.")
        # the stored APA strings mark italics with *...*, as markdown does
        def to_html(t):
            return re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
        items = "".join(
            f'<p style="text-indent:-2em;padding-left:2em;margin:0 0 0.75em 0;line-height:1.45">{to_html(r.apa)}'
            f'<span style="color:#888"> [{r.hypotheses} hypothes{"is" if r.hypotheses == 1 else "es"}]</span></p>'
            for r in shown.itertuples())
        st.markdown(f'<div style="font-size:0.95rem">{items}</div>', unsafe_allow_html=True)
        st.download_button("Download the reference list as CSV",
                           shown[["article_id", "apa", "year", "journal", "hypotheses"]].to_csv(index=False).encode(),
                           file_name="cross_national_studies.csv")

# ================================================================== 7. about
else:
    st.header("About the data")
    st.markdown("""
The network is built from the hypothesized relationships in 262 articles published in six accounting journals
(*The Accounting Review*, *Journal of Accounting Research*, *Journal of Accounting and Economics*, *Contemporary Accounting Research*,
*Review of Accounting Studies*, and *Accounting, Organizations and Society*) between 1973 and 2022, each using data from ten or more countries.
Every hypothesis is coded as a directed relationship from an independent variable (determinant) to a dependent variable (outcome);
the 701 hypotheses reduce to 683 unique relationships among 575 concepts. Each concept is assigned to one of 11 accounting and finance
categories or one of five external disciplines, and to a research stream identified by community detection on the network's largest component.

The three files below are the complete dataset behind every view in this app.
""")
    c1, c2, c3 = st.columns(3)
    c1.download_button("edges.csv (683 relationships)", open("data/edges.csv", "rb").read(), "edges.csv")
    c2.download_button("nodes.csv (575 concepts)", open("data/nodes.csv", "rb").read(), "nodes.csv")
    c3.download_button("article_relationships.csv (701 hypotheses)", open("data/article_relationships.csv", "rb").read(), "article_relationships.csv")
    st.subheader("Most connected concepts")
    top = nodes.sort_values("degree", ascending=False).head(20)[["node", "category", "degree", "out_degree", "in_degree", "hypotheses_as_iv", "hypotheses_as_dv", "stream"]]
    st.dataframe(top, use_container_width=True, hide_index=True)
