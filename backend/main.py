from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.agent import run_agent


app = FastAPI(
    title="CivicLens API",
    description="Agentic municipal policy impact intelligence",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "name": "CivicLens",
        "status": "online",
        "message": "Municipal Policy Impact Intelligence Agent"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/api/analyze")
def analyze(request: AnalysisRequest):

    result = run_agent(request.question)

    return {
        "success": True,

        "request": request.question,

        "plan": result["plan"],

        "tools": [
            {
                "tool": item["tool"],
                "query": item["query"]
            }
            for item in result["tool_results"]
        ],

        # NEW:
        # Send the locally-generated evidence graph
        # to the React frontend.
        "evidence_graph": result.get(
            "evidence_graph",
            {
                "nodes": [],
                "edges": []
            }
        ),

        "report": result["report"]
    }