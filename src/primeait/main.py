from pathlib import Path
from collections import deque
from datetime import datetime
from dotenv import load_dotenv
import litellm

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

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


class MarkdownLogger:
    def __init__(self, path: Path):
        self.path = path
        if not self.path.exists():
            self.path.write_text("# Conversation Log\n\n")

    def log_round(self, round_data: dict):
        lines = [f"## {datetime.now():%Y-%m-%d %H:%M:%S}", "", f"**Q:** {round_data['question']}", ""]
        for model, answer in round_data["answers"].items():
            tag = " 🏆" if model == round_data["winner"] else ""
            lines.append(f"**{model}{tag}:** {answer}\n")
        if round_data["feedback"]:
            lines.append(f"**Feedback:** {round_data['feedback']}\n")
        lines.append("---\n")

        with self.path.open("a") as f:
            f.write("\n".join(lines))

class RagAgent:
    def __init__(self, name: str, model: str, retriever, transcript: SharedTranscript):
        self.name = name
        self.model = model
        self._retriever = retriever
        self._transcript = transcript

    def ask(self, question: str) -> str:
        docs = self._retriever.invoke(question)
        context = "\n\n".join(d.page_content for d in docs)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(self._transcript.as_messages())
        messages.append({
            "role": "user",
            "content": f"Context: {context}\n\nQuestion: {question}",
        })

        response = litellm.completion(model=self.model, messages=messages)
        return response.choices[0].message.content

def build_agents():
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory=PERSIST_DIR, embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    transcript = SharedTranscript(max_rounds=8)

    logger = MarkdownLogger(PROJECT_ROOT / "data" / "conversation_log.md")
    transcript.on_add(logger.log_round)

    def write_back(round_data: dict):
        doc_text = (
            f"Q: {round_data['question']}\n"
            f"Winner: {round_data['winner']}\n"
            f"Chosen answer: {round_data['answers'][round_data['winner']]}"
        )
        if round_data["feedback"]:
            doc_text += f"\nWhy it won: {round_data["feedback"]}"

        vectorstore.add_texts(
            [doc_text],
            metadatas=[{"winner": round_data["winner"], "type": "past_round", "has_feedback": bool(round_data["feedback"])}],
        )

    transcript.on_evict(write_back)


    agents = {
        "OpenAI": RagAgent("OpenAI", "openai/gpt-4o-mini", retriever, transcript),
        "DeepSeek": RagAgent("DeepSeek", "deepseek/deepseek-chat", retriever, transcript)
    }
    return agents, transcript
        

if __name__ == "__main__":
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