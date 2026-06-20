import arxiv
from typing import List, Dict

class ArxivFetcher:
    def __init__(self, max_results: int = 10):
        self.client = arxiv.Client()
        self.max_results = max_results

    def fetch_papers(self, query: str, category: str = "all") -> List[Dict]:
        # Enforce exact phrase matching by adding quotes
        clean_query = query.strip()
        if not (clean_query.startswith('"') and clean_query.endswith('"')):
            clean_query = f'"{clean_query}"'
        
        # Build category filter if not "all"
        if category != "all":
            category_map = {
                "cs": "cat:cs.*",
                "cs.AI": "cat:cs.AI",
                "cs.LG": "cat:cs.LG",
                "cs.CV": "cat:cs.CV",
                "cs.CL": "cat:cs.CL",
                "cs.NE": "cat:cs.NE",
                "cs.RO": "cat:cs.RO",
                "cs.SE": "cat:cs.SE",
                "math": "cat:math.*",
                "math.OC": "cat:math.OC",
                "physics": "cat:physics.*",
                "astro-ph": "cat:astro-ph.*",
                "cond-mat": "cat:cond-mat.*",
                "gr-qc": "cat:gr-qc",
                "hep-ex": "cat:hep-ex",
                "hep-lat": "cat:hep-lat",
                "hep-ph": "cat:hep-ph",
                "hep-th": "cat:hep-th",
                "math-ph": "cat:math-ph",
                "nlin": "cat:nlin.*",
                "nucl-ex": "cat:nucl-ex",
                "nucl-th": "cat:nucl-th",
                "quant-ph": "cat:quant-ph",
                "q-bio": "cat:q-bio.*",
                "q-fin": "cat:q-fin.*",
                "stat": "cat:stat.*",
                "stat.ML": "cat:stat.ML",
                "econ": "cat:econ.*",
                "eess": "cat:eess.*",
            }
            cat_query = category_map.get(category, "")
            if cat_query:
                final_query = f"{cat_query} AND {clean_query}"
            else:
                final_query = clean_query
        else:
            final_query = clean_query

        search = arxiv.Search(
            query=final_query,
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        papers = []
        for result in self.client.results(search):
            papers.append({
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "abstract": result.summary,
                "pdf_url": result.pdf_url,
                "published": result.published.strftime("%Y-%m-%d"),
                "entry_id": result.entry_id,
            })
        return papers