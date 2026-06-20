import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import uuid

class EmbeddingManager:
    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="papers",
            embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name='all-MiniLM-L6-v2'
            )
        )

    def add_papers(self, papers: List[Dict]):
        """FAST version: uses only abstract – no PDF download."""
        ids, documents, metadatas = [], [], []
        for paper in papers:
            combined_text = f"Title: {paper['title']}\nAbstract: {paper['abstract']}"
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            documents.append(combined_text)
            metadatas.append({
                "title": paper['title'],
                "authors": ", ".join(paper['authors']),
                "pdf_url": paper['pdf_url'],
                "chunk_index": 0
            })
        if ids:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        return [
            {
                "document": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            }
            for i in range(len(results['ids'][0]))
        ]