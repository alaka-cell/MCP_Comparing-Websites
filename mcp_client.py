import os
import json
import time
import traceback
import subprocess
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

            self.logger.info(f"[MATCH DEBUG] Keyword Norm: '{keyword_norm}'")

            for name in names:
                norm_name = normalize_name(name).lower()
                self.logger.info(f"[MATCH DEBUG] Checking: '{norm_name}'")

                if keyword_norm in norm_name:
                    match_count += 1
                elif len(keyword_norm) <= 6:
                    if keyword_norm in name.lower() or SequenceMatcher(None, keyword_norm, norm_name).ratio() > 0.4:
                        match_count += 1
                else:
                    if SequenceMatcher(None, keyword_norm, norm_name).ratio() > 0.5:
                        match_count += 1

            self.logger.info(f"[MATCH DEBUG] Total Matches: {match_count} out of {len(names)}")

            match_percent = (match_count / len(names)) * 100 if names else 0
            return round(match_percent, 2)

        except Exception as e:
            self.logger.error("Match calculation failed: " + str(e))
            return 0.0

    def is_similar(self, a: str, b: str, threshold: float = 0.7) -> bool:
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
            return json.loads(result.stdout.strip())
        except Exception as e:
            self.logger.error("Scraper error: " + str(e))
            return {"myntra": [], "ajio": []}

    def generate_summary(self, keyword: str, myntra: list, ajio: list) -> str:
        try:
            prompt = (
                f"Compare top products for '{keyword}' from Myntra and AJIO.\n"
                f"Myntra: {[p['name'] for p in myntra]}\n"
                f"AJIO: {[p['name'] for p in ajio]}\n"
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

    def match_products_across_sites(self, myntra, ajio):
        matched = []
        for m in myntra:
            for a in ajio:
                if self.is_similar(m.get("name", ""), a.get("name", "")):
                    matched.append({"myntra": m, "ajio": a})
                    break
        return matched

    def compare_sites(self, keyword: str) -> dict:
        try:
            start_scrape = time.time()
            raw = self.scrape_combined_subprocess(keyword)
            scrape_time = round(time.time() - start_scrape, 2)
            self.logger.info(f"[TIMER] Scraper took {scrape_time}s")
            myntra = raw.get("myntra", [])
            ajio = raw.get("ajio", [])
        except Exception as e:
            self.logger.error("Scraping failed: " + str(e))
            myntra, ajio = [], []
            scrape_time = 0.0

        # ✅ Use brand + name for accurate match detection
        myntra_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in myntra if p.get("name")]
        ajio_names = [f"{p.get('brand', '')} {p.get('name', '')}".strip() for p in ajio if p.get("name")]

        start_match = time.time()
        myntra_match = self.calculate_match(myntra_names, keyword)
        ajio_match = self.calculate_match(ajio_names, keyword)
        match_time = round(time.time() - start_match, 2)
        self.logger.info(f"[TIMER] Match calculation took {match_time}s")

        start_summary = time.time()
        summary = self.generate_summary(keyword, myntra[:5], ajio[:5])
        summary_time = round(time.time() - start_summary, 1)
        self.logger.info(f"[TIMER] Summary generation took {summary_time}s")

        start_serper = time.time()
        serper = self.get_serper_info(f"{keyword} site:myntra.com OR site:ajio.com")
        serper_time = round(time.time() - start_serper, 2)
        self.logger.info(f"[TIMER] Serper search took {serper_time}s")

        matched = self.match_products_across_sites(myntra, ajio)

        return {
            "keyword": keyword,
            "myntra_match": myntra_match,
            "ajio_match": ajio_match,
            "myntra_total": len(myntra),
            "ajio_total": len(ajio),
            "top_myntra": self.dedupe(myntra),
            "top_ajio": self.dedupe(ajio),
            "matched_products": matched,
            "summary": summary,
            "serper_links": serper,
            "timing": {
                "scraper": scrape_time,
                "match_calc": match_time,
                "summary": summary_time,
                "serper": serper_time
            }
        }

    async def process_query(self, query: str):
        self.logger.info(f"Processing keyword: {query}")
        return self.compare_sites(query)
