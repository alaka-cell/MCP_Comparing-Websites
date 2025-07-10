# Beauty Product Comparator

A simple, minimal tool to compare beauty products across Myntra, AJIO, Nykaa, and Amazon. Enter any product name (like "lipstick" or "face wash") and get real-time results, matched items, AI-powered summaries, and suggestions.

## Features

- Compare products across 4 major e-commerce sites (real-time scraping)
- Wishlist and remove products with login functionality
- AI-generated product summaries and suggestions using Ollama (Mistral)
- Google search trend suggestions via Serper API
- Matched product grouping across websites
- Simple filters like price range
- Clean, pastel-themed Streamlit UI with authentication

## Tech Stack

- Python 3.10+
- Streamlit
- Selenium + BeautifulSoup
- RapidFuzz
- Ollama (Mistral)
- FastAPI (for auth backend)
- SQLite + SQLAlchemy (user management)

## Getting Started

```bash
git clone https://github.com/your-username/product-comparator.git
cd product-comparator

python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

pip install -r requirements.txt

ollama run mistral

# Start the backend (FastAPI server)
python server.py

# In a new terminal, start the Streamlit frontend
streamlit run streamlit_app.py
