"""
demo/app.py — ReviewIQ Stores (نسخة Demo)
نسخة مبسّطة: تحليل أساسي فقط، مصدر واحد (CSV مخصص)،
بدون تصدير PDF/Excel وبدون اقتراح ردود (تظهر رسالة "متوفر في النسخة الكاملة").
Simplified demo: basic analysis only, single source (custom CSV),
no PDF/Excel export, no reply suggestions.
"""

import io

import pandas as pd
import streamlit as st

from analyzer import analyze_basic
from utils import (
    t,
    sanitize_text,
    find_critical_word,
    STORE_NEGATIVE_KEYWORDS,
    STORE_POSITIVE_KEYWORDS,
)

# ============================================================================
#  CSS — نفس النسخة الكاملة (لا يُعدَّل)
# ============================================================================
CUSTOM_CSS = """
<style>
/* ===== RTL + FONTS ===== */
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&display=swap');
html, body, [class="css"] { font-family: 'Cairo' !important; }
.main .block-container { direction: rtl !important; }
[data-testid="stSidebar"] > div { direction: rtl !important; }
[data-testid="stAppDeployButton"] { display: none !important; }
#MainMenu, footer { visibility: hidden !important; }
header { background-color: transparent !important; }
[data-testid="stSlider"] { direction: ltr !important; }
[data-testid="collapsedControl"] {
    position: fixed !important; top: 15px !important; left: 15px !important;
    display: flex !important; visibility: visible !important; opacity: 1 !important;
    z-index: 999999 !important; background-color: #1e293b !important;
    border: 1px solid #334155 !important; border-radius: 8px !important;
}

/* ===== DARK THEME ===== */
.stApp { background-color: #0e1117 !important; color: #fafafa !important; }
[data-testid="stSidebar"] { background-color: #1e293b !important; }
.stMetric {
    background-color: #1e293b !important;
    padding: 15px !important;
    border-radius: 10px !important;
    border: 1px solid #334155 !important;
}

/* ===== SIDEBAR TEXT — نصوص الشريط الجانبي ===== */
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }

/* ===== INPUT FIELDS — حقول الإدخال ===== */
.stTextInput input {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
}
.stSelectbox div[data-baseweb="select"] {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
}
.stTextArea textarea {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #475569 !important;
}

/* ===== RADIO BUTTONS — لون التحديد ===== */
[data-testid="stRadio"] input:checked + div { accent-color: #38bdf8 !important; }

/* ===== KPI CARDS ===== */
[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}
[data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background-color: #1e293b !important;
    border: 2px dashed #475569 !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"] * { color: #cbd5e1 !important; }
[data-testid="stFileUploaderDropzone"] { background-color: #1e293b !important; }
[data-testid="stFileUploaderDropzone"] p { color: #94a3b8 !important; }

/* ===== TEXT INPUT ===== */
.stTextInput input {
    background-color: #1e293b !important;
    color: #f1f5f9 !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 6px !important;
}
</style>
"""

st.set_page_config(page_title="ReviewIQ Stores — Demo", page_icon="🛒", layout="wide")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================================
#  قراءة CSV مبسّطة — simplified CSV reading with column auto-detect
# ============================================================================
TEXT_ALIASES = ["review_text", "review", "body", "content", "comment", "text",
                "feedback", "نص التقييم", "التقييم", "المراجعة", "تعليق"]
RATING_ALIASES = ["rating", "stars", "score", "نجوم", "الدرجة", "تقييم"]


@st.cache_data(show_spinner=False)
def read_csv(file_bytes, file_name):
    for enc in ("utf-8-sig", "utf-8", "cp1256", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc, sep=None, engine="python")
            break
        except Exception:
            df = None
    if df is None or df.empty:
        return pd.DataFrame(columns=["review_text", "rating"])

    df.columns = [str(c).strip().lower() for c in df.columns]

    def match(aliases):
        for a in aliases:
            for c in df.columns:
                if a.lower() in c or c in a.lower():
                    return c
        return None

    text_col = match(TEXT_ALIASES)
    if text_col is None:
        obj = [c for c in df.columns if df[c].dtype == object]
        text_col = max(obj, key=lambda c: df[c].astype(str).str.len().mean()) if obj else df.columns[0]
    rating_col = match(RATING_ALIASES)

    out = pd.DataFrame()
    out["review_text"] = df[text_col].astype(str).str.strip()
    out["rating"] = pd.to_numeric(df[rating_col], errors="coerce") if rating_col else None
    out = out[out["review_text"].notna() & (out["review_text"] != "") & (out["review_text"].str.lower() != "nan")]
    return out.reset_index(drop=True).head(200)


