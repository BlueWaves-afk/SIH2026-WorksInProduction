from fastapi import FastAPI
from app.schemas import FarmerProfile, RiskEvent  # sanity import check

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}