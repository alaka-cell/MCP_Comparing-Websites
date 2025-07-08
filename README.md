## Product Comparator

A fast and intelligent product comparison tool that scrapes **Myntra**, **AJIO**, **Nykaa**, and **Amazon** for real-time product results based on a search keyword. Built using the MCP architecture with support from LLMs (via Ollama), this project compares product matches, highlights overlap, and summarizes key differences.

---

## Features

- Search any fashion or beauty product (e.g., "Nike shoes", "lipstick", "bags")
- Match percentage calculation using fuzzy logic and normalization
- LLM-powered summaries with Ollama (Mistral)
- Google Serper integration for top 5 relevant links
- Comparison of matched items between Myntra, AJIO, Nykaa, and Amazon
- Streamlit UI with dark mode, autocomplete & fun "fortune" mode

---

## Tech Stack

- **Python 3.10+**
- **Streamlit** – frontend UI
- **Scrapy + Selenium** – for real-time scraping
- **FuzzyWuzzy / RapidFuzz** – keyword-based match logic
- **Ollama + Mistral** – local LLM for product summary generation
- **Serper.dev API** – top 5 web links via Google search
- **MCP Framework** – modular client-server communication

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/your-username/product-comparator.git
cd product-comparator

# 2. Create and activate virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows

# 3. Install requirements
pip install -r requirements.txt

# 4. Make sure Ollama is installed and Mistral is pulled
ollama run mistral
