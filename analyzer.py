"""
demo/analyzer.py — ReviewIQ Stores (نسخة Demo)
فقط التحليل الأساسي بدون أي API.
Basic analysis only — no Claude API.
"""

from collections import Counter

from utils import (
    STORE_NEGATIVE_KEYWORDS,
    STORE_POSITIVE_KEYWORDS,
    sanitize_text,
)

MAX_REVIEWS = 200


def _clean_reviews(reviews):
    cleaned = []
    for r in reviews:
        s = sanitize_text(r)
        if s:
            cleaned.append(s)
    return cleaned[:MAX_REVIEWS]


def _score_sentiment(text: str):
    low = text.lower()
    pos_hits = sum(1 for w in STORE_POSITIVE_KEYWORDS["ar"] if w in low)
    pos_hits += sum(1 for w in STORE_POSITIVE_KEYWORDS["en"] if w in low)
    neg_hits = sum(1 for w in STORE_NEGATIVE_KEYWORDS["ar"] if w in low)
    neg_hits += sum(1 for w in STORE_NEGATIVE_KEYWORDS["en"] if w in low)

    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

        compound = SentimentIntensityAnalyzer().polarity_scores(text)["compound"]
        if compound >= 0.25:
            pos_hits += 1
        elif compound <= -0.25:
            neg_hits += 1
    except Exception:
        pass

    if pos_hits > neg_hits:
        return "positive"
    if neg_hits > pos_hits:
        return "negative"
    return "neutral"


def _extract_keywords(reviews, keyword_map):
    counter = Counter()
    for r in reviews:
        low = r.lower()
        for w in keyword_map["ar"] + keyword_map["en"]:
            if w in low:
                counter[w] += 1
    return counter


def _build_recommendations(neg_counter, neg_pct, lang):
    recs = []
    keys = set(neg_counter.keys())
    rules_ar = [
        ({"بطيء", "تأخير", "slow", "delay"}, "حسّن سرعة التوصيل وتابع شركات الشحن عن قرب."),
        ({"مكسور", "broken", "مشكلة", "issue"}, "راجِع جودة التغليف لتقليل تلف المنتجات أثناء الشحن."),
        ({"مزيف", "مختلف", "fake", "different"}, "تأكد من مطابقة المنتج للوصف والصور المعروضة."),
        ({"غالي", "expensive", "لا يستحق", "not worth"}, "أعد تقييم التسعير أو قدّم عروضاً تبرز القيمة."),
        ({"إرجاع", "return", "صعب", "difficult"}, "بسّط سياسة الإرجاع واجعلها أوضح للعميل."),
        ({"رديء", "poor"}, "افحص جودة المنتجات الأكثر شكوى وراجِع المورّدين."),
    ]
    rules_en = [
        ({"بطيء", "تأخير", "slow", "delay"}, "Improve delivery speed and monitor shipping partners closely."),
        ({"مكسور", "broken", "مشكلة", "issue"}, "Review packaging quality to reduce in-transit damage."),
        ({"مزيف", "مختلف", "fake", "different"}, "Ensure products match their description and photos."),
        ({"غالي", "expensive", "لا يستحق", "not worth"}, "Re-evaluate pricing or add offers that highlight value."),
        ({"إرجاع", "return", "صعب", "difficult"}, "Simplify the return policy and make it clearer."),
        ({"رديء", "poor"}, "Inspect quality of most-complained products and review suppliers."),
    ]
    rules = rules_ar if lang == "ar" else rules_en
    for trigger, advice in rules:
        if keys & trigger:
            recs.append(advice)
    if not recs:
        recs.append(
            "حافظ على مستوى الخدمة الحالي وراقب التقييمات دورياً."
            if lang == "ar"
            else "Maintain current service levels and monitor reviews regularly."
        )
    if neg_pct >= 30:
        recs.insert(
            0,
            "نسبة السلبي مرتفعة — خصّص فريقاً للرد السريع على الشكاوى."
            if lang == "ar"
            else "Negative ratio is high — assign a team for fast complaint response.",
        )
    return recs[:5]


def analyze_basic(reviews, lang="ar"):
    """تحليل أساسي محلي بالكامل. Fully local basic analysis."""
    reviews = _clean_reviews(reviews)
    if not reviews:
        return {"sentiments": [], "complaints": [], "praises": [],
                "recommendations": [], "summary": ""}

    sentiments = [_score_sentiment(r) for r in reviews]
    neg_counter = _extract_keywords(reviews, STORE_NEGATIVE_KEYWORDS)
    pos_counter = _extract_keywords(reviews, STORE_POSITIVE_KEYWORDS)

    complaints = [{"text": w, "count": c} for w, c in neg_counter.most_common(8)]
    praises = [{"text": w, "count": c} for w, c in pos_counter.most_common(8)]

    total = len(sentiments)
    neg = sentiments.count("negative")
    pos = sentiments.count("positive")
    neg_pct = round(100 * neg / total) if total else 0
    pos_pct = round(100 * pos / total) if total else 0

    recommendations = _build_recommendations(neg_counter, neg_pct, lang)

    if lang == "ar":
        summary = (
            f"تم تحليل {total} تقييم. النتائج: {pos_pct}% إيجابي، {neg_pct}% سلبي. "
            + (f"أبرز شكوى متكررة: «{complaints[0]['text']}»." if complaints else "لا توجد شكاوى متكررة واضحة.")
        )
    else:
        summary = (
            f"Analyzed {total} reviews. Results: {pos_pct}% positive, {neg_pct}% negative. "
            + (f"Top recurring complaint: '{complaints[0]['text']}'." if complaints else "No clear recurring complaints.")
        )

    return {
        "sentiments": sentiments,
        "complaints": complaints,
        "praises": praises,
        "recommendations": recommendations,
        "summary": summary,
    }
