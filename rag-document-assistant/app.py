import os
import sys
import shutil
import argparse
from dotenv import load_dotenv

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

# Config
load_dotenv()

DOCS_DIR = "sample_docs"
FAISS_INDEX_DIR = "faiss_index"
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K_RESULTS = 4

# CLI Arguments
def parse_args():
    parser = argparse.ArgumentParser(description="RAG Document Assistant")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild of the FAISS index from documents.",
    )
    return parser.parse_args()

# Prompt Template
RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a helpful assistant. Use only the context below to answer the question.
If the answer is not in the context, say "I don't have enough information to answer that."

Context:
{context}

Question:
{question}

Answer:""",
)

# Document Loading
def load_documents(docs_dir: str):
    """Load all .txt files from the given directory."""
    if not os.path.exists(docs_dir):
        print(f"[ERROR] Documents folder '{docs_dir}' not found.")
        sys.exit(1)

    loader = DirectoryLoader(
        docs_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
        show_progress=True,
    )
    docs = loader.load()

    if not docs:
        print(f"[ERROR] No .txt files found in '{docs_dir}'. Add documents and retry.")
        sys.exit(1)

    print(f"[INFO] Loaded {len(docs)} document(s) from '{docs_dir}'.")
    return docs

# Chunking
def chunk_documents(docs):
    """Split documents into smaller overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    print(f"[INFO] Split into {len(chunks)} chunk(s) "
          f"(chunk_size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}).")
    return chunks

# Vector Store
def build_vector_store(chunks, embeddings):
    """Embed chunks and store in a FAISS index."""
    print("[INFO] Generating embeddings and building FAISS index...")
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(FAISS_INDEX_DIR)
    print(f"[INFO] FAISS index saved to '{FAISS_INDEX_DIR}/'.")
    return vector_store


def load_vector_store(embeddings):
    """Load an existing FAISS index from disk."""
    print(f"[INFO] Loading existing FAISS index from '{FAISS_INDEX_DIR}/'...")
    return FAISS.load_local(
        FAISS_INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )

# QA Chain
def build_qa_chain(vector_store):
    """Wire up the retriever + GPT model into a RetrievalQA chain."""
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": TOP_K_RESULTS},
    )
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": RAG_PROMPT},
        return_source_documents=True,
    )
    return chain

# Terminal Loop
def run_query_loop(chain):
    """Interactive terminal Q&A loop."""
    print("\n" + "═" * 55)
    print("  RAG Document Assistant — ready.")
    print("  Type your question, or 'exit' to quit.")
    print("═" * 55 + "\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Session ended.")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("[INFO] Goodbye.")
            break

        result = chain.invoke({"query": question})
        answer = result["result"]
        sources = result.get("source_documents", [])

        print(f"\nAssistant: {answer}\n")

        if sources:
            seen = set()
            print("  Sources:")
            for doc in sources:
                src = doc.metadata.get("source", "unknown")
                if src not in seen:
                    seen.add(src)
                    print(f"    • {os.path.basename(src)}")
        print()

# Entry Point
def main():
    args = parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY not set. Add it to a .env file or export it.")
        sys.exit(1)

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # If --rebuild flag passed, wipe the existing index first
    if args.rebuild and os.path.exists(FAISS_INDEX_DIR):
        shutil.rmtree(FAISS_INDEX_DIR)
        print("[INFO] Existing index cleared. Rebuilding from documents...")

    # Re-use existing index if it exists, otherwise build a new one
    if os.path.exists(FAISS_INDEX_DIR):
        vector_store = load_vector_store(embeddings)
    else:
        docs = load_documents(DOCS_DIR)
        chunks = chunk_documents(docs)
        vector_store = build_vector_store(chunks, embeddings)

    chain = build_qa_chain(vector_store)
    run_query_loop(chain)

if __name__ == "__main__":
    main()
