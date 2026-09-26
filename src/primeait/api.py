from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from contextlib import asynccontextmanager

from primeait import db

from primeait.query import build_resources
from primeait.threads import ThreadManager

retriever, vectorstore, providers = build_resources()
thread_manager = ThreadManager(retriever, providers, vectorstore)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield



app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateThreadRequest(BaseModel):
    title: str | None = None


class AskRequest(BaseModel):
    question: str


class VoteRequest(BaseModel):
    question: str
    answers: dict[str, str]
    winner: str
    feedback: str = ""


@app.post("/threads")
async def create_thread(req: CreateThreadRequest):
    return await db.create_thread(req.title)


@app.get("/threads")
async def get_threads():
    return await db.list_threads()


@app.post("/threads/{thread_id}/ask")
async def ask(thread_id: str, req: AskRequest):
    agents = await thread_manager.get_agents(thread_id)
    names = list(agents.keys())
    results = await asyncio.gather(*(agents[name].ask(req.question) for name in names))
    return dict(zip(names, results))


@app.post("/threads/{thread_id}/vote")
async def vote(thread_id: str, req: VoteRequest):
    await db.insert_round(thread_id, req.question, req.answers, req.winner, req.feedback)
    await thread_manager.record_round(thread_id, req.question, req.answers, req.winner, req.feedback)
    return {"status": "ok"}