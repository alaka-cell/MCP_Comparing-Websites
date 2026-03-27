import os
import sys
import json
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")


def init_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver


def scroll_page(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)


def safe_text(element, css):
    try:
        return element.find_element(By.CSS_SELECTOR, css).text.strip()
    except:
        return "-"


def get_image(element):
    try:
        img = element.find_element(By.CSS_SELECTOR, "img")
        src = (
            img.get_attribute("src") or
            img.get_attribute("data-src") or
            img.get_attribute("srcset") or
            img.get_attribute("data-srcset")
        )
        if src and " " in src:
            src = src.split(" ")[0]
        return src or ""
    except:
        return ""


def safe_link(element, css, base=""):
    try:
        link = element.find_element(By.CSS_SELECTOR, css).get_attribute("href")
        if link and link.startswith("/"):
            return base + link
        return link
    except:
        return ""


def scrape_myntra(keyword, max_products=10):
    driver = init_driver()
    results = []
    try:
        driver.get(f"https://www.myntra.com/{keyword.replace(' ', '-')}")
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, "li.product-base")
        for card in cards[:max_products]:
            results.append({
                "brand": safe_text(card, "h3.product-brand"),
                "name": safe_text(card, "h4.product-product"),
                "price": safe_text(card, "span.product-discountedPrice"),
                "image": get_image(card),
                "link": safe_link(card, "a"),
                "source": "myntra"
            })
    finally:
        driver.quit()
    return results


def scrape_amazon(keyword, max_products=10):
    driver = init_driver()
    results = []
    try:
        driver.get(f"https://www.amazon.in/s?k={keyword.replace(' ', '+')}")
        time.sleep(3)
        scroll_page(driver)
        cards = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
        for card in cards:
            name = safe_text(card, "h2 span")
            price = safe_text(card, "span.a-price-whole")
            if name == "-" or price == "-":
                continue
            results.append({
                "brand": name.split()[0],
                "name": name,
                "price": f"₹{price}",
                "image": get_image(card),
                "link": safe_link(card, "h2 a", "https://www.amazon.in"),
                "source": "amazon"
            })
            if len(results) >= max_products:
                break
    finally:
        driver.quit()
    return results


def scrape_flipkart(keyword, max_products=10):
    driver = init_driver()
    results = []
    try:
        driver.get(f"https://www.flipkart.com/search?q={keyword}")
        time.sleep(6)
        try:
            driver.find_element(By.XPATH, "//button[contains(text(),'✕')]").click()
        except:
            pass
        
        for _ in range(3):
            scroll_page(driver)

        # Wait for products to load
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[data-id]")))

        # Find all product containers with data-id
        product_containers = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")
        
        for container in product_containers:
            try:
                # Get the link which contains product details
                link_elem = container.find_element(By.CSS_SELECTOR, "a.GnxRXv")
                
                # Extract href
                link_href = link_elem.get_attribute("href")
                
                # The product name is in the alt text of the image
                img = container.find_element(By.CSS_SELECTOR, "img.UCc1lI")
                name = img.get_attribute("alt") or "-"
                
                # Extract the main product name (first part before "with" or "for")
                if name != "-":
                    # Clean up the name
                    name = name.split("with")[0].strip()
                
                # Price - get all text and find the price
                all_text = container.text
                price = "-"
                
                # Extract price from text (look for ₹ symbol)
                lines = all_text.split('\n')
                for line in lines:
                    if '₹' in line:
                        # Extract price numbers
                        import re
                        matches = re.findall(r'₹(\d+)', line)
                        if matches:
                            # Take the first price (usually the discounted one)
                            price = f"₹{matches[0]}"
                            break
                
                if name == "-" or price == "-":
                    continue

                results.append({
                    "brand": name.split()[0] if name != "-" else "-",
                    "name": name,
                    "price": price,
                    "image": get_image(container),
                    "link": f"https://www.flipkart.com{link_href}" if link_href and link_href.startswith("/") else link_href,
                    "source": "flipkart"
                })

                if len(results) >= max_products:
                    break
            except Exception as e:
                continue

    except Exception as e:
        pass
    finally:
        driver.quit()
    return results


def scrape_nykaa(keyword, max_products=10):
    driver = init_driver()
    results = []
    try:
        driver.get(f"https://www.nykaa.com/search/result/?q={keyword}")
        time.sleep(8)
        
        for _ in range(3):
            scroll_page(driver)

        # Find product wrapper containers
        products = driver.find_elements(By.CSS_SELECTOR, "div.productWrapper")
        
        for product in products:
            try:
                # Get the product link
                link_elem = product.find_element(By.CSS_SELECTOR, "a.css-qlopj4")
                link_href = link_elem.get_attribute("href")
                
                # Get product name from the link or the title div
                name = "-"
                try:
                    name_elem = product.find_element(By.CSS_SELECTOR, "div.css-xrzmfa")
                    name = name_elem.text.strip()
                except:
                    pass
                
                # Get brand - try to extract from name or find brand element
                brand = "-"
                if name != "-":
                    # Brand is usually the first word
                    brand = name.split()[0]
                
                # Get price - look for the discounted price
                price = "-"
                try:
                    price_elem = product.find_element(By.CSS_SELECTOR, "span.css-111z9ua")
                    price = price_elem.text.strip()
                except:
                    try:
                        price_elem = product.find_element(By.CSS_SELECTOR, "span.css-17x46n5 span")
                        price = price_elem.text.strip()
                    except:
                        pass
                
                if name == "-" or price == "-":
                    continue

                results.append({
                    "brand": brand,
                    "name": name,
                    "price": price,
                    "image": get_image(product),
                    "link": f"https://www.nykaa.com{link_href}" if link_href and link_href.startswith("/") else link_href,
                    "source": "nykaa"
                })

                if len(results) >= max_products:
                    break

            except Exception as e:
                continue

    except Exception as e:
        pass
    finally:
        driver.quit()
    return results


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "blush"

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(scrape_myntra, keyword): "myntra",
                executor.submit(scrape_flipkart, keyword): "flipkart",
                executor.submit(scrape_nykaa, keyword): "nykaa",
                executor.submit(scrape_amazon, keyword): "amazon",
            }

            results = {k: [] for k in ["myntra", "flipkart", "nykaa", "amazon"]}

            for future in concurrent.futures.as_completed(futures):
                site = futures[future]
                try:
                    results[site] = future.result()
                except:
                    results[site] = []

        print(json.dumps(results))

    except:
        print(json.dumps({
            "myntra": [],
            "flipkart": [],
            "nykaa": [],
            "amazon": []
        }))