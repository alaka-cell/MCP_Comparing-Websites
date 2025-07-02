import argparse
import subprocess
import uvicorn
import asyncio
from mcp_client import MCPClient

def run_streamlit():
    subprocess.run(["streamlit", "run", "streamlit_app.py"])

def run_fastapi():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

def test_client():
    keyword = input("Keyword: ")
    result = asyncio.run(MCPClient().process_query(keyword))
    print(result)

def main():
    parser = argparse.ArgumentParser(description="Run the product search app in different modes.")
    parser.add_argument(
        "mode",
        choices=["streamlit", "fastapi", "test"],
        default="fastapi",
        nargs="?",
        help="Choose the mode: 'streamlit', 'fastapi', or 'test' (default: fastapi)"
    )

    args = parser.parse_args()

    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "fastapi":
        run_fastapi()
    elif args.mode == "test":
        test_client()

if __name__ == "__main__":
    main()
