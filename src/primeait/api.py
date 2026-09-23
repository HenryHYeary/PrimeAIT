from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
from primeait.query import build_agents

app = FastAPI()
agents, transcript = build_agents()

class AskRequest(BaseModel):
    question: str

class VoteRequest(BaseModel):
    question: str
    answers: dict[str, str]
    winner: str
    feedback: str = ""

@app.post("/ask")
async def ask(req: AskRequest):
    names = list(agents.keys())
    results = await asyncio.gather(*(agents[name].ask(req.question) for name in names))
    return dict(zip(names, results))

@app.post("/vote")
async def vote(req: VoteRequest):
    transcript.add_round(req.question, req.answers, req.winner, req.feedback)
    return {"status": "ok"}