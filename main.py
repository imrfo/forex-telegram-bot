import feedparser

RSS_URL = "https://www.forexlive.com/feed/"

feed = feedparser.parse(RSS_URL)

print("===================================")
print("Forex News RSS Test")
print("===================================")
print(f"Number of items: {len(feed.entries)}")
print()

for index, item in enumerate(feed.entries[:10], start=1):
    title = item.get("title", "No title")
    link = item.get("link", "No link")
    published = item.get("published", "No date")

    print(f"{index}. {title}")
    print(f"   Date: {published}")
    print(f"   Link: {link}")
    print()
