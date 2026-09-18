import feedparser


RSS_URL = "https://www.forexlive.com/feed/"


# ==============================
# 1. اقتصاد کلان و بانک‌های مرکزی
# ==============================

MACRO_KEYWORDS = [
    "federal reserve",
    "fed",
    "ecb",
    "european central bank",
    "boe",
    "bank of england",
    "boj",
    "bank of japan",
    "interest rate",
    "interest rates",
    "rate decision",
    "rate cut",
    "rate hike",
    "cpi",
    "pce",
    "nfp",
    "nonfarm payroll",
    "employment",
    "unemployment",
    "gdp",
    "pmi",
    "inflation",
    "central bank",
    "monetary policy",
]


# ==============================
# 2. فارکس و ارزها
# ==============================

FOREX_KEYWORDS = [
    "forex",
    "fx",
    "currency",
    "usd",
    "eur",
    "gbp",
    "jpy",
    "chf",
    "cad",
    "aud",
    "nzd",
    "eur/usd",
    "usd/jpy",
    "gbp/usd",
    "usd/chf",
    "usd/cad",
    "aud/usd",
    "nzd/usd",
]


# ==============================
# 3. طلا و نفت
# ==============================

COMMODITY_KEYWORDS = [
    "gold",
    "xau",
    "xau/usd",
    "oil",
    "crude",
    "brent",
    "wti",
]


# ==============================
# 4. کریپتو
# ==============================

CRYPTO_KEYWORDS = [
    "bitcoin",
    "btc",
    "ethereum",
    "eth",
    "solana",
    "sol",
    "xrp",
    "ripple",
    "cardano",
    "ada",
    "dogecoin",
    "doge",
    "binance",
    "coinbase",
    "crypto",
    "cryptocurrency",
    "blockchain",
    "stablecoin",
    "defi",
    "altcoin",
    "token",
    "zcash",
    "usdt",
    "usdc",
]


# ==============================
# 5. موضوعاتی که معمولاً
#    برای کانال ما اولویت ندارند
# ==============================

EXCLUDE_KEYWORDS = [
    "nasdaq",
    "dow jones",
    "s&p 500",
    "sp500",
    "stock market",
    "stocks",
    "equities",
    "shares",
]


def find_matches(text, keywords):
    """
    تمام کلمات پیدا شده در متن را برمی‌گرداند.
    """

    text = text.lower()

    matches = []

    for keyword in keywords:
        if keyword.lower() in text:
            matches.append(keyword)

    return matches


def classify_news(title, summary):
    """
    خبر را در یکی از دسته‌های اصلی قرار می‌دهد.
    """

    text = f"{title} {summary}".lower()

    macro_matches = find_matches(text, MACRO_KEYWORDS)
    forex_matches = find_matches(text, FOREX_KEYWORDS)
    commodity_matches = find_matches(text, COMMODITY_KEYWORDS)
    crypto_matches = find_matches(text, CRYPTO_KEYWORDS)
    exclude_matches = find_matches(text, EXCLUDE_KEYWORDS)

    # ------------------------------
    # تشخیص دسته اصلی
    # ------------------------------

    categories = []

    if macro_matches:
        categories.append("MACRO")

    if forex_matches:
        categories.append("FOREX")

    if commodity_matches:
        categories.append("GOLD/OIL")

    if crypto_matches:
        categories.append("CRYPTO")

    # ------------------------------
    # اگر هیچ موضوع مرتبطی نبود
    # ------------------------------

    if not categories:
        return None, [], [], [], [], exclude_matches

    # ------------------------------
    # اگر خبر کریپتو است و موضوع
    # دیگری ندارد، آن را Crypto بدان
    # ------------------------------

    if crypto_matches and not macro_matches and not forex_matches:
        category = "CRYPTO"

    # ------------------------------
    # اگر خبر طلا/نفت است
    # ------------------------------

    elif commodity_matches and not macro_matches and not forex_matches:
        category = "GOLD/OIL"

    # ------------------------------
    # اگر خبر فارکس یا اقتصاد کلان است
    # ------------------------------

    elif macro_matches and forex_matches:
        category = "MACRO + FOREX"

    elif macro_matches:
        category = "MACRO"

    elif forex_matches:
        category = "FOREX"

    else:
        category = "OTHER"

    # ------------------------------
    # تعیین اولویت اولیه
    # ------------------------------

    if macro_matches:
        priority = "HIGH"

    elif forex_matches or commodity_matches:
        priority = "MEDIUM"

    elif crypto_matches:
        priority = "MEDIUM"

    else:
        priority = "LOW"

    # ------------------------------
    # اگر خبر صرفاً درباره سهام بود
    # ولی هیچ موضوع اصلی نداشت،
    # آن را حذف کن
    # ------------------------------

    if exclude_matches and not (
        macro_matches
        or forex_matches
        or commodity_matches
        or crypto_matches
    ):
        return None, [], [], [], [], exclude_matches

    return (
        category,
        macro_matches,
        forex_matches,
        commodity_matches,
        crypto_matches,
        exclude_matches,
        priority,
    )


# ==============================
# دریافت RSS
# ==============================

feed = feedparser.parse(RSS_URL)


print("===================================")
print("Forex + Crypto News Filter Test")
print("===================================")

print(f"Total RSS items: {len(feed.entries)}")
print()


relevant_count = 0


for item in feed.entries:

    title = item.get("title", "No title")
    link = item.get("link", "No link")
    published = item.get("published", "No date")
    summary = item.get("summary", "")

    result = classify_news(title, summary)

    if result is None:
        continue

    (
        category,
        macro_matches,
        forex_matches,
        commodity_matches,
        crypto_matches,
        exclude_matches,
        priority,
    ) = result

    relevant_count += 1

    print("-----------------------------------")
    print(f"News #{relevant_count}")
    print(f"Priority: {priority}")
    print(f"Category: {category}")
    print(f"Title: {title}")
    print(f"Date: {published}")
    print(f"Link: {link}")

    if macro_matches:
        print(
            f"Macro keywords: {', '.join(macro_matches)}"
        )

    if forex_matches:
        print(
            f"Forex keywords: {', '.join(forex_matches)}"
        )

    if commodity_matches:
        print(
            f"Gold/Oil keywords: {', '.join(commodity_matches)}"
        )

    if crypto_matches:
        print(
            f"Crypto keywords: {', '.join(crypto_matches)}"
        )

    print()


print("===================================")
print(f"Relevant news: {relevant_count}")
print("===================================")
