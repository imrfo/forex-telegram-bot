import feedparser


RSS_URL = "https://www.forexlive.com/feed/"


# کلمات مربوط به اقتصاد کلان و بانک‌های مرکزی
HIGH_PRIORITY_KEYWORDS = [
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
]


# کلمات مربوط به ارزها و بازارهای مورد نظر ما
MARKET_KEYWORDS = [
    "usd",
    "eur",
    "gbp",
    "jpy",
    "chf",
    "cad",
    "aud",
    "nzd",
    "forex",
    "fx",
    "currency",
    "eur/usd",
    "usd/jpy",
    "gbp/usd",
    "usd/chf",
    "usd/cad",
    "aud/usd",
    "nzd/usd",
    "gold",
    "oil",
    "crude",
]


def contains_keyword(text, keywords):
    """
    بررسی می‌کند آیا یکی از کلمات موردنظر
    در متن خبر وجود دارد یا نه.
    """
    text = text.lower()

    for keyword in keywords:
        if keyword.lower() in text:
            return True

    return False


def get_priority(title, summary):
    """
    یک اولویت اولیه برای خبر مشخص می‌کند.
    این هنوز تحلیل هوش مصنوعی نیست.
    """

    text = f"{title} {summary}".lower()

    high_matches = []
    market_matches = []

    for keyword in HIGH_PRIORITY_KEYWORDS:
        if keyword.lower() in text:
            high_matches.append(keyword)

    for keyword in MARKET_KEYWORDS:
        if keyword.lower() in text:
            market_matches.append(keyword)

    if high_matches:
        priority = "HIGH"
    elif market_matches:
        priority = "MEDIUM"
    else:
        priority = "IGNORE"

    return priority, high_matches, market_matches


# دریافت اخبار
feed = feedparser.parse(RSS_URL)


print("===================================")
print("Forex News Filter Test")
print("===================================")
print(f"Total RSS items: {len(feed.entries)}")
print()


relevant_count = 0


for index, item in enumerate(feed.entries, start=1):

    title = item.get("title", "No title")
    link = item.get("link", "No link")
    published = item.get("published", "No date")
    summary = item.get("summary", "")

    priority, high_matches, market_matches = get_priority(
        title,
        summary
    )

    # فقط خبرهای مرتبط را نمایش بده
    if priority == "IGNORE":
        continue

    relevant_count += 1

    print("-----------------------------------")
    print(f"News #{relevant_count}")
    print(f"Priority: {priority}")
    print(f"Title: {title}")
    print(f"Date: {published}")
    print(f"Link: {link}")

    if high_matches:
        print(f"Macro keywords: {', '.join(high_matches)}")

    if market_matches:
        print(f"Market keywords: {', '.join(market_matches)}")

    print()


print("===================================")
print(f"Relevant news: {relevant_count}")
print("===================================")
