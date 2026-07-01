from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .graph import run_audit
from .schemas import AuditResponse, SecuritiesCase

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

app = FastAPI(title="FinRisk Multi-Agent API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "finrisk-multi-agent"}


@app.post("/api/audit", response_model=AuditResponse)
def audit(securities_case: SecuritiesCase) -> AuditResponse:
    try:
        return run_audit(securities_case)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


app.mount("/data", StaticFiles(directory=ROOT / "data"), name="data")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@app.get("/{path:path}")
def static_files(path: str) -> FileResponse:
    file_path = ROOT / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(ROOT / "index.html")
