from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticRanker:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def rank(self, paragraph_summary, papers, top_k=3):
        if not papers:
            return []
        para_emb = self.model.encode(paragraph_summary)
        paper_embs = self.model.encode([p['summary'] for p in papers])
        sims = [(i, np.dot(para_emb, pe)/(np.linalg.norm(para_emb)*np.linalg.norm(pe))) for i, pe in enumerate(paper_embs)]
        sims.sort(key=lambda x: x[1], reverse=True)
        top_papers = []
        for idx, sim in sims[:top_k]:
            paper = papers[idx].copy()
            paper['relevance'] = round(sim*100, 2)
            top_papers.append(paper)
        return top_papers
