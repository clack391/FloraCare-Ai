import sys
from pathlib import Path
import random

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.vector_store.chroma_store import BotanicalKnowledgeBase

def check_chroma_db():
    print(f"Checking ChromaDB...")
    try:
        kb = BotanicalKnowledgeBase()
        count = kb.collection.count()
        print(f"Total Documents in Collection: {count}")
        
        if count == 0:
            print("Database is empty.")
            return

        # Sample some documents
        print("\n--- Sampling 5 Random Documents ---")
        
        # Get all IDs first (heavy? no, valid for <10k)
        all_data = kb.collection.get()
        all_ids = all_data['ids']
        
        if not all_ids:
             print("DB Empty")
             return
             
        # Pick 5 random
        import random
        sample_indices = random.sample(range(len(all_ids)), min(5, len(all_ids)))
        
        for idx in sample_indices:
            doc = all_data['documents'][idx]
            meta = all_data['metadatas'][idx] if all_data['metadatas'] else {}
            
            print(f"\n[Chunk ID: {all_ids[idx]}] Source: {meta.get('source', 'Unknown')}")
            print("-" * 40)
            preview = doc[:300] + "..." if len(doc) > 300 else doc
            print(preview)
            print("-" * 40)
            
    except Exception as e:
        print(f"Error checking DB: {e}")

if __name__ == "__main__":
    check_chroma_db()
