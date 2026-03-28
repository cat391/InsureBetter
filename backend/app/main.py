import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="InsureBetter API",
    description="Insurance Denial Appeal Assistant - helps users appeal health insurance claim denials",
    version="0.1.0",
)

origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import appeal  # noqa: E402

app.include_router(appeal.router)


@app.get("/")
async def root():
    return {"message": "InsureBetter API", "docs": "/docs"}
