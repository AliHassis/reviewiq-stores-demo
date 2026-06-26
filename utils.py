"""
demo/utils.py — ReviewIQ Stores (نسخة Demo)
نفس الترجمات والكلمات بدون مفاتيح الميزات المحذوفة (الردود، اللوغو، اقتراحات).
Same translations/keywords, without the removed-feature keys.
"""

import re

# ============================================================================
#  كلمات المتاجر — Store keywords
# ============================================================================

STORE_NEGATIVE_KEYWORDS = {
    "ar": [
        "بطيء", "تأخير", "مكسور", "مختلف", "مزيف", "غالي",
        "رديء", "مشكلة", "إرجاع", "صعب", "لا يستحق",
    ],
    "en": [
        "slow", "delay", "broken", "different", "fake", "expensive",
        "poor", "issue", "return", "difficult", "not worth",
    ],
}

STORE_POSITIVE_KEYWORDS = {
    "ar": [
        "سريع", "أصلي", "ممتاز", "مطابق", "نظيف",
        "تغليف رائع", "خدمة ممتازة", "سعر مناسب",
    ],
    "en": [
        "fast", "original", "excellent", "accurate", "clean",
        "great packaging", "great service", "good price",
    ],
}

CRITICAL_WORDS_AR = [
    "احتيال", "نصب", "مزيف", "مقلد", "مسروق", "مكسور", "خطر",
    "حريق", "انفجار", "سام", "ضار", "غش", "سرقة",
]
CRITICAL_WORDS_EN = [
    "fraud", "scam", "fake", "counterfeit", "stolen", "broken",
    "dangerous", "fire", "explosion", "toxic", "harmful", "cheat",
    "theft", "defective", "lawsuit",
]

# ============================================================================
#  الترجمات — Translations (بدون مفاتيح الميزات المحذوفة)
# ============================================================================

TRANSLATIONS = {
    "ar": {
        "app_title": "ReviewIQ للمتاجر — نسخة تجريبية",
        "app_subtitle": "جرّب التحليل الأساسي لتقييمات متجرك",
        "language": "اللغة",
        "settings": "الإعدادات",
        "menu": "القائمة",
        "page_analysis": "التحليل",
        "data_source": "مصدر البيانات",
        "source_custom": "ملف مخصص (CSV)",
        "upload_file": "ارفع الملف",
        "analyze_btn": "حلّل التقييمات",
        "no_data": "لا توجد بيانات بعد. ارفع ملف CSV للبدء.",
        "loading": "جارٍ التحليل...",
        "rows_limited": "تم تحليل أول 200 تقييم فقط للحفاظ على الأداء.",
        "error_file": "تعذّر قراءة الملف. تأكد من الصيغة.",

        "reputation_score": "مؤشر السمعة",
        "total_reviews": "إجمالي التقييمات",
        "avg_rating": "متوسط التقييم",
        "negative_pct": "نسبة السلبي",
        "positive_pct": "نسبة الإيجابي",

        "keyword_sentiment": "خريطة مشاعر الكلمات",
        "keyword_sentiment_desc": "الكلمات الأكثر تكراراً ملوّنة حسب المشاعر",
        "critical_reviews_urgent": "تقييمات تحتاج رد فوري",
        "critical_word": "الكلمة الحرجة",
        "no_critical": "لا توجد تقييمات حرجة. ممتاز!",

        "complaints": "أبرز الشكاوى",
        "praises": "أبرز المديح",
        "recommendations": "التوصيات",
        "summary": "الملخص",
        "sentiment_dist": "توزيع المشاعر",
        "positive": "إيجابي",
        "negative": "سلبي",
        "neutral": "محايد",
        "count": "العدد",

        "full_version_only": "🔒 هذه الميزة متوفرة في النسخة الكاملة",
        "demo_badge": "نسخة تجريبية",
    },
    "en": {
        "app_title": "ReviewIQ for Stores — Demo",
        "app_subtitle": "Try basic analysis for your store reviews",
        "language": "Language",
        "settings": "Settings",
        "menu": "Menu",
        "page_analysis": "Analysis",
        "data_source": "Data Source",
        "source_custom": "Custom file (CSV)",
        "upload_file": "Upload file",
        "analyze_btn": "Analyze Reviews",
        "no_data": "No data yet. Upload a CSV file to start.",
        "loading": "Analyzing...",
        "rows_limited": "Only the first 200 reviews were analyzed for performance.",
        "error_file": "Could not read the file. Check the format.",

        "reputation_score": "Reputation Score",
        "total_reviews": "Total Reviews",
        "avg_rating": "Average Rating",
        "negative_pct": "Negative %",
        "positive_pct": "Positive %",

        "keyword_sentiment": "Keyword Sentiment Map",
        "keyword_sentiment_desc": "Most frequent keywords colored by sentiment",
        "critical_reviews_urgent": "Reviews That Need Urgent Reply",
        "critical_word": "Critical word",
        "no_critical": "No critical reviews. Excellent!",

        "complaints": "Top Complaints",
        "praises": "Top Praises",
        "recommendations": "Recommendations",
        "summary": "Summary",
        "sentiment_dist": "Sentiment Distribution",
        "positive": "Positive",
        "negative": "Negative",
        "neutral": "Neutral",
        "count": "Count",

        "full_version_only": "🔒 This feature is available in the full version",
        "demo_badge": "Demo",
    },
}


def t(key: str, lang: str = "ar") -> str:
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)


def sanitize_text(text) -> str:
    if text is None:
        return ""
    s = str(text)
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def find_critical_word(text: str):
    if not text:
        return None
    low = str(text).lower()
    for w in CRITICAL_WORDS_AR:
        if w in low:
            return w
    for w in CRITICAL_WORDS_EN:
        if re.search(r"\b" + re.escape(w) + r"\b", low):
            return w
    return None
