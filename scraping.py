"""
myntra_scraper_playwright.py

Playwright-based scraper for Myntra product listings (Lipstick category).
 - checks robots.txt (will abort if disallowed)
 - scrapes up to MAX_PAGES pages
 - captures JSON XHR responses and falls back to DOM scraping
 - deduplicates and saves to CSV
"""

import re
import time
import random
from urllib.parse import urljoin, urlparse
from datetime import datetime
import urllib.robotparser

import pandas as pd
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# -------- CONFIG --------
BASE_URL = "https://www.myntra.com/personal-care?f=Categories%3ALipstick"
MAX_PAGES = 5
OUTPUT_CSV = "scraped_products.csv"
HEADLESS = True
# polite user agent — replace the email with yours if you intend to run more often
USER_AGENT = "MyScraperBot/1.0 (+mailto:rupsajana1234@gmail.com) Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

# -------- utilities --------
def allowed_by_robots(base_url, user_agent=USER_AGENT):
    parsed = urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception:
        print(f"[!] Could not fetch robots.txt at {robots_url}. Aborting to be safe.")
        return False
    return rp.can_fetch(user_agent, base_url)

def extract_items_from_json(obj):
    results = []
    def looks_like_product(d):
        if not isinstance(d, dict):
            return False
        keys = set(k.lower() for k in d.keys())
        common = {'productid','product_id','id','name','productname','brand','price','searchimage','image','productlink','url'}
        return bool(keys & common)
    queue = [obj]
    while queue:
        node = queue.pop(0)
        if isinstance(node, list):
            if node and isinstance(node[0], dict) and looks_like_product(node[0]):
                for entry in node:
                    if isinstance(entry, dict):
                        results.append(entry)
            else:
                for elem in node:
                    if isinstance(elem, (dict, list)):
                        queue.append(elem)
        elif isinstance(node, dict):
            if looks_like_product(node):
                results.append(node)
            for v in node.values():
                if isinstance(v, (dict, list)):
                    queue.append(v)
    return results

