import os, json, time, traceback, subprocess
from typing import Optional
from contextlib import AsyncExitStack
from dotenv import load_dotenv
import requests
from ollama import Client
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from utils.logger import logger
from difflib import SequenceMatcher, get_close_matches

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

    # ─────────────────────────────────────────────
    # SCRAPER CALL
    # ─────────────────────────────────────────────
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

            if not raw_output.startswith("{"):
                self.logger.error("[SCRAPER ERROR] Invalid JSON output")
                return {"myntra": [], "flipkart": [], "nykaa": [], "amazon": []}

            return json.loads(raw_output)

        except Exception as e:
            self.logger.error("Scraper error: " + str(e))
            return {"myntra": [], "flipkart": [], "nykaa": [], "amazon": []}

    # ─────────────────────────────────────────────
    # MATCH %
    # ─────────────────────────────────────────────
    def calculate_match(self, names, keyword):
        if not names:
            return 0.0

        keyword = normalize_name(keyword).lower()
        match_count = 0

        for name in names:
            name = normalize_name(name).lower()

            if keyword in name:
                match_count += 1
            elif SequenceMatcher(None, keyword, name).ratio() > 0.5:
                match_count += 1

        return round((match_count / len(names)) * 100, 2)

    # ─────────────────────────────────────────────
    # MATCH PRODUCTS
    # ─────────────────────────────────────────────
    def match_products_across_sites(self, myntra, flipkart, nykaa, amazon):
        matched = []
        all_products = []

        for site, products in [
            ("myntra", myntra),
            ("flipkart", flipkart),
            ("nykaa", nykaa),
            ("amazon", amazon)
        ]:
            for p in products:
                if not p.get("name"):
                    continue
                p["source"] = site
                p["normalized"] = normalize_name(p["name"])
                all_products.append(p)

        seen = set()

        for i, p1 in enumerate(all_products):
            if i in seen:
                continue

            group = {"myntra": None, "flipkart": None, "nykaa": None, "amazon": None}
            group[p1["source"]] = p1
            seen.add(i)

            for j in range(i + 1, len(all_products)):
                if j in seen:
                    continue

                p2 = all_products[j]
                sim = SequenceMatcher(None, p1["normalized"], p2["normalized"]).ratio()

                if sim > 0.7:
                    group[p2["source"]] = p2
                    seen.add(j)

            if sum(1 for v in group.values() if v) >= 2:
                matched.append(group)

        return matched

    # ─────────────────────────────────────────────
    # SUMMARY
    # ─────────────────────────────────────────────
    def generate_summary(self, keyword, myntra, flipkart, nykaa, amazon):
        try:
            prompt = f"""
Compare products for '{keyword}' across Myntra, Flipkart, Nykaa and Amazon.

Myntra: {[p['name'] for p in myntra]}
Flipkart: {[p['name'] for p in flipkart]}
Nykaa: {[p['name'] for p in nykaa]}
Amazon: {[p['name'] for p in amazon]}

Give short 2-3 line summary.
"""

            result = self.llm.generate(model=self.model, prompt=prompt)
            return result.get("response", "")

        except:
            return "Summary unavailable."

    # ─────────────────────────────────────────────
    # MAIN FUNCTION
    # ─────────────────────────────────────────────
    def compare_sites(self, keyword: str):

        raw = self.scrape_combined_subprocess(keyword)

        myntra = raw.get("myntra", [])
        flipkart = raw.get("flipkart", [])
        nykaa = raw.get("nykaa", [])
        amazon = raw.get("amazon", [])

        self.logger.info(
            f"Counts → Myntra:{len(myntra)}, Flipkart:{len(flipkart)}, Nykaa:{len(nykaa)}, Amazon:{len(amazon)}"
        )

        myntra_names = [p["name"] for p in myntra if p.get("name")]
        flipkart_names = [p["name"] for p in flipkart if p.get("name")]
        nykaa_names = [p["name"] for p in nykaa if p.get("name")]
        amazon_names = [p["name"] for p in amazon if p.get("name")]

        return {
            "myntra_match": self.calculate_match(myntra_names, keyword),
            "flipkart_match": self.calculate_match(flipkart_names, keyword),
            "nykaa_match": self.calculate_match(nykaa_names, keyword),
            "amazon_match": self.calculate_match(amazon_names, keyword),

            "myntra_total": len(myntra),
            "flipkart_total": len(flipkart),
            "nykaa_total": len(nykaa),
            "amazon_total": len(amazon),

            "summary": self.generate_summary(keyword, myntra[:3], flipkart[:3], nykaa[:3], amazon[:3]),

            "matched_products": self.match_products_across_sites(
                myntra, flipkart, nykaa, amazon
            ),

            "top_myntra": myntra,
            "top_flipkart": flipkart,
            "top_nykaa": nykaa,
            "top_amazon": amazon
        }