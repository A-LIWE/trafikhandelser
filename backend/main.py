import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from store import init_db, get_all_device_tokens
from poller import poll_trafikverket
from apns import send_push_to_all
from formatter import format_incident
from api import app

load_dotenv()

POLL_INTERVAL = 60  # sekunder

async def polling_loop():
    while True:
        try:
            incidents = await poll_trafikverket()
            tokens = await get_all_device_tokens()

            for incident in incidents:
                # Skicka notis direkt med råtext
                await send_push_to_all(tokens, incident)

                # Formatera asynkront i bakgrunden
                asyncio.create_task(format_incident(incident))

        except Exception as e:
            print(f"Polling error: {e}")

        await asyncio.sleep(POLL_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    asyncio.create_task(polling_loop())
    yield

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)