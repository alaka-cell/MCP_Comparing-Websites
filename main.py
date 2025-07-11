import argparse
import subprocess
import uvicorn
import asyncio
from multiprocessing import Process
from mcp_client import MCPClient

def run_streamlit():
    subprocess.run(["streamlit", "run", "streamlit_app.py"])

def run_fastapi():
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)

def run_flask():
    subprocess.run(["flask", "run", "--app", "flask_app", "--port", "5000"])

def test_client():
    keyword = input("Keyword: ")
    result = asyncio.run(MCPClient().process_query(keyword))
    print(result)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["streamlit", "fastapi", "flask", "all", "test"], default="all", nargs="?")
    args = parser.parse_args()

    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "fastapi":
        run_fastapi()
    elif args.mode == "flask":
        run_flask()
    elif args.mode == "test":
        test_client()
    elif args.mode == "all":
        p1 = Process(target=run_fastapi)
        p2 = Process(target=run_flask)
        p1.start()
        p2.start()
        run_streamlit()
        p1.join()
        p2.join()

if __name__ == "__main__":
    main()
