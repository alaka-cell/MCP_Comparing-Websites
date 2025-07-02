import required files 
import selenium (uv add selenium) 
...
from dotenv import load_dotenv


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

def required_website():
    ...

def other_required_website():
    ...

if __name__ == "__main__":
        args 

....


