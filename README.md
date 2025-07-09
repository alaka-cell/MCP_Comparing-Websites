# Beauty Product Comparator

A simple tool to compare beauty products across Myntra, AJIO, Nykaa, and Amazon. Enter any product name (like "lipstick" or "face wash") and get real-time results, matched items, and AI-generated summaries and suggestions.

## Features

- Real-time scraping from 4 major e-commerce sites
- Match percentage and product overlap detection
- Local LLM-based comparison summaries and related suggestions (via Ollama + Mistral)
- Wishlist functionality and price filtering
- Clean, responsive Streamlit UI

## Tech Stack

- Python 3.10+
- Streamlit
- Selenium + BeautifulSoup
- RapidFuzz
- Ollama (Mistral)

## Getting Started

```bash
git clone https://github.com/your-username/product-comparator.git
cd product-comparator

python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

pip install -r requirements.txt

ollama run mistral

streamlit run streamlit_app.py
