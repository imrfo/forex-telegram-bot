import os
import re
import time
import feedparser
from google import genai
import requests

RSS_URL = "https://www.forexlive.com/feed/"
SEEN_FILE = "seen_ids.txt"

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MACRO_KEYWORDS = [
    "fed", "federal reserve", "fomc", "ecb", "european central bank",
    "boe", "bank of england", "boj", "bank of japan", "central bank",
    "interest rate", "rate decision", "rate cut", "rate hike",
    "inflation", "cpi", "core cpi", "pce", "nfp", "nonfarm payroll",
    "payrolls", "employment", "unemployment", "jobless claims",
    "jobs report", "gdp", "pmi", "retail sales", "ppi"
]

FOREX_KEYWORDS = [
    "forex", "fx", "usd", "eur", "gbp", "jpy", "chf", "cad", "aud", "nzd",
    "eur/usd", "gbp/usd", "usd/jpy", "usd/chf", "aud/usd", "eurusd", "gbpusd", "usdjpy"
]

COMMODITY_KEYWORDS = ["gold", "xau", "xau/usd", "oil", "crude", "brent", "wti"]
CRYPTO_KEYWORDS = ["bitcoin", "btc", "ethereum", "eth", "crypto", "binance", "solana"]
STOCK_ONLY_KEYWORDS = ["nasdaq", "dow jones", "s&p 500", "s&p500", "stocks", "equities"]

def load_seen_ids():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_id(news_id):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(f"{news_id}\n")

def keyword_exists(text, keyword):
    text = text.lower()
    keyword = keyword.lower()
    if len(keyword) <= 4:
        pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return keyword in text

def find_matches(text, keywords):
    return [kw for kw in keywords if keyword_exists(text, kw)]

def classify_news(title):
    title_text = title.lower()
    macro_matches = find_matches(title_text, MACRO_KEYWORDS)
    forex_matches = find_matches(title_text, FOREX_KEYWORDS)
    commodity_matches = find_matches(title_text, COMMODITY_KEYWORDS)
    crypto_matches = find_matches(title_text, CRYPTO_KEYWORDS)
    stock_matches = find_matches(title_text, STOCK_ONLY_KEYWORDS)

    if stock_matches and not (crypto_matches or commodity_matches or forex_matches):
        return None

    categories = []
    if crypto_matches: categories.append("CRYPTO")
    if commodity_matches: categories.append("GOLD/OIL")
    if forex_matches: categories.append("FOREX")
    if macro_matches: categories.append("MACRO")

    return " + ".join(categories) if categories else None

def generate_persian_post(title, summary, category):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
تو یک تحلیل‌گر بازار فارکس هستی. برای این خبر یک پست تلگرامی فارسی بساز.
از به کار بردن تگ‌های HTML غیراستاندارد خودداری کن. تنها از تگ <b> برای بولد کردن استفاده کن.

تیتر: {title}
خلاصه: {summary}
دسته‌بندی: {category}

قالب خروجی دقیقاً به این فرمت باشد:
🔴 <b>[تیتر فوری و جذاب فارسی]</b>

📌 <b>خلاصه خبر:</b>
[۲ تا ۳ جمله روان و کامل فارسی]

💡 <b>اثر روی بازار:</b>
[یک خط درباره دارایی‌ها یا ارزهای متاثر]

#{category.replace(' + ', ' #').replace('/', '_')} #فارکس
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return response.text

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"Telegram error response: {res.text}")
        return False
    return True

def main():
    seen_ids = load_seen_ids()
    feed = feedparser.parse(RSS_URL)
    print(f"Total items in feed: {len(feed.entries)}")

    processed_count = 0
    MAX_PER_RUN = 3  # در هر بار اجرا فقط ۳ خبر جدید ارسال شود تا سقف رایگان پر نشود

    for item in reversed(feed.entries):
        if processed_count >= MAX_PER_RUN:
            print("Reached batch limit for this run.")
            break

        news_id = item.get("id") or item.get("link")
        title = item.get("title", "")
        summary = item.get("summary", "")

        if news_id in seen_ids:
            continue

        category = classify_news(title)
        if not category:
            seen_ids.add(news_id)
            save_seen_id(news_id)
            continue

        print(f"Processing: {title}")
        try:
            persian_text = generate_persian_post(title, summary, category)
            success = send_to_telegram(persian_text)
            
            if success:
                print("-> Sent to Telegram successfully!")
                seen_ids.add(news_id)
                save_seen_id(news_id)
                processed_count += 1
                time.sleep(12)  # وقفه ایمن برای رعایت سقف درخواست
            else:
                print("-> Failed to send to Telegram.")
        except Exception as e:
            print(f"Error calling Gemini: {e}")

if __name__ == "__main__":
    main()
