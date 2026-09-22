from dotenv import load_dotenv
from pathlib import Path
from langchain_unstructured import UnstructuredLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PERSIST_DIR = DATA_DIR / "chroma_db"

def ingest():
    conversations = []
    for md_path in DATA_DIR.glob("*.md"):
        loader = UnstructuredLoader(md_path)
        conversations.extend(loader.load())

    print(f"Loaded {len(conversations)} conversations")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )
    chunks = splitter.split_documents(conversations)
    print(f"Split into {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(PERSIST_DIR)
    )
    print(f"Indexed {vectorstore._collection.count()} vectors into Chroma at {PERSIST_DIR}")

if __name__ == "__main__":
    ingest()