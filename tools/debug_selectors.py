from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import os
from dotenv import load_dotenv

load_dotenv()
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

try:
    driver.get("https://www.flipkart.com/search?q=blush")
    time.sleep(6)
    
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
    
    # Get first product
    container = driver.find_element(By.CSS_SELECTOR, "div[data-id]")
    
    print("\n" + "="*70)
    print("FLIPKART PRODUCT STRUCTURE")
    print("="*70)
    
    html = container.get_attribute("outerHTML")
    print("\nFull HTML (first 5000 chars):")
    print(html[:5000])
    
    print("\n" + "="*70)
    print("FINDING NAME AND PRICE")
    print("="*70)
    
    # Get all text content
    all_text = container.text
    print(f"\nAll text from container:\n{all_text}")
    
    # Try to find all span elements
    spans = container.find_elements(By.CSS_SELECTOR, "span")
    print(f"\n✓ Found {len(spans)} span elements")
    
    # Try to find all div elements
    divs = container.find_elements(By.CSS_SELECTOR, "div")
    print(f"✓ Found {len(divs)} div elements")
    
    # Look for text that looks like a price (contains ₹ or is a number)
    print("\n" + "="*70)
    print("POTENTIAL PRICE CANDIDATES:")
    print("="*70)
    
    for i, elem in enumerate(spans[:20]):
        text = elem.text.strip()
        if text and ('₹' in text or text[0].isdigit()):
            classes = elem.get_attribute("class") or "no-class"
            print(f"{i}. [{classes}]: {text}")
    
    # Look for image alt (which has the name)
    print("\n" + "="*70)
    print("IMAGE DETAILS:")
    print("="*70)
    
    img = container.find_element(By.CSS_SELECTOR, "img")
    alt = img.get_attribute("alt")
    src = img.get_attribute("src")
    
    print(f"Alt text: {alt}")
    print(f"Src: {src[:60]}")
    
    # Parse with BeautifulSoup to see class names
    soup = BeautifulSoup(html, 'html.parser')
    
    print("\n" + "="*70)
    print("ALL UNIQUE CLASSES:")
    print("="*70)
    
    classes_set = set()
    for elem in soup.find_all(True):
        if elem.get('class'):
            for cls in elem.get('class'):
                classes_set.add(cls)
    
    print("\nAll classes found:")
    for cls in sorted(classes_set)[:50]:
        print(f"  - {cls}")
    
    input("\nPress Enter to close...")
    
finally:
    driver.quit()