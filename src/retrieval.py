"""Comparable lexical, dense and reciprocal-rank-fusion retrieval."""
from starter.baseline import TfidfIndex


def check_filter(filters):
    filters=filters or {}
    if not isinstance(filters,dict) or set(filters)-{'top_level_section','language'}:
        raise ValueError('Unsupported filter')
    if any(not isinstance(v,str) for v in filters.values()):raise ValueError('Filter values must be strings')
    return filters


class LexicalRetriever:
    def __init__(self,chunks):
        self.index=TfidfIndex(chunks)
        self.count=len(chunks)

    def search(self,query,*,filters=None,top_k=3):
        filters=check_filter(filters)
        # Filter before cutoff; do not retrieve top-k globally and discard matches afterward.
        ranked=self.index.search(query,top_k=self.count)
        return [c for c in ranked if all(c['metadata'].get(k)==v for k,v in filters.items())][:top_k]


def fuse_rrf(dense_results,lexical_results,k=60):
    if k<=0:raise ValueError('RRF constant must be positive')
    merged={}
    for method,rows in [('dense',dense_results),('lexical',lexical_results)]:
        if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate IDs in component ranking')
        for rank,row in enumerate(rows,1):
            item=merged.setdefault(row['id'],dict(row,score=0.,component_ranks={},component_scores={}))
            item['score']+=1./(k+rank)
            item['component_ranks'][method]=rank
            item['component_scores'][method]=row['score']
    return sorted(merged.values(),key=lambda c:(-c['score'],c['id']))


class HybridRetriever:
    def __init__(self,dense,lexical,candidate_depth=10,rrf_k=60):
        self.dense=dense;self.lexical=lexical
        self.candidate_depth=candidate_depth;self.rrf_k=rrf_k
        self.last_components={}

    def search(self,query,*,filters=None,top_k=3):
        filters=check_filter(filters)
        depth=max(self.candidate_depth,top_k)
        d=self.dense.search(query,filters=filters,top_k=depth)
        l=self.lexical.search(query,filters=filters,top_k=depth)
        self.last_components={'dense':d,'lexical':l}
        return fuse_rrf(d,l,self.rrf_k)[:top_k]