def reputation_color(score):
    if score > 70:
        return "#2ecc71"
    if score >= 40:
        return "#f1c40f"
    return "#e74c3c"


def render_keyword_map(df, lang):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from collections import Counter

    texts = " ".join(df["review_text"].astype(str).tolist()).lower()
    pos_words = STORE_POSITIVE_KEYWORDS["ar"] + STORE_POSITIVE_KEYWORDS["en"]
    neg_words = STORE_NEGATIVE_KEYWORDS["ar"] + STORE_NEGATIVE_KEYWORDS["en"]

    counter, sentiment_of = Counter(), {}
    for w in pos_words:
        c = texts.count(w)
        if c:
            counter[w] = c
            sentiment_of[w] = "positive"
    for w in neg_words:
        c = texts.count(w)
        if c:
            counter[w] = c
            sentiment_of[w] = "negative"

    if not counter:
        st.info(t("no_data", lang))
        return

    items = counter.most_common(15)
    words = [w for w, _ in items]
    counts = [c for _, c in items]
    colors = [{"positive": "#2ecc71", "negative": "#e74c3c"}.get(sentiment_of.get(w), "#95a5a6") for w in words]

    fig, ax = plt.subplots(figsize=(8, max(3, len(words) * 0.4)))
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")
    ax.barh(range(len(words)), counts, color=colors)
    ax.set_yticks(range(len(words)))
    ax.set_yticklabels(words, color="#fafafa")
    ax.invert_yaxis()
    ax.tick_params(colors="#fafafa")
    for spine in ax.spines.values():
        spine.set_color("#334155")
    ax.set_xlabel(t("count", lang), color="#fafafa")
    st.pyplot(fig)
    plt.close(fig)


