#  Your dress-up darling — Beauty Price Comparator

YDUD is a real-time beauty product price comparison tool built for shoppers who want to make smarter purchasing decisions without jumping between tabs. It scrapes live product listings from Myntra, Flipkart, Nykaa, and Amazon simultaneously, then presents results in a clean, unified interface — complete with product images, prices, brand tags, and direct links. Products that appear across multiple platforms are automatically grouped using fuzzy matching, so you can instantly see where a specific item is cheapest. A local Ollama (Mistral) model generates human-readable summaries of the search results and powers a side-by-side AI comparison of any two products, while Serper pulls in real-time Google trending searches to help users discover what's popular right now.

Beyond search, YDUD is a fully functional web app with user authentication, role-based access, and persistent wishlists. Shoppers can register an account, log in, and save any product directly from the results grid — their wishlist lives in the sidebar for quick reference at all times. Admins get a dedicated dashboard with elevated access. The app is built on Streamlit for the frontend, Flask for the auth backend, and SQLite for data persistence, making it lightweight and easy to run locally on Windows without any containerisation. The scraping layer uses Selenium with undetected-chromedriver to handle JavaScript-heavy e-commerce pages, with BeautifulSoup handling the HTML parsing and a dedicated debug tool for maintaining selectors when sites update their structure.

---

## Features

- **Real-time scraping** across Myntra, Flipkart, Nykaa, and Amazon using Selenium + BeautifulSoup
- **Cross-site matched products** — fuzzy-matched items grouped across all 4 platforms using RapidFuzz
- **AI-powered summaries & suggestions** via Ollama (Mistral) running locally
- **Trending search suggestions** via Serper (Google Search API)
- **Wishlist** — save and remove products per user account (persisted in SQLite)
- **Price range filter** — slider to narrow results after scraping
- **AI product comparison** — compare any two products from your search results
- **Role-based auth** — separate user and admin flows, with an admin dashboard at `pages/admin_app.py`
- **Pastel-themed Streamlit UI** with DM Sans + Playfair Display typography

---

## Project Structure

```
MCP_COMPARING-WEBSITES/
├── auth/
│   ├── __init__.py
│   ├── database.py          # SQLAlchemy DB setup
│   ├── models.py            # User, Wishlist models
│   ├── routes.py            # Flask auth endpoints (login, register, session)
│   ├── users.py             # User helper functions
│   ├── utils.py             # Password hashing, JWT utilities
│   └── users.db             # SQLite user database
├── pages/
│   └── admin_app.py         # Admin dashboard (Streamlit multipage)
├── tools/
│   ├── debug_selectors.py   # CSS selector debugging utilities
│   └── scraper.py           # Selenium + BS4 scraper for all 4 sites
├── utils/
│   ├── ai_suggestor.py      # Ollama (Mistral) suggestions & product comparison
│   ├── logger.py            # App-wide logger
│   └── wishlist_manager.py  # Load/add/remove wishlist items (JSON-backed per user)
├── wishlists/
│   └── <username>.json      # Per-user wishlist files
├── mcp_client.py            # MCPClient — orchestrates scraping & result assembly
├── streamlit_app.py         # Main Streamlit frontend
├── server.py                # Flask auth backend (run separately)
├── auth.db                  # Auth SQLite database
├── .env                     # Environment variables (not committed)
├── .gitignore
└── requirements.txt
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit 1.55 |
| Auth Backend | Flask + Flask-CORS |
| Scraping | Selenium, undetected-chromedriver, BeautifulSoup4 |
| Fuzzy Matching | RapidFuzz |
| AI Summaries | Ollama (Mistral), running locally |
| Trending Search | Serper API (Google Search) |
| Database | SQLite + SQLAlchemy |
| Auth | JWT (python-jose), Passlib (bcrypt) |
| HTTP | Requests, FastAPI (optional) |

---

## Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running locally
- Google Chrome (for Selenium scraping)
- A [Serper API key](https://serper.dev/) (free tier available)

### 1. Clone & set up environment

```bash
git clone https://github.com/your-username/MCP_Comparing-Websites.git
cd MCP_Comparing-Websites

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
FLASK_API_URL=http://localhost:5000
SERPER_API_KEY=your_serper_api_key_here
```

### 3. Start Ollama with Mistral

```bash
ollama run mistral
```

Keep this running in the background. It powers AI summaries and product comparison.

### 4. Start the Flask auth backend

```bash
python server.py
```

This runs on `http://localhost:5000` by default and handles login, registration, and session management.

### 5. Start the Streamlit app

In a new terminal (with `.venv` activated):

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501` in your browser.

---

## Usage

1. **Register or log in** from the sidebar
2. **Type a product name** in the search bar (e.g. `Maybelline lipstick`, `face wash`, `sunscreen SPF 50`)
3. Click **Compare Prices →** to trigger scraping across all 4 sites
4. Browse results by tab (Myntra / Flipkart / Nykaa / Amazon)
5. Use the **price range slider** to filter results
6. View **matched products** grouped across all platforms in the Cross-Site Comparison section
7. Click **+ Wishlist** on any product to save it (visible in the sidebar)
8. Use the **Compare** panel in the sidebar to AI-compare two specific products
9. Explore **AI Suggestions** and **Trending Searches** at the bottom

Admin users are redirected automatically to `pages/admin_app.py` on login.

---

## Notes

- Scraping relies on Selenium with `undetected-chromedriver`. Make sure Google Chrome is installed and up to date.
- If a site updates its HTML structure, update the selectors in `tools/scraper.py` and debug with `tools/debug_selectors.py`.
- Wishlists are stored as JSON files under `wishlists/<username>.json`.
- The app does not use Docker — run all services natively on Windows as described above.

---

## Contributing

Pull requests welcome. For major changes, open an issue first to discuss what you'd like to change.

---

*Made with care ♥ — GLAM Beauty Price Comparator*
