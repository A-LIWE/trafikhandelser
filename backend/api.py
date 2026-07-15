from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from store import save_device_token, delete_device_token

app = FastAPI()

class TokenRequest(BaseModel):
    token: str

@app.post("/register-token")
async def register_token(request: TokenRequest):
    if not request.token:
        raise HTTPException(status_code=400, detail="Token missing")
    await save_device_token(request.token)
    return {"status": "ok"}

@app.delete("/register-token")
async def unregister_token(request: TokenRequest):
    if not request.token:
        raise HTTPException(status_code=400, detail="Token missing")
    await delete_device_token(request.token)
    return {"status": "ok"}