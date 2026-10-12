# Patient-Reported Drug Review Analytics & Ranking

[![GitHub Pages](https://img.shields.io/badge/site-GitHub%20Pages-green)](https://harshini-suresha.github.io/patient-drug-analysis/)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Harshini-Suresha/patient-drug-analysis/blob/main/drug_review_analytics.ipynb)
[![Streamlit](https://img.shields.io/badge/app-Streamlit-red)](https://share.streamlit.io/)
[![nbviewer](https://img.shields.io/badge/view-nbviewer-orange)](https://nbviewer.org/github/Harshini-Suresha/patient-drug-analysis/blob/main/drug_review_analytics.ipynb)

**Condition-stratified drug ranking using shrinkage estimation and interactive analytics.**
Real Drugs.com reviews (UCI Drug Review Dataset), cleaned, ranked, validated.

> Educational analysis of patient opinions. Not clinical evidence and not medical advice.

## Live links (after push)

| What | Where |
|---|---|
| 🌐 Website (GitHub Pages) | https://harshini-suresha.github.io/patient-drug-analysis/ |
| 📓 Notebook in Colab (no install) | https://colab.research.google.com/github/Harshini-Suresha/patient-drug-analysis/blob/main/drug_review_analytics.ipynb |
| 📓 Notebook in browser (nbviewer) | https://nbviewer.org/github/Harshini-Suresha/patient-drug-analysis/blob/main/drug_review_analytics.ipynb |
| 🎈 Streamlit app (after 1-click deploy below) | `https://<your-app>.streamlit.app` |

## What's in this repo

| File | Purpose |
|---|---|
| `index.html` | Static site — works offline, hosts GitHub Pages. Self-contained (all stats embedded). |
| `Patient-Reported Drug Review Analytics & Ranking.html` | Original copy of the site (same as `index.html`). |
| `drug_review_analytics.ipynb` | Companion notebook — reproduces every number + Love-or-Hate index + bootstrap rank robustness. Colab-ready. |
| `app.py` | Streamlit version of the lookup (same shrinkage logic). |
| `requirements.txt` | `pip install -r requirements.txt` for Streamlit / local runs. |
| `archive.zip` | Raw UCI files (`drugsComTrain_raw.csv`, `drugsComTest_raw.csv`). 41MB, shipped so Colab/Streamlit work offline. The code also auto-downloads from UCI if missing. |

## Run locally

```bash
# 1. static site (no install)
open index.html
# or
python3 -m http.server 8000
# -> http://localhost:8000

# 2. notebook
pip install pandas numpy matplotlib scipy
jupyter notebook drug_review_analytics.ipynb

# 3. streamlit
pip install -r requirements.txt
streamlit run app.py
```

## Open in Colab

Click the **Open in Colab** badge above, or manually: `colab.research.google.com → File → Open notebook → GitHub → Harshini-Suresha/patient-drug-analysis`.
Choose *Runtime → Run all*. If the automatic UCI download is blocked, upload `archive.zip` when prompted (the notebook handles it).

## Deploy Streamlit Cloud (free, 2 min)

1. Push this repo to GitHub (see below).
2. Go to https://share.streamlit.io → New app → select `Harshini-Suresha/patient-drug-analysis` → `app.py` → Deploy.
3. Your app gets a `https://*.streamlit.app` URL. Add it to the table above.

## Enable GitHub Pages (`github.io` domain)

Pages serves `index.html` from the `main` branch root:

```bash
gh repo create patient-drug-analysis --public --source=. --push
# then: repo Settings → Pages → Deploy from branch → main / (root) → Save
# live at: https://harshini-suresha.github.io/patient-drug-analysis/
```

Or via CLI after first push:

```bash
gh api repos/Harshini-Suresha/patient-drug-analysis/pages -X POST \
  -f build_type=legacy -f source='{"branch":"main","path":"/"}'
```

## Method in 30 seconds

For condition *c*, drug *d* with *n* reviews and mean *x̄*:

`score = n/(n+m) · x̄ + m/(n+m) · μc`

where *μc* is the condition mean and *m* (default 10) is the prior strength.
Validated with split-half Spearman ρ across 89 conditions; diagnosed with Love-or-Hate Index `LHI = 4·P(≤3)·P(≥8)` and bootstrap rank intervals.

Dataset: [UCI Drug Review Dataset (Drugs.com)](https://archive.ics.uci.edu/dataset/462/drug+review+dataset+drugs+com)

## Contact

harshinisuresha7@gmail.com
