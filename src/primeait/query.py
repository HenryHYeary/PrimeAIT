from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_deepseek import ChatDeepSeek
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PERSIST_DIR = PROJECT_ROOT / "data" / "chroma_db"
SYSTEM_PROMPT = "You are a competitive model competing with other models for the best answer to the user's prompt. Keep an eye out for their preferences."

class RagAgent:
    """Thin adapter so callers never touch LangChain types directly."""

    def __init__(self, chain):
        self._chain = chain

    def ask(self, question: str) -> str:
        return self._chain.invoke(question)

def build_agents() -> dict[str, RagAgent]:
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "You are actively competing against other models (or other instances "
            "of yourself) for the best answer.\n\n"
            "Use the user's previous conversations and choices of best prompt to "
            "guide yourself to the best answer.\n\n"
            "Context: {context}\n\nQuestion: {question}",
        ),
    ])


    base = {"context": retriever, "question": RunnablePassthrough()} | prompt

    openai_model = ChatOpenAI(model="gpt-4o-mini")
    deepseek_model = ChatDeepSeek(model="deepseek-chat")

    return {
        "OpenAI": RagAgent(base | openai_model | StrOutputParser()),
        "DeepSeek": RagAgent(base | deepseek_model | StrOutputParser()),
    }

if __name__ == "__main__":
    agents = build_agents()
    while True:
        question = input("\nAsk something (or 'quit'): ")
        if question.lower() == "quit":
            break
        for name, agent in agents.items():
            print(f"{name}: {agent.ask(question)}")