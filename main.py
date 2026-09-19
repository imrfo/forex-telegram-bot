import os
import re
import time
import feedparser
from google import genai
import requests

RSS_URL = "https://www.forexlive.com/feed/"
SEEN_FILE = "seen_ids.txt"

# خواندن کلیدها از متغیرهای سیستمی GitHub Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "@ForexPersianNews")

# =========================
# Keywords
# =========================

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

# =========================
# File Handlers
# =========================

def load_seen_ids():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_id(news_id):
    with open(SEEN_FILE, "a", encoding="utf-8") as f:
        f.write(f"{news_id}\n")

# =========================
# Helper & Classifier
# =========================

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

def extract_image_url(item):
    """استخراج تصویر خبر از متادیتاها و تگ‌های موجود در فید"""
    # 1. بررسی media_content
    if "media_content" in item and len(item.media_content) > 0:
        url = item.media_content[0].get("url")
        if url:
            return url

    # 2. بررسی media_thumbnail
    if "media_thumbnail" in item and len(item.media_thumbnail) > 0:
        url = item.media_thumbnail[0].get("url")
        if url:
            return url

    # 3. بررسی enclosures
    if "enclosures" in item and len(item.enclosures) > 0:
        url = item.enclosures[0].get("href")
        if url:
            return url

    # 4. جستجو داخل متن و خلاصه خبر برای تگ‌های <img>
    raw_html = item.get("summary", "")
    if "content" in item and len(item.content) > 0:
        raw_html += " " + item.content[0].get("value", "")

    img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', raw_html, re.IGNORECASE)
    for img_url in img_matches:
        if any(ext in img_url.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return img_url

    return None

# =========================
# Gemini AI
# =========================

def generate_persian_post(title, summary, category):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
تو یک تحلیل‌گر و دبیر خبر حرفه‌ای بازار فارکس هستی. برای خبر زیر یک پست تلگرامی فارسی بساز.
تنها از تگ <b> برای بولد کردن تیترها استفاده کن و تگ HTML دیگری به کار نبر.

تیتر خبر: {title}
خلاصه خبر: {summary}
دسته‌بندی: {category}

قالب خروجی دقیقاً به این شکل باشد:
🔴 <b>[تیتر فوری و جذاب فارسی]</b>

📌 <b>خلاصه خبر:</b>
[۲ تا ۳ جمله روان، ساده و دقیق درباره اصل اتفاق]

💡 <b>اثر روی بازار:</b>
[یک خط اثر احتمالی روی نمادها و جفت‌ارزها]

#{category.replace(' + ', ' #').replace('/', '_')} #فارکس
"""
    # استفاده از مدل سریع Flash-Lite با سهمیه رایگان بالا
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt
    )
    
    post_text = response.text.strip()
    post_text += "\n\n🆔 @ForexPersianNews"
    return post_text

# =========================
# Telegram Sender
# =========================

def send_to_telegram(text, image_url=None):
    if image_url:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url,
            "caption": text[:1024],  # سقف طول مجاز کپشن در تلگرام
            "parse_mode": "HTML"
        }
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            return True
        print(f"Failed to send image, falling back to text. Details: {res.text}")

    # در صورت نبود تصویر یا بروز خطا در ارسال تصویر، ارسال متنی انجام می‌شود
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    res = requests.post(url, json=payload, timeout=10)
    if res.status_code != 200:
        print(f"Telegram error response: {res.text}")
        return False
    return True

# =========================
# Main Execution Loop
# =========================

def main():
    seen_ids = load_seen_ids()
    feed = feedparser.parse(RSS_URL)
    print(f"Total items in feed: {len(feed.entries)}")

    processed_count = 0
    MAX_PER_RUN = 2  # ارسال ۲ خبر در هر دوره برای مدیریت مصرف سهمیه

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
            image_url = extract_image_url(item)
            if image_url:
                print(f"Image found: {image_url}")
            else:
                print("No image found, using text format.")

            persian_text = generate_persian_post(title, summary, category)
            success = send_to_telegram(persian_text, image_url)
            
            if success:
                print("-> Sent to Telegram successfully!")
                seen_ids.add(news_id)
                save_seen_id(news_id)
                processed_count += 1
                time.sleep(10)  # وقفه ایمن بین درخواست‌ها
            else:
                print("-> Failed to send to Telegram.")
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            break

if __name__ == "__main__":
    main()
