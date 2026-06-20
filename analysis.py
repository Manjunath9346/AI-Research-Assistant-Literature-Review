from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import nltk
from nltk.corpus import stopwords
from collections import Counter
import re
from typing import List

# Download stopwords safely
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

class ThemeGapAnalyzer:
    def __init__(self, papers):
        self.papers = papers
        self.abstracts = [p['abstract'] for p in papers]

    def extract_keywords(self, n_keywords: int = 10) -> List[str]:
        word_list = []
        for abstract in self.abstracts:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', abstract.lower())
            word_list.extend(words)
        filtered = [w for w in word_list if w not in stop_words and len(w) > 2]
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(n_keywords)]

    def find_common_themes(self, n_topics: int = 3) -> List[str]:
        vectorizer = CountVectorizer(max_features=1000, stop_words='english')
        dtm = vectorizer.fit_transform(self.abstracts)
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(dtm)
        feature_names = vectorizer.get_feature_names_out()
        topics = []
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[-5:]]
            topics.append(" ".join(top_words))
        return topics

    def identify_gaps(self) -> List[str]:
        all_words = []
        for abstract in self.abstracts:
            words = set(re.findall(r'\b[a-zA-Z]{3,}\b', abstract.lower()))
            all_words.append(words)
        doc_freq = {}
        for words in all_words:
            for w in words:
                doc_freq[w] = doc_freq.get(w, 0) + 1
        threshold = max(1, len(self.papers) * 0.3)
        gap_terms = [w for w, freq in doc_freq.items() if freq < threshold and freq > 0 and w not in stop_words]
        gap_terms.sort(key=lambda x: doc_freq[x], reverse=True)
        return gap_terms[:5]