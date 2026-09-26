import os

from pathlib import Path
from collections import deque
from dotenv import load_dotenv
import litellm

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PROVIDER_REGISTRY = {
    "OpenAI": {"env_key": "OPENAI_API_KEY", "model": "openai/gpt-4o-mini"},
    "DeepSeek": {"env_key": "DEEPSEEK_API_KEY", "model": "deepseek/deepseek-chat"},
    "Anthropic": {"env_key": "ANTHROPIC_API_KEY", "model": "anthropic/claude-sonnet-4-5"},
    "Gemini": {"env_key": "GEMINI_API_KEY", "model": "gemini/gemini-2.5-flash"},
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PERSIST_DIR = PROJECT_ROOT / "data" / "chroma_db"
SYSTEM_PROMPT = (
    "You are actively competing against other models (or other instances of "
    "yourself) for the best answer.\n\n"
    "Use the user's previous conversations and choices of best prompt to guide "
    "yourself to the best answer.\n\n"
    "You are a competitive model competing with other models for the best "
    "answer to the user's prompt. Keep an eye out for their preferences."
)

class SharedTranscript:
    """Bounded recent window, identitcal for every agent."""

    def __init__(self, max_rounds: int = 8):
        self._rounds = deque()
        self._max_rounds = max_rounds
        self._evicted_sink = None
        self._add_sink = None

    def on_evict(self, callback):
        """callback(round: dict) fires for any round pushed out of the window"""
        self._evicted_sink = callback

    def on_add(self, callback):
        self._add_sink = callback

    def add_round(self, question: str, answers: dict[str, str], winner: str, feedback: str = ""):
        round_data = {"question": question, "answers": answers, "winner": winner, "feedback": feedback}
        self._rounds.append(round_data)

        if self._add_sink:
            self._add_sink(round_data)

        while len(self._rounds) > self._max_rounds:
            oldest = self._rounds.popleft()
            if self._evicted_sink:
                self._evicted_sink(oldest)


    def as_messages(self) -> list[dict]:
        messages = []
        for r in self._rounds:
            messages.append({"role": "user", "content": r["question"]})
            for model, answer in r["answers"].items():
                tag = " (winner)" if model == r["winner"] else ""
                messages.append({"role": "assistant", "content": f"[{model}{tag}]: {answer}"})
            if r["feedback"]:
                messages.append({
                    "role": "user",
                    "content": f"Feedback on why {r['winner']} won: {r['feedback']}",
                })
        return messages

class RagAgent:
    def __init__(self, name: str, model: str, retriever, transcript: SharedTranscript):
        self.name = name
        self.model = model
        self._retriever = retriever
        self._transcript = transcript

    async def ask(self, question: str) -> str:
        docs = self._retriever.invoke(question)
        context = "\n\n".join(d.page_content for d in docs)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self._transcript.as_messages())
        messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {question}",
        })

        response = await litellm.acompletion(model=self.model, messages=messages)
        return response.choices[0].message.content

def available_providers() -> dict[str, str]:
    """Return {name: model_string} for every provider with a key set."""
    return {
        name: cfg["model"]
        for name, cfg in PROVIDER_REGISTRY.items()
        if os.environ.get(cfg["env_key"])
    }

def build_resources():
    """Expensive, shared setup: embeddings, vectorstore, retriever, provider check.
    Used by both the CLI (build_agents) and the API (ThreadManager)."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    providers = available_providers()
    if len(providers) < 2:
        raise RuntimeError(f"Need at least 2 provider API keys to compete. Found {list(providers) or 'none'}")

    return retriever, vectorstore, providers

def build_agents():
    retriever, vectorstore, providers = build_resources()
    transcript = SharedTranscript(max_rounds=8)

    def write_back(round_data: dict):
        doc_text = (
            f"Q: {round_data['question']}\n"
            f"Winner: {round_data['winner']}\n"
            f"Chosen answer: {round_data['answers'][round_data['winner']]}"
        )
        if round_data["feedback"]:
            doc_text += f"\nWhy it won: {round_data['feedback']}"
        vectorstore.add_texts(
            [doc_text],
            metadatas=[{"winner": round_data["winner"], "type": "past_round", "has_feedback": bool(round_data["feedback"])}]
        )

    transcript.on_evict(write_back)

    agents = {
        name: RagAgent(name, model, retriever, transcript)
        for name, model in providers.items()
    }
    return agents, transcript

def main():
    agents, transcript = build_agents()
    while True:
        question = input("\nAsk something (or 'quit'): ")
        if question.lower() == "quit":
            break

        answers = {}
        for name, agent in agents.items():
            answers[name] = agent.ask(question)
            print(f"\n{name}: {answers[name]}")

        winner = input(f"\nWho won? ({'/'.join(agents.keys())}): ").strip()
        while winner not in agents:
            winner = input(f"Please choose one of {list(agents.keys())}: ").strip()

        feedback = input("Why? (optional, press Enter to skip): ").strip()

        transcript.add_round(question, answers, winner, feedback)
    

if __name__ == "__main__":
    main()