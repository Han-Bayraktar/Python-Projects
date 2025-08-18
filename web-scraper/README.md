# 📝 Web Scraper (BeautifulSoup)

&#x20;&#x20;

A **Python web scraper** that collects **quotes (text, author, tags)** from [quotes.toscrape.com](https://quotes.toscrape.com) and saves them into a **CSV file**.

---

## 🚀 Installation

```bash
# Optional: create virtual environment
python -m venv .venv

# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🏃 Usage

```bash
# Scrape 2 pages and save results to data.csv
python scraper.py --csv data.csv --limit-pages 2 --delay 1.0

# Scrape all pages (no page limit, polite 1s delay)
python scraper.py --csv data.csv --delay 1.0
```

---

## ⚠️ Ethical & Legal Notice

- ✅ Always check the target website’s **robots.txt** and **Terms of Service**
- ✅ Do not overload servers – use a **delay** between requests
- ✅ Collect only data you are legally allowed to use
- ⚠️ This project is for **educational purposes** only

---

## 🔧 Adapting to Another Website

1. **Change the base URL**\
   In `scraper.py`:

   ```python
   BASE_URL = "https://quotes.toscrape.com"
   ```

2. **Update the parsing logic**\
   Modify `parse_quotes` to match the new site’s HTML structure. Example for products:

   ```python
   def parse_items(html: str):
       soup = BeautifulSoup(html, "lxml")
       items = []
       for p in soup.select(".product"):
           title = p.select_one(".title")
           price = p.select_one(".price")
           items.append({
               "title": title.get_text(strip=True) if title else "",
               "price": price.get_text(strip=True) if price else "",
           })
       return items, None
   ```

3. **Adjust CSV fields**\
   The keys in `items.append({ ... })` will be used as CSV column headers.

---
