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

## Run locally

```
pip install -r requirements.txt
streamlit run app.py
```

## Deploy anonymously

`anonymous.4open.science` mirrors a repository's *code* for double-blind review; it does not run
applications. The app therefore needs two links:

1. **Code (anonymized).** Push this folder to a GitHub repository under an account that does not
   identify the authors, then create an anonymized mirror at https://anonymous.4open.science/
   and cite that URL for the code and data.
2. **Running app.** Deploy the same repository on Streamlit Community Cloud (https://share.streamlit.io):
   New app, select the repository and `app.py`, and under *Advanced settings* set a custom
   subdomain (for example `cross-national-network`). The public URL is then
   `https://cross-national-network.streamlit.app`, which does not expose the GitHub account name.
   Use a repository and account created for this purpose; the default Streamlit URL pattern embeds
   the account name, so set the subdomain before sharing.

Neither link contains author names. The data files contain only bibliographic information about
the sampled articles.
