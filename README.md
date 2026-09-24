# Cross-national accounting research network: interactive companion

Interactive companion to *A Conceptual Review of the Cross-National Accounting Literature*.
A single Streamlit app (`app.py`) with five views: the full network colored by category or
research stream, concept search with ego networks and relationship tables, the category-level
map (interactive Figure 6), the external-discipline sub-networks (interactive Figure 8), and a
study lookup that returns every sampled article testing a relationship involving a term.

## Files

| Path | Contents |
|---|---|
| `app.py` | The app |
| `requirements.txt` | Python dependencies |
| `data/edges.csv` | 683 unique relationships: `source`, `target`, `hypotheses` |
| `data/nodes.csv` | 575 concepts: category, external flag, degrees, hypothesis counts, research stream |
| `data/article_relationships.csv` | 701 hypotheses: one row per article and relationship, with citation, journal, title, DOI |
| `data/studies.csv` | 262 articles: APA reference string, year, journal, hypothesis count |

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```
