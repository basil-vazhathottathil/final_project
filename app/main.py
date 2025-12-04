# app/main.py
from fastapi import FastAPI, Depends
from app.auth.auth import verify_token

app = FastAPI()

@app.get("/protected")
async def protected_route(user=Depends(verify_token)):
    return {"message": "You are authenticated", "user": user}
