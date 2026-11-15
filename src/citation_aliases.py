"""Short, reversible citation IDs for runtime context; original corpus IDs unchanged."""
class CitationAliasRetriever:
    def __init__(self,retriever,chunks):
        self.retriever=retriever
        ids=sorted(c['id'] for c in chunks)
        if len(set(ids))!=len(ids):raise ValueError('Duplicate corpus IDs')
        self.alias_to_original={f'C{i:03d}':cid for i,cid in enumerate(ids,1)}
        self.original_to_alias={cid:alias for alias,cid in self.alias_to_original.items()}

    def search(self,query,*,filters=None,top_k=3):
        hits=self.retriever.search(query,filters=filters,top_k=top_k)
        return [dict(c,id=self.original_to_alias[c['id']],original_chunk_id=c['id']) for c in hits]
