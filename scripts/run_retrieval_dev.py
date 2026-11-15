"""Compare retrieval/context on dev only. No agent, test run or hidden gold inputs."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.dense import DenseRetriever
from src.retrieval import LexicalRetriever,HybridRetriever
from starter.baseline import pack_context

CONFIGS=[
 {'id':'dense_baseline','method':'dense','top_k':3,'budget_chars':800,'hypothesis':'Dense baseline with starter context budget.'},
 {'id':'lexical_baseline','method':'lexical','top_k':3,'budget_chars':800,'hypothesis':'Exact protocol names may favor lexical matching.'},
 {'id':'hybrid_baseline','method':'hybrid','top_k':3,'budget_chars':800,'hypothesis':'RRF can combine semantic and exact-term rankings.'},
 {'id':'dense_context_3000','method':'dense','top_k':3,'budget_chars':3000,'hypothesis':'Larger context may retain complete retrieved evidence; only budget changes from dense baseline.'},
 {'id':'hybrid_top6_context_3000','method':'hybrid','top_k':6,'budget_chars':3000,'hypothesis':'More candidates and a larger context may improve coverage. Two factors change together; not a causal isolation.'},
]


def hit(c,gold):
    return any(c['source_id']==g['source_id'] and c['page']==g['page'] and ' '.join(g['evidence'].split()) in ' '.join(c['text'].split()) for g in gold)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-path',required=True,type=Path)
    args=parser.parse_args()
    out=ROOT/'results/retrieval_dev';out.mkdir(parents=True,exist_ok=True)
    # Persist hypotheses and retrieval-only ranking rule BEFORE any dev retrieval call.
    plan={'stage':'retrieval_dev_only_not_agent_selection','configs':CONFIGS,'rrf_k':60,'rrf_candidate_depth':10,
          'query_policy':'Original question, no rewriting; explicit question filters shared across methods',
          'shortlist_rule':'Context Evidence Rate, then Hit@3, then Hit@1, then fewer context characters, then name. Agent answer quality/cost still required before final test selection.',
          'context_policy':'Whole chunks in rank order, deduplicated, skip chunks that do not fit character budget including citation headers',
          'test_execution':False}
    (out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    benchmark=ROOT/'benchmark/questions.json'
    cases=[q for q in json.loads(benchmark.read_text(encoding='utf-8')) if q['split']=='dev']
    assert len(cases)==17 and sum(q['answerable'] for q in cases)==15
    chunks=json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))
    init=time.perf_counter()
    dense=DenseRetriever(args.model_path,ROOT/'local_vectors')
    lexical=LexicalRetriever(chunks)
    hybrid=HybridRetriever(dense,lexical)
    initialized=time.perf_counter()-init
    retrievers={'dense':dense,'lexical':lexical,'hybrid':hybrid}
    traces=[]
    try:
        for config in CONFIGS:
            for q in cases:
                start=time.perf_counter()
                retriever=retrievers[config['method']]
                # No gold, answerable flag, answer or expected behavior enters the retriever.
                ranked=retriever.search(q['question'],filters=q.get('filter'),top_k=config['top_k'])
                context,ids=pack_context(ranked,config['budget_chars'])
                duration=time.perf_counter()-start
                assert len(context)<=config['budget_chars'] and len(ids)==len(set(ids))
                if q.get('filter'):assert all(all(c['metadata'][k]==v for k,v in q['filter'].items()) for c in ranked)
                relevant=[hit(c,q['gold']) for c in ranked] if q['answerable'] else []
                row={'query_id':q['id'],'split':'dev','config_id':config['id'],'method':config['method'],'query':q['question'],
                     'filters':q.get('filter'),'top_k':config['top_k'],'budget_chars':config['budget_chars'],
                     'results':ranked,'top3':ranked[:3],'context':context,'context_ids':ids,'context_chars':len(context),
                     'elapsed_ms':duration*1000,'answerable':q['answerable'],
                     'hit1':bool(relevant and relevant[0]) if q['answerable'] else None,
                     'hit3':any(relevant[:3]) if q['answerable'] else None,
                     'context_hit':any(hit(c,q['gold']) for c in ranked if c['id'] in ids) if q['answerable'] else None,
                     'agent_executed':False,'abstention_evaluated':False}
                if config['method']=='hybrid':row['component_rankings']=hybrid.last_components
                traces.append(row)
                with (out/'traces.jsonl').open('a' if len(traces)>1 else 'w',encoding='utf-8') as stream:
                    stream.write(json.dumps(row,ensure_ascii=False)+'\n')
        summary=[]
        for config in CONFIGS:
            all_rows=[t for t in traces if t['config_id']==config['id']]
            rows=[t for t in all_rows if t['answerable']]
            n=len(rows)
            result=dict(config,n_answerable=n,n_unanswerable=len(all_rows)-n,
                        hit1_count=sum(t['hit1'] for t in rows),hit3_count=sum(t['hit3'] for t in rows),
                        context_evidence_count=sum(t['context_hit'] for t in rows),
                        hit1_rate=sum(t['hit1'] for t in rows)/n,hit3_rate=sum(t['hit3'] for t in rows)/n,
                        context_evidence_rate=sum(t['context_hit'] for t in rows)/n,
                        mean_context_chars=statistics.mean(t['context_chars'] for t in all_rows),
                        median_ms=statistics.median(t['elapsed_ms'] for t in all_rows),
                        service_cost_usd=0,agent_run=False)
            summary.append(result)
        selected=sorted(summary,key=lambda r:(-r['context_evidence_count'],-r['hit3_count'],-r['hit1_count'],r['mean_context_chars'],r['id']))[0]['id']
        record={'completed_at_utc':datetime.now(timezone.utc).isoformat(),'benchmark_sha256':hashlib.sha256(benchmark.read_bytes()).hexdigest(),
                'initialization_seconds':initialized,'retrieval_shortlist_candidate':selected,'selection_status':'Provisional retrieval/context candidate only; compare real agent answers on dev before freezing final test config',
                'summaries':summary,'test_executed':False,'agent_executed':False,'trace_count':len(traces),
                'timing_note':'Single sequential pass per config; CPU/cache effects possible. Initialization recorded separately. No API cost; hardware/network costs unmeasured.'}
        (out/'summary.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(record,indent=2))
    finally:dense.close()


if __name__=='__main__':
    try:main()
    except Exception as error:
        out=ROOT/'results/retrieval_dev';out.mkdir(parents=True,exist_ok=True)
        with (out/'errors.log').open('a',encoding='utf-8') as stream:stream.write(type(error).__name__+': '+str(error)+'\n')
        raise