def render_critical(df, lang):
    st.markdown(f"<h3 style='color:#e74c3c;'>🚨 {t('critical_reviews_urgent', lang)}</h3>",
                unsafe_allow_html=True)
    found = False
    for _, row in df.iterrows():
        txt = sanitize_text(row.get("review_text", ""))
        cw = find_critical_word(txt)
        if cw:
            found = True
            st.markdown(
                f"""
                <div style='background-color:#3b1414;border:1px solid #e74c3c;
                            border-radius:8px;padding:12px;margin-bottom:8px;'>
                    <span style='color:#ff8a80;font-weight:700;'>{t('critical_word', lang)}: {cw}</span><br>
                    <span style='color:#f1f5f9;'>{txt}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if not found:
        st.success(t("no_critical", lang))


def compute_kpis(df, analysis):
    total = len(df)
    ratings = pd.to_numeric(df.get("rating"), errors="coerce").dropna() if "rating" in df else pd.Series(dtype=float)
    avg_rating = round(float(ratings.mean()), 2) if not ratings.empty else 0.0
    s = analysis.get("sentiments", [])
    n = len(s) or 1
    pos_pct = round(100 * s.count("positive") / n)
    neg_pct = round(100 * s.count("negative") / n)
    has_critical = any(find_critical_word(x) for x in df.get("review_text", pd.Series(dtype=str)))
    no_critical = 0 if has_critical else 1
    # نفس صيغة النسخة الكاملة (معدل الرد = 0 في الـ demo)
    reputation = int(round(max(0, min(100,
        (avg_rating / 5) * 40 + (pos_pct / 100) * 35 + 0 * 15 + no_critical * 10))))
    return {"reputation_score": reputation, "total_reviews": total,
            "avg_rating": avg_rating, "negative_pct": neg_pct, "positive_pct": pos_pct}


# ============================================================================
#  التطبيق — main
# ============================================================================

def main():
    with st.sidebar:
        st.markdown("## 🛒 ReviewIQ Stores")
        lang = st.radio("Language / اللغة", options=["ar", "en"],
                        format_func=lambda x: "العربية" if x == "ar" else "English")
        st.markdown(f"<span style='background:#38bdf8;color:#0e1117;padding:2px 10px;"
                    f"border-radius:12px;font-size:12px;'>{t('demo_badge', lang)}</span>",
                    unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📥 " + t("data_source", lang))
        st.caption(t("source_custom", lang))
        file = st.file_uploader(t("upload_file", lang), type=["csv"], key="uploader")

    st.title("📊 " + t("app_title", lang))
    st.caption(t("app_subtitle", lang))

    if file is None:
        st.info(t("no_data", lang))
        # عرض الميزات المقفلة
        st.markdown("---")
        st.markdown(t("full_version_only", lang) + " — PDF / Excel · "
                    + t("data_source", lang) + " (سلة · زد · أمازون)")
        return

    try:
        df = read_csv(file.getvalue(), file.name)
    except Exception:
        st.error(t("error_file", lang))
        return

    if df.empty:
        st.warning(t("error_file", lang))
        return

    if len(df) >= 200:
        st.caption("ℹ️ " + t("rows_limited", lang))

    with st.spinner(t("loading", lang)):
        analysis = analyze_basic(df["review_text"].tolist(), lang)

    kpis = compute_kpis(df, analysis)

    # بطاقة Reputation Score
    color = reputation_color(kpis["reputation_score"])
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg,{color}33,#1e293b);
                    border:2px solid {color};border-radius:16px;
                    padding:24px;text-align:center;margin-bottom:18px;'>
            <div style='color:#cbd5e1;font-size:18px;'>{t('reputation_score', lang)}</div>
            <div style='color:{color};font-size:64px;font-weight:800;line-height:1;'>
                {kpis['reputation_score']}<span style='font-size:28px;'>/100</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(t("total_reviews", lang), kpis["total_reviews"])
    c2.metric(t("avg_rating", lang), kpis["avg_rating"])
    c3.metric(t("negative_pct", lang), f"{kpis['negative_pct']}%")

    st.divider()

    colA, colB = st.columns(2)
    with colA:
        st.subheader(t("sentiment_dist", lang))
        s = analysis.get("sentiments", [])
        if s:
            import plotly.express as px
            counts = {t("positive", lang): s.count("positive"),
                      t("negative", lang): s.count("negative"),
                      t("neutral", lang): s.count("neutral")}
            fig = px.pie(names=list(counts.keys()), values=list(counts.values()), hole=0.45,
                         color=list(counts.keys()),
                         color_discrete_map={t("positive", lang): "#2ecc71",
                                             t("negative", lang): "#e74c3c",
                                             t("neutral", lang): "#95a5a6"})
            fig.update_layout(paper_bgcolor="#0e1117", font_color="#fafafa")
            st.plotly_chart(fig, use_container_width=True)
    with colB:
        st.subheader(t("summary", lang))
        st.write(analysis.get("summary", ""))
        if analysis.get("recommendations"):
            st.markdown("**" + t("recommendations", lang) + "**")
            for r in analysis["recommendations"]:
                st.markdown(f"- {r}")

    st.divider()
    colC, colD = st.columns(2)
    with colC:
        st.subheader("👎 " + t("complaints", lang))
        for c in analysis.get("complaints", []):
            st.markdown(f"- {c['text']} — **{c['count']}**")
    with colD:
        st.subheader("👍 " + t("praises", lang))
        for p in analysis.get("praises", []):
            st.markdown(f"- {p['text']} — **{p['count']}**")

    st.divider()
    st.subheader("🗺️ " + t("keyword_sentiment", lang))
    st.caption(t("keyword_sentiment_desc", lang))
    render_keyword_map(df, lang)

    st.divider()
    render_critical(df, lang)

    # الميزات المقفلة في الـ demo
    st.divider()
    st.info(t("full_version_only", lang) + " — "
            "💬 " + ("اقتراح ردود AI" if lang == "ar" else "AI Reply Suggestions") + " · "
            "📄 PDF / Excel · 📅 " + ("مقارنة فترتين" if lang == "ar" else "Period Comparison"))


if __name__ == "__main__":
    main()
