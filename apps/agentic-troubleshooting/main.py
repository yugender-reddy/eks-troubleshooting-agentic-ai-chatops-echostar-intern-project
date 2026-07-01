import logging
import sys
import uvicorn
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException

# Load .env before anything else reads os.environ
load_dotenv()

from src.config.settings import Config
from src.handlers.gchat_handler import handle_gchat_message
from src.handlers.gchat_auth import verify_gchat_request

# 1. Setup Logging immediately before anything runs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 2. Use a Lifespan Context Manager to run validation *before* the API opens
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup configuration validation and cleanup operations."""
    try:
        Config.validate()
        logger.setLevel(getattr(logging, Config.LOG_LEVEL, logging.INFO))
        logger.info("Configuration validated successfully. Starting K8s Troubleshooting Agent...")
        yield
    except ValueError as e:
        logger.error(f"Config validation error during startup: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected startup error: {e}")
        sys.exit(1)

# 3. Create the FastAPI app with the lifespan attachment
app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint for K8s liveness/readiness probes."""
    return {"status": "healthy"}


@app.post("/webhook")
async def gchat_webhook(request: Request):
    """Google Chat webhook endpoint with JWT verification."""
    try:
        # Verify request authenticity (no-op when MOCK_MODE=true)
        await verify_gchat_request(request)

        payload = await request.json()
        event_type = payload.get("type")

        if event_type in ["ADDED_TO_SPACE", "MESSAGE"]:
            return handle_gchat_message(payload)

        return Response(status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook event: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)
