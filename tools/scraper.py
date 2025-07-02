import json
import sys
import time
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import concurrent.futures

load_dotenv()
API_KEY = os.getenv("SCRAPERAPI_KEY")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

def init_driver(proxy=False):
    options = Options()
    #options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    if proxy and API_KEY:
        proxy_url = f"http://{API_KEY}:scraperapi.proxy:8001"
        options.add_argument(f"--proxy-server={proxy_url}")

    if not CHROMEDRIVER_PATH:
        raise ValueError("CHROMEDRIVER_PATH is not set in the .env file.")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', { get: () => false })"
    })

    return driver

def scrape_myntra(keyword):
    driver = init_driver()
    try:
        query = keyword.replace(" ", "%20")
        url = f"https://www.myntra.com/shoes?rawQuery={query}"
        driver.get(url)

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li.product-base"))
        )
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = []

        for product in soup.select("li.product-base")[:10]:
            brand = product.select_one("h3.product-brand")
            name = product.select_one("h4.product-product")
            price = product.select_one("span.product-discountedPrice") or product.select_one("span.product-price")
            link_tag = product.select_one("a[href]")

            if brand and name and price and link_tag:
                items.append({
                    "name": f"{brand.text.strip()} {name.text.strip()}",
                    "price": price.text.strip(),
                    "link": "https://www.myntra.com" + link_tag["href"]
                })
        return items

    except Exception as e:
        print(f"[MYNTRA] Error while scraping HTML: {e}", file=sys.stderr)
        driver.save_screenshot("myntra_error.png")
        return []
    finally:
        driver.quit()

def scrape_ajio(keyword):
    driver = init_driver()
    try:
        query = keyword.replace(" ", "%20")
        url = f"https://www.ajio.com/search/?text={query}"
        driver.get(url)

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.item"))
        )
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        items = []

        for product in soup.select("div.item")[:10]:
            brand = product.select_one("div.brand")
            name = product.select_one("div.nameCls")
            price = product.select_one("span.price")
            link_tag = product.select_one("a[href]")

            if brand and name and price and link_tag:
                items.append({
                    "name": f"{brand.text.strip()} {name.text.strip()}",
                    "price": price.text.strip(),
                    "link": "https://www.ajio.com" + link_tag["href"]
                })

        return items

    except Exception as e:
        print(f"[AJIO] Error while scraping HTML: {e}", file=sys.stderr)
        driver.save_screenshot("ajio_error.png")
        return []
    finally:
        driver.quit()

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "kurta"

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_myntra = executor.submit(scrape_myntra, keyword)
        future_ajio = executor.submit(scrape_ajio, keyword)

        try:
            myntra_items = future_myntra.result()
        except Exception as e:
            print(f"[MYNTRA] Unexpected error: {e}", file=sys.stderr)
            myntra_items = []

        try:
            ajio_items = future_ajio.result()
        except Exception as e:
            print(f"[AJIO] Unexpected error: {e}", file=sys.stderr)
            ajio_items = []

    output = {
        "myntra": myntra_items,
        "ajio": ajio_items
    }

    print(json.dumps(output, indent=2))
