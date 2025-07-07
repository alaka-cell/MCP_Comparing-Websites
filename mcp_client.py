import os, json, time, traceback, subprocess
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
import requests
from ollama import Client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from utils.logger import logger
from difflib import SequenceMatcher

load_dotenv()

BLACKLIST = {
    "black", "white", "red", "blue", "green", "pink", "purple", "orange", "yellow",
    "xl", "l", "s", "m", "xxl", "hydrating", "refreshing", "glow", "classic",
    "combo", "pack", "kit", "style", "for", "with", "set", "edition", "cream", "gel"
}

def normalize_name(name: str) -> str:
    if not name:
        return ""
    words = name.lower().split()
    return " ".join([w for w in words if w not in BLACKLIST])

class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.llm = Client(host="http://localhost:11434")
        self.model = "mistral"
        self.logger = logger

    async def connect_to_server(self, script: str):
        try:
            cmd = "python" if script.endswith(".py") else "node"
            params = StdioServerParameters(command=cmd, args=[script], env=os.environ.copy())
            self.session = await self.exit_stack.enter_async_context(stdio_client(params))
            self.logger.info("Connected to MCP server.")
            return True
        except Exception:
            self.logger.error("MCP connection failed:")
            self.logger.error(traceback.format_exc())
            return False

    async def cleanup(self):
        await self.exit_stack.aclose()
        self.logger.info("Resources cleaned up successfully.")

    def calculate_match(self, names: list[str], keyword: str) -> float:
        try:
            if not names or not keyword:
                return 0.0
            keyword_norm = normalize_name(keyword).lower()
            match_count = 0
            for name in names:
                norm_name = normalize_name(name).lower()
                if keyword_norm in norm_name:
                    match_count += 1
                elif len(keyword_norm) <= 6:
                    if keyword_norm in name.lower() or SequenceMatcher(None, keyword_norm, norm_name).ratio() > 0.4:
                        match_count += 1
                else:
                    if SequenceMatcher(None, keyword_norm, norm_name).ratio() > 0.5:
                        match_count += 1
            return round((match_count / len(names)) * 100, 2)
        except Exception as e:
            self.logger.error("Match calculation failed: " + str(e))
            return 0.0

    def is_similar(self, a: str, b: str, threshold: float = 0.5) -> bool:
        return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio() >= threshold

    def dedupe(self, products: list[dict], limit: int = 5) -> list:
        seen = set()
        unique = []
        for p in products:
            name = normalize_name(p.get("name", ""))
            if name not in seen:
                seen.add(name)
                unique.append(p)
            if len(unique) >= limit:
                break
        return unique

    def scrape_combined_subprocess(self, keyword: str) -> dict:
        try:
            result = subprocess.run(
                ["python", "tools/scraper.py", keyword],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.stderr:
                self.logger.warning(f"[SCRAPER STDERR] {result.stderr.strip()}")

            raw_output = result.stdout.strip()
            self.logger.info(f"[SCRAPER RAW OUTPUT] {raw_output}")

            if not raw_output.startswith("{"):
                self.logger.error("[SCRAPER ERROR] Output not JSON: " + raw_output)
                return {"myntra": [], "ajio": [], "nykaa": [], "amazon": []}

            return json.loads(raw_output)
        except Exception as e:
            self.logger.error("Scraper error: " + str(e))
            return {"myntra": [], "ajio": [], "nykaa": [], "amazon": []}

    def generate_summary(self, keyword: str, myntra: list, ajio: list, nykaa: list, amazon: list) -> str:
        try:
            prompt = (
                f"Compare top products for '{keyword}' from Myntra, AJIO, Nykaa and Amazon.\n"
                f"Myntra: {[p['name'] for p in myntra]}\n"
                f"AJIO: {[p['name'] for p in ajio]}\n"
                f"Nykaa: {[p['name'] for p in nykaa]}\n"
                f"Amazon: {[p['name'] for p in amazon]}\n"
                "Summarize the key differences in 1-2 lines."
            )
            result = self.llm.generate(model=self.model, prompt=prompt, stream=False)
            return result.get("response", "No response.")
        except Exception as e:
            self.logger.error("Summary error: " + str(e))
            return "Summary unavailable."

    def get_serper_info(self, keyword: str):
        try:
            hdr = {
                "X-API-KEY": os.getenv("SERPER_API_KEY"),
                "Content-Type": "application/json"
            }
            resp = requests.post("https://google.serper.dev/search", json={"q": keyword}, headers=hdr)
            return [{"title": i.get("title"), "link": i.get("link")} for i in resp.json().get("organic", [])][:5]
        except Exception as e:
            self.logger.error("Serper error: " + str(e))
            return []

    def match_products_across_sites(self, myntra, ajio, nykaa, amazon):
        matched = []
        all_products = []

        for site, products in [("myntra", myntra), ("ajio", ajio), ("nykaa", nykaa), ("amazon", amazon)]:
            for p in products:
                p["source"] = site
                all_products.append(p)

        seen = set()
        for i, p1 in enumerate(all_products):
            if i in seen or not p1.get("name"):
                continue
            group = {"myntra": None, "ajio": None, "nykaa": None, "amazon": None}
            group[p1["source"]] = p1
            seen.add(i)
            for j, p2 in enumerate(all_products[i + 1:], start=i + 1):
                if j in seen or not p2.get("name"):
                    continue
                if self.is_similar(p1["name"], p2["name"]):
                    group[p2["source"]] = p2
                    seen.add(j)
            if sum(1 for v in group.values() if v) >= 2:
                matched.append(group)
        return matched

    def compare_sites(self, keyword: str) -> dict:
        try:
            start_scrape = time.time()
            raw = self.scrape_combined_subprocess(keyword)
            scrape_time = round(time.time() - start_scrape, 2)
            self.logger.info(f"[TIMER] Scraper took {scrape_time}s")

            myntra = raw.get("myntra", [])
            ajio = raw.get("ajio", [])
            nykaa = raw.get("nykaa", [])
            amazon = raw.get("amazon", [])
        except Exception as e:
            self.logger.error("Scraping failed: " + str(e))
            myntra = ajio = nykaa = amazon = []
            scrape_time = 0.0

        myntra_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in myntra if p.get("name")]
        ajio_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in ajio if p.get("name")]
        nykaa_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in nykaa if p.get("name")]
        amazon_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in amazon if p.get("name")]

        start_match = time.time()
        myntra_match = self.calculate_match(myntra_names, keyword)
        ajio_match = self.calculate_match(ajio_names, keyword)
        nykaa_match = self.calculate_match(nykaa_names, keyword)
        amazon_match = self.calculate_match(amazon_names, keyword)
        match_time = round(time.time() - start_match, 2)
        self.logger.info(f"[TIMER] Match calculation took {match_time}s")

        start_summary = time.time()
        summary = self.generate_summary(keyword, myntra[:3], ajio[:3], nykaa[:3], amazon[:3])
        summary_time = round(time.time() - start_summary, 1)
        self.logger.info(f"[TIMER] Summary generation took {summary_time}s")

        start_serper = time.time()
        serper = self.get_serper_info(f"{keyword} site:myntra.com OR site:ajio.com OR site:nykaa.com OR site:amazon.in")
        serper_time = round(time.time() - start_serper, 2)
        self.logger.info(f"[TIMER] Serper search took {serper_time}s")

        matched = self.match_products_across_sites(myntra, ajio, nykaa, amazon)

        return {
            "myntra_match": myntra_match,
            "ajio_match": ajio_match,
            "nykaa_match": nykaa_match,
            "amazon_match": amazon_match,
            "myntra_total": len(myntra),
            "ajio_total": len(ajio),
            "nykaa_total": len(nykaa),
            "amazon_total": len(amazon),
            "summary": summary,
            "matched_products": matched,
            "serper_links": serper,
            "top_myntra": myntra[:5],
            "top_ajio": ajio[:5],
            "top_nykaa": nykaa[:5],
            "top_amazon": amazon[:5]
        }

    async def process_query(self, query: str):
        self.logger.info(f"Processing keyword: {query}")
        return self.compare_sites(query)
