# RAG Document Assistant

A clean, terminal-based **Retrieval-Augmented Generation (RAG)** pipeline built with Python,
LangChain, OpenAI embeddings, and FAISS. Drop plain-text documents into a folder, ask
questions, and get grounded answers - no hallucinated facts, sources always cited.

> Personal R&D project - exploring production RAG patterns in a minimal, readable codebase.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Ingestion Path                                              │
│ (first run only)                                            │
│                                                             │
│ sample_docs/*.txt -> Loader -> Splitter -> Embeddings       │
│     │                                                       │
│ FAISS Index                                                 │
│ (saved to disk)                                             │
└─────────────────────────────────────────────────────────────┘
```
```
┌─────────────────────────────────────────────────────────────┐
│ Query Path                                                  │
│                                                             │
│ User Question -> Embed Query -> FAISS Similarity Search     │
│ │                                                           │
│ Top-K Chunks                                                │
│ │                                                           │
│ Prompt: context + question                                  │
│ │                                                           │
│ GPT-4o (OpenAI)                                             │
│ │                                                           │
│ Grounded Answer + Sources                                   │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component                                     | Role                                              |
|-----------------------------------------------|---------------------------------------------------|
| `DirectoryLoader`                             | Reads all `.txt` files from `sample_docs/`        |
| `RecursiveCharacterTextSplitter`              | Breaks documents into overlapping chunks          |
| `OpenAIEmbeddings` (`text-embedding-3-small`) | Converts chunks into dense vectors                |
| `FAISS` (CPU)                                 | Stores and searches vectors via cosine similarity |
| `ChatOpenAI` (`gpt-4o`)                       | Generates final answers from retrieved context    |
| `RetrievalQA` chain                           | LangChain glue: retriever + prompt + LLM          |

---

## How RAG Works

Traditional LLMs answer from what they memorized during training - that knowledge is frozen
and generic. RAG solves this by:

1. **Indexing** - your documents are chunked and converted to embeddings (vectors that capture
   semantic meaning), then stored in a vector database (FAISS).
2. **Retrieval** - when you ask a question, it is also embedded and the most semantically
   similar document chunks are fetched from the index.
3. **Augmented Generation** - the retrieved chunks are injected into the prompt as grounding
   context, and the LLM is instructed to answer *only* from that context.

The result: answers that are factual, specific to *your* data, and traceable back to source
documents.

```
Question ── embed ── ► query vector
              |
    FAISS similarity search
              |
    Top-K doc chunks
              |
┌────────────────────────────┐
│ Prompt = context + question│
└─────────────┬──────────────┘
              |
            GPT-4o
              |
        Grounded Answer
```

---

## Project Structure

```
rag-document-assistant/
│
├── app.py # Full pipeline: load -> chunk -> embed -> query loop
├── requirements.txt # Pinned dependencies
├── .env # OPENAI_API_KEY (git-ignored)
├── .gitignore
├── README.md
│
├── sample_docs/ # Drop your .txt documents here
│ ├── company_policy.txt
│ ├── product_manual.txt
│ └── research_notes.txt
│
└── faiss_index/ # Auto-generated on first run (git-ignored)
├── index.faiss
└── index.pkl
```

---

## Setup Instructions

### 1. Clone and enter the project

```bash
git clone https://github.com/your-username/rag-document-assistant.git
cd rag-document-assistant
```

### 2. Create a virtual environment

```
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```
pip install -r requirements.txt
```


### 4. Set your OpenAI API key
Create a .env file in the project root:
```
OPENAI_API_KEY=sk-...your-key-here...
```

Or export it directly:

```
export OPENAI_API_KEY=sk-...your-key-here...
```

### 5. Add your documents

Place any plain .txt files inside sample_docs/:

```
cp my_notes.txt sample_docs/
```

### 6. Run

```
python app.py
```

On first run, the app builds the FAISS index and saves it to faiss_index/.
On subsequent runs, it loads the saved index instantly - no re-embedding needed.

To force a full re-index (e.g. after adding new documents):

```
rm -rf faiss_index/ && python app.py
```

**Sample session:**

```
[INFO] Loaded 3 document(s) from 'sample_docs'.
[INFO] Split into 42 chunk(s) (chunk_size=500, overlap=50).
[INFO] Generating embeddings and building FAISS index...
[INFO] FAISS index saved to 'faiss_index/'.

═══════════════════════════════════════════════════════
  RAG Document Assistant - ready.
  Type your question, or 'exit' to quit.
═══════════════════════════════════════════════════════

You: What is the return policy?
```

## Future Improvements

- [ ] **PDF & Markdown support** - extend `DirectoryLoader` with `PyPDFLoader` and `UnstructuredMarkdownLoader`
- [ ] **Parent-child chunking** - store small child chunks for retrieval, inject large parent chunks as context (`ParentDocumentRetriever`)
- [ ] **MMR retrieval** - switch to `search_type="mmr"` to reduce redundant chunks in Top-K results
- [ ] **Streaming responses** - use `ChatOpenAI(streaming=True)` with a callback handler for token-by-token output
- [ ] **Conversation memory** - add `ConversationBufferMemory` to support multi-turn follow-up questions
- [ ] **RAGAS evaluation** - integrate [ragas.io](https://ragas.io) for automated faithfulness and relevance scoring
- [ ] **Swap FAISS -> Chroma** - drop-in replacement with built-in metadata filtering
- [ ] **Async ingestion pipeline** - `asyncio` + batch embedding calls for large document corpora
- [ ] **CLI flags** - `--rebuild-index`, `--docs-dir`, `--model` via `argparse`
