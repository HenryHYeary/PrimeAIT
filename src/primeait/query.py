from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PERSIST_DIR = PROJECT_ROOT / "data" / "chroma_db"

def build_chain():
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(persist_directory=str(PERSIST_DIR), embedding_function=embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

    prompt = ChatPromptTemplate.from_template(
        "You are actively competing against other models (or other instances of yourself) for the best answer.\n\n"
        "Use the user's previous conversations and choices of best prompt to guide yourself to the best answer.\n\n"
    )
    agent = create_agent(
        model="openai:gpt-4o-mini",
        system_prompt="You are a competitive model competing with other models for the best answer to the user's prompt. Keep an eye out for their preferences.",
        debug=True
    )

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | agent
        | StrOutputParser()
    )
    return chain

if __name__ == "__main__":
    chain = build_chain()
    while True:
        question = input("\nAsk something (or 'quit'): ")
        if question.lower() == "quit":
            break
        print(chain.invoke(question))