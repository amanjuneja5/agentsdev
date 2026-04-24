import os 
import re
import json
from pathlib import Path
import chromadb


base_path = Path(__file__).cwd()
runbook_dir = base_path / "runbooks"
all_chunks = []


def chunk_by_headers(content, source):

    title_match = re.match(r'^# (.+)',content)
    doc_title = title_match.group(1) if title_match else source

    sections = re.split(r'\n(?=##)', content)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section or section.startswith('#') and not section.startswith('##'):
            continue

        chunk_text = f"[{doc_title}]\n{section}"

        heading_match = re.match(r'## (.+)', section)
        heading = heading_match.group(1) if heading_match else "intro"

        chunks.append({
            "text": chunk_text,
            "source": source,
            "section": heading
        })
    
    return chunks

for filename in os.listdir(runbook_dir):
    if not filename.endswith(".md"):
        continue

    with open(os.path.join(runbook_dir, filename), "r") as f:
        content = f.read()

    chunks = chunk_by_headers(content, filename)
    all_chunks.append(chunks)
    


# chroma_client = chromadb.Client()

# collection = chroma_client.create_collection(name="runbooks")