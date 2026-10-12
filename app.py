"""Patient-Reported Drug Review Analytics — Streamlit app.

Same shrinkage ranking as the notebook + static site, but interactive.
Run locally:  pip install -r requirements.txt && streamlit run app.py
Deploy: share.streamlit.io -> point at this repo / app.py
"""
import glob
import html
import re
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.stats import norm, spearmanr

st.set_page_config(page_title="Drug Review Analytics", layout="wide")

UCI_URL = "https://archive.ics.uci.edu/static/public/462/drug+review+dataset+drugs+com.zip"
RNG = np.random.default_rng(42)

FIX = {"Ibromyalgia": "Fibromyalgia", "Emale Infertility": "Female Infertility",
       "Atigue": "Fatigue", "Acial Wrinkles": "Facial Wrinkles",
       "Ibrocystic Breast Disease": "Fibrocystic Breast Disease",
       "Amilial Mediterranean Feve": "Familial Mediterranean Fever",
       "Ailure To Thrive": "Failure To Thrive",
       "Llicle Stimulation": "Follicle Stimulation",
       "Llicular Lymphoma": "Follicular Lymphoma",
       "Ungal Infection Prophylaxis": "Fungal Infection Prophylaxis",
       "Ungal Pneumonia": "Fungal Pneumonia",
       "Unctional Gastric Disorde": "Functional Gastric Disorder",
       "Cal Segmental Glomerulosclerosis": "Focal Segmental Glomerulosclerosis",
       "Eve": "Fever", "Zen Shoulde": "Frozen Shoulder",
       "Mance Anxiety": "Performance Anxiety",
       "Not Listed / Othe": "Not Listed / Other",
       "Premature Lab": "Premature Labor", "Vertig": "Vertigo",
       "Impetig": "Impetigo", "Tinea Versicol": "Tinea Versicolor", "Cance": "Cancer"}
SUFFIX = [(r" Disorde$", " Disorder"), (r" Cance$", " Cancer"), (r" Tum$", " Tumor"),
          (r" Ulce$", " Ulcer"), (r" Bladde$", " Bladder"), (r" Zoste$", " Zoster"),
          (r" Trem$", " Tremor"), (r" Feve$", " Fever")]


@st.cache_data(show_spinner=True)
def load_data():
    def find_files():
        tr = glob.glob("**/drugsComTrain_raw.*", recursive=True)
        te = glob.glob("**/drugsComTest_raw.*", recursive=True)
        return (tr[0], te[0]) if tr and te else None

    files = find_files()
    if not files:
        # repo ships archive.zip (41MB) — use it if present
        for candidate in ["archive.zip", "uci.zip", "data/uci.zip"]:
            if Path(candidate).exists():
                try:
                    zipfile.ZipFile(candidate).extractall("data")
                    files = find_files()
                    break
                except Exception:
                    pass
    if not files:
        # fall back to UCI download (cached by streamlit)
        urllib.request.urlretrieve(UCI_URL, "uci.zip")
        zipfile.ZipFile("uci.zip").extractall("data")
        files = find_files()
    if not files:
        st.error("Could not find or download the UCI files. Upload archive.zip next to app.py.")
        st.stop()

    read = lambda p: pd.read_csv(p, sep="\t" if p.endswith(".tsv") else ",")
    raw = pd.concat([read(f) for f in files], ignore_index=True)

    artifact = raw["condition"].str.contains("users found this comment helpful", case=False, na=False)
    df = raw.dropna(subset=["condition", "drugName", "rating"])
    df = df[~df["condition"].str.contains("users found this comment helpful", case=False, na=False)].copy()
    df["condition"] = df["condition"].str.strip().str.title().str.replace(r"'S\b", "'s", regex=True)
    df["drugName"] = df["drugName"].str.strip()

    have = set(df["condition"])

    def repair(n):
        m = FIX.get(n, n)
        if m == n:
            for pat, rep in SUFFIX:
                m = re.sub(pat, rep, m)
        return n if (m != n and m in have) else m

    mapping = {n: repair(n) for n in have}
    df["condition"] = df["condition"].map(mapping)
    df["review"] = df["review"].fillna("").map(html.unescape).str.strip('" ')
    df["r"] = df["rating"].round().astype(int)
    df["year"] = pd.to_datetime(df["date"], format="%d-%b-%y", errors="coerce").dt.year
    return df, len(raw), int(artifact.sum())


df, n_raw, n_art = load_data()

st.title("Patient-Reported Drug Review Analytics & Ranking")
st.caption(
    f"{len(df):,} clean reviews ({n_raw:,} raw, {n_art:,} scraping artifacts removed) · "
    f"{df.condition.nunique():,} conditions · {df.drugName.nunique():,} drugs · "
    "Educational analysis of patient opinions. Not medical advice."
)

# ---- sidebar ----
conds = sorted(df["condition"].unique())
default_ix = conds.index("Depression") if "Depression" in conds else 0
with st.sidebar:
    st.header("Settings")
    cond = st.selectbox("Condition", conds, index=default_ix)
    m = st.slider("Shrinkage m", 0, 100, 10,
                  help="score = n/(n+m)·mean + m/(n+m)·condition-mean. m=0 is raw mean.")
    min_n = st.slider("Min reviews per drug", 1, 100, 10)
    B = st.slider("Bootstrap B (robustness)", 100, 1000, 500, step=100)

