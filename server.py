from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from mcp_client import MCPClient
import logging
import asyncio

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Settings(BaseSettings):
    server_script_path: str = "dummy_script.py"

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Starting up and connecting to MCP server...")
    client = MCPClient()

    ok = await client.connect_to_server(settings.server_script_path)
    if not ok:
        logger.error("Failed to connect to MCP server.")
        raise RuntimeError("Could not connect to MCP server during startup.")

    async def warmup_model():
        try:
            logger.info("Warming up Mistral model...")
            client.llm.generate(model="mistral", prompt="hello", stream=False)
            logger.info("Mistral warm-up completed.")
        except Exception as e:
            logger.warning(f"Mistral warm-up skipped or failed: {e}")

    await asyncio.to_thread(warmup_model)

    app.state.client = client
    yield
    logger.info("Cleaning up MCP resources...")
    await client.cleanup()
    logger.info("🔌 Shutdown complete.")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
)

class CompareRequest(BaseModel):
    keyword: str

@app.post("/compare")
async def compare(req: CompareRequest):
    try:
        return await app.state.client.process_query(req.keyword)
    except Exception as e:
        logger.exception("Error during comparison:")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok"}