def normalize_product_dict(raw):
    get = lambda *keys: next((raw[k] for k in keys if k in raw and raw.get(k) not in (None, "")), None)
    name = get('productName','name','title','displayName','product_title') or ""
    brand = get('brand','brandName','productBrand') or ""
    price = get('price','sellingPrice','mrp','finalPrice','minPrice','offerPrice','amount')
    if isinstance(price, dict):
        price = price.get('value') or price.get('amount') or price.get('mrp')
    image = get('searchImage','image','searchImages','images')
    if isinstance(image, list):
        image = image[0] if image else ""
    prod_id = get('productId','id','product_id')
    product_url = get('product_url','url','link','productLink') or ""
    if product_url and isinstance(product_url, str) and product_url.startswith("/"):
        product_url = urljoin("https://www.myntra.com", product_url)
    if not product_url and prod_id:
        product_url = f"https://www.myntra.com/product/{prod_id}"
    rating = get('rating','avgRating','ratingScore') or ""
    desc = get('description','productDescription','shortDescription') or ""

    # clean price
    price_value = 0.0
    try:
        if price is not None:
            if isinstance(price, (int,float)):
                price_value = float(price)
            else:
                s = re.sub(r'[^\d.]', '', str(price))
                price_value = float(s) if s else 0.0
    except Exception:
        price_value = 0.0

    return {
        "product_name": (name or "").strip(),
        "brand": (brand or "").strip(),
        "price": price_value,
        "rating": str(rating).strip(),
        "product_url": product_url or "",
        "image_url": image or "",
        "breadcrumbs": "Home / Personal Care / Lipstick",
        "description": (desc or "").strip(),
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# -------- scraper --------
def scrape_myntra(base_url=BASE_URL, max_pages=MAX_PAGES):
    if not allowed_by_robots(base_url):
        print("[!] robots.txt disallows scraping this path or robots.txt couldn't be read. Exiting.")
        return []

    collected = []
    json_responses = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(user_agent=USER_AGENT, locale="en-US")
        page = context.new_page()

        def on_response(response):
            try:
                url = response.url
                ct = response.headers.get("content-type","")
                if ("application/json" in ct) or any(x in url.lower() for x in ("search","products","gateway","catalog","listing","api")):
                    try:
                        body = response.json()
                        if body:
                            json_responses.append((url, body))
                    except Exception:
                        pass
            except Exception:
                pass

        page.on("response", on_response)

        try:
            print(f"[+] Loading: {base_url}")
            page.goto(base_url, timeout=60000)
            time.sleep(random.uniform(1.5, 3.0))
        except PWTimeoutError as e:
            print(f"[!] Timeout loading initial page: {e}")

        parsed = urlparse(base_url)
        base_query = parsed.query
        for pnum in range(1, max_pages + 1):
            if "p=" in base_query:
                new_q = re.sub(r'p=\d+', f'p={pnum}', base_query)
                paged = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_q}"
            else:
                sep = '&' if base_query else '?'
                paged = base_url + f"{sep}p={pnum}"

            try:
                print(f"[+] Visiting page {pnum}: {paged}")
                page.goto(paged, timeout=60000)
                time.sleep(random.uniform(1.5, 4.0))
            except Exception as e:
                print(f"[!] Navigation to {paged} failed: {e}")
                time.sleep(min(10, 2 ** min(pnum,4)))

        print(f"[+] Processing {len(json_responses)} captured JSON responses...")
        for url, body in json_responses:
            try:
                items = extract_items_from_json(body)
                for raw in items:
                    rec = normalize_product_dict(raw)
                    if rec.get("product_name"):
                        collected.append(rec)
            except Exception:
                continue

        if not collected or len(collected) < 10:
            print("[+] Falling back to DOM scraping of product cards.")
            card_selectors = [
                ".product-base", ".product", ".product-card", ".product-grid",
                ".product-listing", ".productItem", ".product-item", ".grid-product", "li.product"
            ]
            seen_cards = 0
            for sel in card_selectors:
                try:
                    elems = page.query_selector_all(sel)
                except Exception:
                    elems = []
                if not elems:
                    continue
                print(f"[+] Found {len(elems)} elements for selector {sel}")
                for el in elems:
                    try:
                        name_el = el.query_selector(".product-product, .product-title, .productName, .product-name")
                        brand_el = el.query_selector(".product-brand, .productBrand")
                        price_el = el.query_selector(".product-discountedPrice, .price, .product-price")
                        link_el = el.query_selector("a")
                        img_el = el.query_selector("img")

                        name = name_el.inner_text().strip() if name_el else ""
                        brand = brand_el.inner_text().strip() if brand_el else ""
                        price_text = price_el.inner_text().strip() if price_el else ""
                        link = link_el.get_attribute("href") if link_el else ""
                        image = ""
                        if img_el:
                            image = img_el.get_attribute("src") or img_el.get_attribute("data-src") or ""

                        price_value = 0.0
                        if price_text:
                            s = re.sub(r'[^\d.]', '', price_text)
                            price_value = float(s) if s else 0.0

                        product_url = urljoin("https://www.myntra.com", link) if link and link.startswith("/") else (link or "")
                        collected.append({
                            "product_name": name,
                            "brand": brand,
                            "price": price_value,
                            "rating": "",
                            "product_url": product_url,
                            "image_url": image or "",
                            "breadcrumbs": "Home / Personal Care / Lipstick",
                            "description": "",
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    except Exception:
                        continue
                seen_cards += len(elems)
                if seen_cards >= 200:
                    break

        browser.close()

    # dedupe
    unique = []
    seen = set()
    for it in collected:
        key = (it.get("product_url") or (it.get("product_name","") + "|" + it.get("brand",""))).strip()
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append(it)

    print(f"[+] Collected {len(collected)} items; {len(unique)} unique after dedupe.")
    return unique

# -------- CSV export --------
def save_to_csv(items, filename=OUTPUT_CSV):
    if not items:
        print("[!] No items to save.")
        return
    df = pd.DataFrame(items)
    cols = ["product_name","brand","price","rating","product_url","image_url","breadcrumbs","description","scraped_at"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df = df[cols]
    df.to_csv(filename, index=False)
    print(f"[+] Saved {len(df)} products to {filename}")

# -------- main --------
if __name__ == "__main__":
    print("[*] Starting scraper for:", BASE_URL)
    items = scrape_myntra()
    save_to_csv(items)
    print("[*] Done.")
