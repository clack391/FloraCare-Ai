import sys

from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.vector_store.chroma_store import BotanicalKnowledgeBase
import uuid
from typing import Union

def ingest_file(file_path: Union[str, Path]):
    kb = BotanicalKnowledgeBase()
    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return

    if path.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n\n"
        except ImportError:
            print("Error: pypdf not installed. Please run: pip install pypdf")
            return
    else:
        # Assume text
        with open(path, "r") as f:
            content = f.read()
    
    # Simple chunking by paragraph for Phase 1
    chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
    
    if not chunks:
        print(f"Skipping {path.name}: No indexable content found.")
        return
    
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [{"source": path.name, "chunk_index": i} for i in range(len(chunks))]
    
    print(f"Ingesting {len(chunks)} chunks from {path.name}...")
    kb.add_documents(documents=chunks, metadatas=metadatas, ids=ids)
    print("Ingestion complete.")

def process_path(input_path: str):
    path = Path(input_path)
    if not path.exists():
        print(f"Path not found: {input_path}")
        return

    if path.is_file():
        ingest_file(path)
    elif path.is_dir():
        print(f"Scanning directory: {path}")
        supported_extensions = {".txt", ".pdf"}
        # Recursive search for supported files
        files = [p for p in path.rglob("*") if p.suffix.lower() in supported_extensions]
        
        if not files:
            print("No suitable files (.txt, .pdf) found in directory.")
            return
            
        print(f"Found {len(files)} files. Starting batch ingestion...")
        for p in files:
            ingest_file(p)
    else:
        print("Invalid path type.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_data.py <file_or_directory_path>")
        sys.exit(1)
    
    process_path(sys.argv[1])
