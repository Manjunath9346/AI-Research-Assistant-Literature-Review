from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
import nltk

class PaperSummarizer:
    def __init__(self, sentences_count: int = 3):
        # Ensure NLTK tokenizer data is available
        try:
            nltk.data.find('tokenizers/punkt_tab/english')
        except LookupError:
            nltk.download('punkt_tab', quiet=True)
        self.sentences_count = sentences_count
        self.summarizer = TextRankSummarizer()

    def summarize(self, text: str) -> str:
        if not text or len(text.strip()) < 50:
            return "Text too short to summarize."

        # Create a parser and tokenizer
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        # Get summary sentences
        summary_sentences = self.summarizer(parser.document, self.sentences_count)
        # Join sentences into a paragraph
        summary = " ".join(str(sentence) for sentence in summary_sentences)
        return summary if summary else "No summary generated."