sub = df[df.condition == cond]
C = sub.rating.mean()
pairs = (sub.groupby("drugName")
            .agg(n=("rating", "size"), mean=("rating", "mean"),
                 useful=("usefulCount", "mean")).reset_index())
pairs["score"] = pairs.n / (pairs.n + m) * pairs["mean"] + m / (pairs.n + m) * C if m else pairs["mean"]
pairs["rank_raw"] = pairs["mean"].rank(ascending=False, method="min").astype(int)
pairs["rank_shrunk"] = pairs.score.rank(ascending=False, method="min").astype(int)
ranked = pairs[pairs.n >= min_n].sort_values("score", ascending=False).reset_index(drop=True)

tab1, tab2, tab3, tab4 = st.tabs(["Ranking", "Sensitivity & uncertainty", "Love-or-Hate", "Head-to-head"])

with tab1:
    st.subheader(f"{cond} — top drugs by shrunk score (m={m}, C={C:.2f})")
    st.dataframe(ranked.head(30).round(2), use_container_width=True)
    st.download_button("Download this ranking (CSV)",
                       ranked.round(4).to_csv(index=False), f"{cond}_ranking.csv")
    if len(ranked):
        top = ranked.iloc[0]
        st.info(f"Top: **{top.drugName}** — score {top.score:.2f}, mean {top['mean']:.2f}, n={top.n}")

with tab2:
    st.subheader("Shrinkage sensitivity (top 6 by raw mean)")
    if len(ranked):
        top6 = pairs.sort_values("mean", ascending=False).head(6)
        ms = [0, 1, 2, 5, 10, 20, 35, 50, 75, 100]
        fig, ax = plt.subplots()
        for _, r in top6.iterrows():
            ax.plot(ms,
                    [r["mean"] if mm == 0 else r.n / (r.n + mm) * r["mean"] + mm / (r.n + mm) * C
                     for mm in ms], marker="o", label=f"{r.drugName} (n={r.n})")
        ax.set_xlabel("m"); ax.set_ylabel("score"); ax.legend(fontsize=7)
        st.pyplot(fig)

    st.subheader("Rank robustness (bootstrap)")
    arrs = {d: x.rating.values for d, x in sub.groupby("drugName") if len(x) >= max(min_n, 30)}
    if len(arrs) >= 2:
        names = list(arrs)
        scores = np.empty((B, len(names)))
        for j, d in enumerate(names):
            a = arrs[d]; n = len(a)
            means = RNG.choice(a, size=(B, n)).mean(axis=1)
            scores[:, j] = n / (n + m) * means + m / (n + m) * C if m else means
        ranks = (-scores).argsort(axis=1).argsort(axis=1) + 1
        out = (pd.DataFrame({"drug": names, "n": [len(arrs[d]) for d in names],
                             "P(rank 1)": (ranks == 1).mean(0),
                             "P(top 3)": (ranks <= 3).mean(0),
                             "rank 5%": np.percentile(ranks, 5, axis=0),
                             "rank 95%": np.percentile(ranks, 95, axis=0)})
                 .sort_values("P(top 3)", ascending=False))
        st.dataframe(out.head(12).round(2), use_container_width=True)
    else:
        st.warning("Not enough drugs with 30+ reviews for bootstrap.")

with tab3:
    st.subheader("Love-or-Hate Index: LHI = 4·P(≤3)·P(≥8)")
    g = df.groupby("drugName").agg(n=("r", "size"), mean=("rating", "mean"),
                                    p_low=("r", lambda x: (x <= 3).mean()),
                                    p_high=("r", lambda x: (x >= 8).mean()))
    g["LHI"] = 4 * g.p_low * g.p_high
    big = g[g.n >= 100].sort_values("LHI", ascending=False).head(10)
    st.dataframe(big.round(2), use_container_width=True)
    fig, ax = plt.subplots()
    sc = ax.scatter(g[g.n >= 100]["mean"], g[g.n >= 100].LHI, alpha=.4)
    ax.set_xlabel("mean rating"); ax.set_ylabel("LHI")
    st.pyplot(fig)

with tab4:
    st.subheader("Is drug A really better than drug B?")
    drugs = ranked.drugName.tolist()[:80]
    if len(drugs) >= 2:
        a_name = st.selectbox("Drug A", drugs, index=0)
        b_name = st.selectbox("Drug B", drugs, index=1 if len(drugs) > 1 else 0)
        if a_name != b_name and m is not None:
            res = {}
            for name in (a_name, b_name):
                x = sub[sub.drugName == name].rating.values
                n = len(x)
                res[name] = (n / (n + m) * x.mean() + m / (n + m) * C if m else x.mean(),
                             x.var(ddof=0) / (n + m) if m else x.var(ddof=0) / n, n)
            (ma, va, na), (mb, vb, nb) = res[a_name], res[b_name]
            p = float(norm.cdf((ma - mb) / np.sqrt(va + vb)))
            st.write(f"Shrunk A **{ma:.2f}** (n={na}) vs B **{mb:.2f}** (n={nb})")
            st.write(f"**P(A > B) = {p:.0%}** — Normal–normal posterior, descriptive only.")
    else:
        st.warning("Need at least 2 drugs.")

st.divider()
st.caption("Dataset: UCI Drug Review Dataset (Drugs.com). Static site version is in index.html (GitHub Pages). "
           "Notebook version is drug_review_analytics.ipynb (Open in Colab). Contact: harshinisuresha7@gmail.com")
st.markdown("**Contact:** [harshinisuresha7@gmail.com](mailto:harshinisuresha7@gmail.com)")
