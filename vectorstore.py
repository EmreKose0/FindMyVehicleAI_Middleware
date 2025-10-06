import faiss
import numpy as np
from embeddings import embed_text

class VectorStore:
	def __init__(self, dim):
		self.vectors = []
		self.texts = []
		self.metadatas = []
		self.dim = dim

	def add(self, texts, metadata=None):
		for text in texts:
			vec = embed_text(text)
			self.vectors.append(vec)
			self.texts.append(text)
			if metadata:
				self.metadatas.append(metadata)
			else:
				self.metadatas.append({})

	def search(self, query, top_k=5, include_metadata=False):
		query_vec = embed_text(query)
		results = []
		for vec, text, meta in zip(self.vectors, self.texts, self.metadatas):
			score = self.cosine_similarity(query_vec, vec)
			results.append((score, text, meta))
		results.sort(key=lambda x: x[0], reverse=True)

		if include_metadata:
			# döndürülen liste: [(score, text, meta), ...]
			return results[:top_k]
		else:
			# döndürülen liste: [text, text, text]
			return [r[1] for r in results[:top_k]]

	def cosine_similarity(self, a, b):
		return sum(x * y for x, y in zip(a, b)) / (
			(sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5)
		)

