"""Real dense retrieval adapter: pinned local embedding + persistent Qdrant."""
from pathlib import Path
import math


class DenseRetriever:
    def __init__(self, model_path, store_path, collection='day7_dense'):
        from sentence_transformers import SentenceTransformer
        from qdrant_client import QdrantClient, models
        model_path = Path(model_path).resolve()
        if not (model_path / 'model.safetensors').is_file():
            raise FileNotFoundError('Missing real local model weights')
        if not Path(store_path).is_dir():
            raise FileNotFoundError('Run scripts/connect_day6.py first')
        self.model = SentenceTransformer(str(model_path), local_files_only=True)
        self.dimensions = self.model.get_embedding_dimension()
        self.client = QdrantClient(path=str(store_path))
        self.collection = collection
        if not self.client.collection_exists(collection):
            self.close()
            raise ValueError('Dense collection is missing')
        config = self.client.get_collection(collection).config.params.vectors
        if config.size != self.dimensions or config.distance != models.Distance.COSINE:
            self.close()
            raise ValueError('Embedding and collection dimensions/cosine metric differ')

    def search(self, query, *, filters=None, top_k=3):
        from qdrant_client import models
        if not isinstance(query, str) or not query.strip():
            raise ValueError('Query must be nonempty text')
        if type(top_k) is not int or not 1 <= top_k <= 100:
            raise ValueError('top_k must be an integer from 1 to 100')
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters)-{'top_level_section','language'}:
            raise ValueError('Unsupported metadata filter')
        if any(not isinstance(v,str) for v in filters.values()):
            raise ValueError('Filter values must be strings')
        conditions = [models.FieldCondition(key=key, match=models.MatchValue(value=value)) for key,value in filters.items()]
        query_filter = models.Filter(must=conditions) if conditions else None
        vector = self.model.encode(query, normalize_embeddings=True, show_progress_bar=False).tolist()
        if len(vector) != self.dimensions or not all(math.isfinite(v) for v in vector):
            raise ValueError('Invalid embedding from model')
        hits = self.client.query_points(self.collection, query=vector, query_filter=query_filter,
                                        limit=top_k, with_payload=True).points
        result = []
        for point in hits:
            p = point.payload
            result.append({'id':p['chunk_id'],'source_id':p['document_id'],'source':p['source'],
                           'page':p['page'],'text':p['text'],'score':point.score,
                           'metadata':{k:v for k,v in p.items() if k not in {'chunk_id','document_id','source','page','text'}}})
        return result

    def close(self):
        self.client.close()
