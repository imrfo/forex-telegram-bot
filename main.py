import feedparser
import re

RSS_URL = "https://www.forexlive.com/feed/"


# =========================
# Keywords
# =========================

MACRO_KEYWORDS = [
    "fed",
    "federal reserve",
    "fomc",
    "ecb",
    "european central bank",
    "boe",
    "bank of england",
    "boj",
    "bank of japan",
    "central bank",
    "interest rate",
    "rate decision",
    "rate cut",
    "rate hike",
    "rate check",
    "rate expectations",
    "inflation",
    "cpi",
    "core cpi",
    "pce",
    "core pce",
    "nfp",
    "nonfarm payroll",
    "payrolls",
    "employment",
    "unemployment",
    "jobless claims",
    "initial claims",
    "jobs report",
    "gdp",
    "pmi",
    "manufacturing",
    "services pmi",
    "retail sales",
    "industrial production",
    "consumer confidence",
    "consumer sentiment",
    "ppi",
    "jolts",
    "adp",
    "wages",
    "average hourly earnings",
    "durable goods",
    "housing starts",
    "building permits",
    "trade balance",
    "current account",
    "capacity utilization",
    "intervention",
]


FOREX_KEYWORDS = [
    "forex",
    "fx",
    "usd",
    "eur",
    "gbp",
    "jpy",
    "chf",
    "cad",
    "aud",
    "nzd",
    "yen",
    "dollar/yen",
    "euro/dollar",
    "pound/dollar",

    # Standard Forex pairs
    "eur/usd",
    "gbp/usd",
    "usd/jpy",
    "usd/chf",
    "usd/cad",
    "aud/usd",
    "nzd/usd",
    "eur/gbp",
    "eur/jpy",
    "gbp/jpy",

    # Compact pair names often used in headlines
    "eurusd",
    "gbpusd",
    "usdjpy",
    "usdchf",
    "usdcad",
    "audusd",
    "nzdusd",
    "eurjpy",
    "gbpjpy",

    "currency pair",
]


COMMODITY_KEYWORDS = [
    "gold",
    "xau",
    "xau/usd",
    "oil",
    "crude",
    "brent",
    "wti",
]


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
    "zcash",
    "crypto",
    "cryptocurrency",
    "blockchain",
    "stablecoin",
    "defi",
    "altcoin",
    "token",
    "binance",
    "coinbase",
    "usdt",
    "usdc",
]


STOCK_ONLY_KEYWORDS = [
    "nasdaq",
    "dow jones",
    "s&p 500",
    "s&p500",
    "stock market",
    "stocks",
    "equities",
    "shares",
]


# =========================
# Helper
# =========================

def keyword_exists(text, keyword):
    """
    Checks whether a keyword exists as a real word/phrase.
    This prevents things like 'eth' matching inside 'technical'.
    """

    text = text.lower()
    keyword = keyword.lower()

    # Short keywords must be complete words.
    if len(keyword) <= 4:
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(keyword)
            + r"(?![a-z0-9])"
        )
        return re.search(pattern, text) is not None

    return keyword in text


def find_matches(text, keywords):
    matches = []

    for keyword in keywords:
        if keyword_exists(text, keyword):
            matches.append(keyword)

    return matches


# =========================
# Classification
# =========================

def classify_news(title, summary):

    # IMPORTANT:
    # Classification is based mainly on the TITLE.
    # We intentionally do NOT use the RSS summary here.

    title_text = title.lower()

    macro_matches = find_matches(
        title_text,
        MACRO_KEYWORDS
    )

    forex_matches = find_matches(
        title_text,
        FOREX_KEYWORDS
    )

    commodity_matches = find_matches(
        title_text,
        COMMODITY_KEYWORDS
    )

    crypto_matches = find_matches(
        title_text,
        CRYPTO_KEYWORDS
    )

    stock_matches = find_matches(
        title_text,
        STOCK_ONLY_KEYWORDS
    )


    # =========================
    # Stock-only exclusion
    # =========================

    # If the title is clearly about stocks/equities
    # and does NOT explicitly mention Forex, Crypto,
    # Gold/Oil, then ignore it.

    if stock_matches and not (
        crypto_matches
        or commodity_matches
        or forex_matches
    ):
        return None, [], [], [], [], []


    categories = []


    # =========================
    # Crypto
    # =========================

    if crypto_matches:
        categories.append("CRYPTO")


    # =========================
    # Gold / Oil
    # =========================

    if commodity_matches:
        categories.append("GOLD/OIL")


    # =========================
    # Forex
    # =========================

    if forex_matches:
        categories.append("FOREX")


    # =========================
    # Macro
    # =========================

    if macro_matches:
        categories.append("MACRO")


    # =========================
    # No relevant category
    # =========================

    if not categories:
        return None, [], [], [], [], []


    return (
        " + ".join(categories),
        categories,
        macro_matches,
        forex_matches,
        commodity_matches,
        crypto_matches,
    )


# =========================
# Read RSS
# =========================

feed = feedparser.parse(RSS_URL)

print("===================================")
print("Forex + Crypto News Filter Test")
print("===================================")

print(f"Total RSS items: {len(feed.entries)}")
print()

relevant_count = 0


# =========================
# Process news
# =========================

for index, item in enumerate(feed.entries, start=1):

    title = item.get("title", "No title")
    link = item.get("link", "No link")
    published = item.get("published", "No date")
    summary = item.get("summary", "")

    result = classify_news(title, summary)

    category = result[0]
    categories = result[1]
    macro_matches = result[2]
    forex_matches = result[3]
    commodity_matches = result[4]
    crypto_matches = result[5]

    # Ignore irrelevant news
    if category is None:
        continue

    relevant_count += 1


    # =========================
    # Priority
    # =========================

    if "MACRO" in categories:
        priority = "HIGH"

    elif len(categories) >= 2:
        priority = "HIGH"

    else:
        priority = "MEDIUM"


    # =========================
    # Print result
    # =========================

    print("-----------------------------------")
    print(f"#{relevant_count}")
    print(f"Title: {title}")
    print(f"Category: {category}")
    print(f"Priority: {priority}")


    all_matches = (
        macro_matches
        + forex_matches
        + commodity_matches
        + crypto_matches
    )

    print(
        "Matched keywords:",
        ", ".join(all_matches)
        if all_matches
        else "None"
    )

    print(f"Date: {published}")
    print(f"Link: {link}")
    print()


print("===================================")
print("Filter Test Finished")
print(
    f"Relevant news: "
    f"{relevant_count} / {len(feed.entries)}"
)
print("===================================")
