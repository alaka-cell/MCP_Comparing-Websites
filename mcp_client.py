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

load_dotenv()

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

    def calculate_match(self, names, keyword):
        kw_tokens = keyword.lower().split()
        matches = [n for n in names if any(tok in n.lower() for tok in kw_tokens)]
        return round(len(matches) / len(names) * 100, 2) if names else 0.0

    def get_serper_info(self, keyword: str):
        try:
            hdr = {
                "X-API-KEY": os.getenv("SERPER_API_KEY"),
                "Content-Type": "application/json"
            }
            start = time.time()
            resp = requests.post("https://google.serper.dev/search", json={"q": keyword}, headers=hdr)
            self.logger.info(f"[TIMER] Serper search took {time.time() - start:.2f}s")
            return [
                {"title": i.get("title"), "link": i.get("link")}
                for i in resp.json().get("organic", [])
            ][:5]
        except Exception as e:
            self.logger.error("Serper error: " + str(e))
            return []

    def generate_summary(self, keyword: str, myntra, ajio) -> str:
        try:
            prompt = (
                f"Compare top products for '{keyword}' from Myntra and AJIO.\n"
                f"Myntra: {[p['name'] for p in myntra]}\n"
                f"AJIO: {[p['name'] for p in ajio]}\n"
                "Summarize the key differences in 2-3 lines."
            )
            start = time.time()
            result = self.llm.generate(model=self.model, prompt=prompt, stream=False)
            self.logger.info(f"[TIMER] Summary generation took {time.time() - start:.2f}s")
            return result.get("response", "No response.")
        except Exception as e:
            self.logger.error("Summary error: " + str(e))
            return "Summary unavailable."

    def scrape_combined_subprocess(self, keyword: str) -> dict:
        try:
            result = subprocess.run(
                ["python", "tools/scraper.py", keyword],
                capture_output=True,
                text=True,
                timeout=45
            )
            if result.stderr:
                self.logger.warning(f"[SCRAPER STDERR] {result.stderr.strip()}")
            return json.loads(result.stdout.strip())
        except Exception as e:
            self.logger.error("Combined scraper error: " + str(e))
            return {"myntra": [], "ajio": []}

    def compare_sites(self, keyword: str) -> dict:
        try:
            start = time.time()
            data = self.scrape_combined_subprocess(keyword)
            m = data.get("myntra", [])
            a = data.get("ajio", [])
            self.logger.info(f"[TIMER] Scraper.py completed in {time.time() - start:.2f}s")
        except Exception as e:
            self.logger.error("Scraper crash: " + str(e))
            m, a = [], []

        mn = [i["name"] for i in m]
        an = [i["name"] for i in a]
        mm = self.calculate_match(mn, keyword)
        am = self.calculate_match(an, keyword)

        try:
            summary = self.generate_summary(keyword, m[:5], a[:5])
        except Exception as e:
            self.logger.error("Summary fallback: " + str(e))
            summary = "Summary unavailable."

        try:
            serper = self.get_serper_info(f"{keyword} site:myntra.com OR site:ajio.com")
        except Exception as e:
            self.logger.error("Serper fallback: " + str(e))
            serper = []

        return {
            "keyword": keyword,
            "myntra_match": mm,
            "ajio_match": am,
            "myntra_total": len(m),
            "ajio_total": len(a),
            "top_myntra": m[:5],
            "top_ajio": a[:5],
            "summary": summary,
            "serper_links": serper
        }

    async def process_query(self, query: str):
        self.logger.info(f"Processing keyword: {query}")
        return self.compare_sites(query)
