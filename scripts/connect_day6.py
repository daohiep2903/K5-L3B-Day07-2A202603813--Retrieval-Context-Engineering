"""Copy actual B vectors to a separate Day 7 store; never re-embed or alter Day 6."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from qdrant_client import QdrantClient,models
    parser=argparse.ArgumentParser()
    parser.add_argument('--day6',required=True,type=Path)
    parser.add_argument('--query',default='How does the client obtain an access token?')
    args=parser.parse_args()
    day6=args.day6.resolve()
    provenance=json.loads((ROOT/'data/day6_import.json').read_text(encoding='utf-8'))
    path=ROOT/'data/chunks.json'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=provenance['output_chunks_sha256']:
        raise ValueError('Imported corpus changed; review provenance before copying vectors')
    chunks={c['id']:c for c in json.loads(path.read_text(encoding='utf-8'))}
    model_path=day6/'local_models/all-MiniLM-L6-v2'
    manifest=json.loads((day6/'results/model_manifest.json').read_text(encoding='utf-8'))
    if manifest['revision']!=provenance['model_revision']:
        raise ValueError('Model revision mismatch')
    for filename,expected in manifest['files'].items():
        if hashlib.sha256((model_path/filename).read_bytes()).hexdigest()!=expected:
            raise ValueError('Model file hash mismatch: '+filename)
    original=QdrantClient(path=str(day6/'local_vectors'))
    try:
        name=provenance['collection_to_reuse']
        config=original.get_collection(name).config.params.vectors
        if config.size!=provenance['dimensions'] or config.distance!=models.Distance.COSINE:
            raise ValueError('Day 6 collection configuration mismatch')
        records=[]
        offset=None
        while True:
            batch,offset=original.scroll(name,offset=offset,limit=256,with_payload=True,with_vectors=True)
            records.extend(batch)
            if offset is None:break
        if len(records)!=len(chunks):raise ValueError('Point count mismatch')
        for point in records:
            payload=point.payload
            c=chunks.get(payload['chunk_id'])
            if c is None or (payload['text'],payload['document_id'],payload['page'],payload['source'])!=(c['text'],c['source_id'],c['page'],c['source']):
                raise ValueError('Vector payload does not match imported corpus')
            if any(payload.get(k)!=v for k,v in c['metadata'].items()):
                raise ValueError('Vector metadata differs')
    finally:original.close()
    target_path=ROOT/'local_vectors'
    client=QdrantClient(path=str(target_path))
    try:
        name='day7_dense'
        if not client.collection_exists(name):
            client.create_collection(name,vectors_config=models.VectorParams(size=provenance['dimensions'],distance=models.Distance.COSINE))
        cfg=client.get_collection(name).config.params.vectors
        if cfg.size!=provenance['dimensions'] or cfg.distance!=models.Distance.COSINE:
            raise ValueError('Existing Day 7 vector configuration differs')
        points=[models.PointStruct(id=p.id,vector=p.vector,payload=p.payload) for p in records]
        for start in range(0,len(points),64):client.upsert(name,points=points[start:start+64],wait=True)
        stored,_=client.scroll(name,limit=len(points)+1,with_vectors=False,with_payload=True)
        if {p.payload['chunk_id'] for p in stored}!=set(chunks):
            raise ValueError('Existing collection contains stale or missing chunks')
        # Verify persisted vectors exactly equal source vectors before search.
        copied,_=client.scroll(name,limit=len(points)+1,with_vectors=True,with_payload=False)
        by_id={str(p.id):p.vector for p in copied}
        max_vector_delta = max(abs(a-b) for p in records for a,b in zip(by_id[str(p.id)],p.vector))
        if max_vector_delta > 1e-6:
            raise ValueError('Copied vectors differ beyond floating-point tolerance')
    finally:client.close()
    from src.dense import DenseRetriever
    retriever=DenseRetriever(model_path,target_path)
    try:
        start=time.perf_counter()
        hits=retriever.search(args.query,filters=None,top_k=3)
        filtered=retriever.search('refresh token',filters={'top_level_section':'6'},top_k=3)
        if len(hits)!=3 or len(filtered)!=3:raise ValueError('Expected 3 hits')
        source=(ROOT/'data/oauth2_sections_2_to_7.txt').read_text(encoding='utf-8')
        for h in hits+filtered:
            m=h['metadata']
            if h['id'] not in chunks or source[m['char_start']:m['char_end_exclusive']]!=h['text']:
                raise ValueError('Retrieved text does not match original source')
        if not all(h['metadata']['top_level_section']=='6' for h in filtered):
            raise ValueError('Filter violated')
        elapsed=time.perf_counter()-start
    finally:retriever.close()
    # Reopen after close to check persistence, without a second model load.
    reopened=QdrantClient(path=str(target_path))
    try:assert reopened.count('day7_dense',exact=True).count==len(chunks)
    finally:reopened.close()
    out=ROOT/'results'
    out.mkdir(exist_ok=True)
    record={'kind':'connection_smoke_check_not_benchmark','completed_at_utc':datetime.now(timezone.utc).isoformat(),
            'embedding_model':provenance['embedding_model'],'revision':manifest['revision'],'dimensions':provenance['dimensions'],
            'source_collection':'day6_B','target_collection':'day7_dense','count':len(chunks),
            'vectors_reused_without_reembedding':True,'max_vector_copy_delta':max_vector_delta,'vector_copy_tolerance':1e-6,'model_files_hash_verified':True,'reopen_count_verified':True,
            'query':args.query,'hits':hits,'filter_check':{'query':'refresh token','filter':{'top_level_section':'6'},'hits':filtered},
            'search_seconds_total':elapsed,'service_cost_usd':0,'model_path':str(model_path),'store_path':'local_vectors',
            'note':'No gold/test labels used. These queries are connection checks and must not later be treated as unseen benchmark test questions.'}
    (out/'dense_connection_check.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['kind','embedding_model','dimensions','count','vectors_reused_without_reembedding','reopen_count_verified']},indent=2))
    for rank,h in enumerate(hits,1):print(f"{rank}. source={h['source_id']} unit={h['page']} section={h['metadata']['top_level_section']} score={h['score']:.4f}")


if __name__=='__main__':main()
