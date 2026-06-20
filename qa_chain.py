from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
from embedding_manager import EmbeddingManager

class QASystem:
    def __init__(self, embedding_manager: EmbeddingManager):
        self.embedding_manager = embedding_manager
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use FLAN-T5-small (already cached, 300 MB)
        self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
        self.model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small").to(self.device)

    def ask(self, question: str, top_k: int = 7) -> str:
        results = self.embedding_manager.search(question, n_results=top_k)
        if not results:
            return "No relevant papers found to answer this question."

        contexts = [res['document'] for res in results]
        combined_context = "\n\n".join(contexts)

        words = combined_context.split()
        if len(words) > 600:
            combined_context = " ".join(words[:600])

        prompt = f"""Answer the question based on the context below. Give a detailed answer with multiple paragraphs.

Question: {question}

Context:
{combined_context}

Answer:"""

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=700
        ).to(self.device)

        outputs = self.model.generate(
            inputs.input_ids,
            max_new_tokens=450,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            repetition_penalty=1.1
        )

        answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return answer if answer and len(answer.split()) > 3 else "No detailed answer could be generated. Try a more specific question."