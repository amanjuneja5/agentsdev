import os 
import json
from pathlib import Path
import chromadb

from rag.chunker import chunk_by_headers

all_chunks = []

def build_index(runbook_dir):
    
    base_path = Path(__file__).cwd()
    runbook_dir = base_path / runbook_dir

    for filename in os.listdir(runbook_dir):
        if not filename.endswith(".md"):
            continue

        with open(os.path.join(runbook_dir, filename), "r") as f:
            content = f.read()

        chunks = chunk_by_headers(content, filename)
        all_chunks.append(chunks)
        

    chroma_client = chromadb.Client()

    collection = chroma_client.get_or_create_collection(
        name="runbooks",
        metadata={"hf:space": "cosine"}
    )

    collection.add(
        ids=[f"doc_id{i}" for i in range(len(chunks))],
        documents = [c["text"] for c in chunks],
        metadatas=[{"source":c.get("source",""), "section": c.get("section","")} for c in chunks]
    )

    return collection
