"""Run real agents on dev only, checkpointing every case; never feed labels to LLM."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'starter'))
from src.openai_controller import OpenAIController
from src.dense import DenseRetriever
from src.retrieval import LexicalRetriever,HybridRetriever
from src.citation_aliases import CitationAliasRetriever
from agentic import run_agent
from scripts.run_agent_demo import load_env


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-path',type=Path,required=True)
    parser.add_argument('--max-cost-usd',type=float,default=1.0)
    args=parser.parse_args()
    load_env()
    controller=OpenAIController() # Validate key without printing it.
    # Previously checked standard rates; estimates, not invoices, and no cache discount.
    os.environ.setdefault('AGENT_INPUT_USD_PER_MILLION','0.4')
    os.environ.setdefault('AGENT_OUTPUT_USD_PER_MILLION','1.6')
    if not os.environ.get('AGENT_INPUT_USD_PER_MILLION'):os.environ['AGENT_INPUT_USD_PER_MILLION']='0.4'
    if not os.environ.get('AGENT_OUTPUT_USD_PER_MILLION'):os.environ['AGENT_OUTPUT_USD_PER_MILLION']='1.6'
    configs=json.loads((ROOT/'results/retrieval_dev/plan.json').read_text())['configs']
    cases=[q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='dev']
    chunks=json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))
    assert len(cases)==17
    out=ROOT/'results/agent_dev';out.mkdir(exist_ok=True,parents=True)
    paths=[ROOT/'src/openai_controller.py',ROOT/'src/citation_aliases.py',ROOT/'src/retrieval.py',ROOT/'src/dense.py',ROOT/'starter/agentic.py',ROOT/'starter/baseline.py',Path(__file__)]
    plan={'stage':'agent_dev_only','model':controller.model,'configs':configs,'max_searches':2,
          'benchmark_sha256':digest(ROOT/'benchmark/questions.json'),'chunks_sha256':digest(ROOT/'data/chunks.json'),
          'code_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in paths},
          'input_rate_usd_per_million':float(os.environ['AGENT_INPUT_USD_PER_MILLION']),
          'output_rate_usd_per_million':float(os.environ['AGENT_OUTPUT_USD_PER_MILLION']),
          'rate_note':'Standard model rates checked 2026-11-14; estimate without cache discounts, not billing invoice.',
          'selection_rule':'AI-assisted reviewed answer-grade mean, then correct abstention count, supported citation rate, prepared final-context evidence rate, then lower estimated cost, then name. Student validation remains necessary.',
          'test_executed':False,'gold_sent_to_model':False,'citation_policy':'Stable C001 aliases with reversible original chunk IDs'}
    plan_file=out/'plan.json'
    if plan_file.exists() and json.loads(plan_file.read_text())!=plan:raise ValueError('Run identity differs from stored plan; use a separate experiment directory')
    plan_file.write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
    trace_file=out/'traces.jsonl'
    done=[json.loads(line) for line in trace_file.read_text(encoding='utf-8').splitlines()] if trace_file.exists() else []
    done_ids={(t['config_id'],t['query_id']) for t in done}
    if len(done_ids)!=len(done):raise ValueError('Duplicate saved traces')
    total_cost=sum(t['usage'].get('estimated_service_cost_usd') or 0 for t in done)
    initialize=time.perf_counter()
    dense=DenseRetriever(args.model_path,ROOT/'local_vectors')
    lexical=LexicalRetriever(chunks);hybrid=HybridRetriever(dense,lexical)
    initialization_seconds=time.perf_counter()-initialize
    retrievers={'dense':dense,'lexical':lexical,'hybrid':hybrid}
    try:
        for config in configs:
            runtime=CitationAliasRetriever(retrievers[config['method']],chunks)
            for q in cases:
                if (config['id'],q['id']) in done_ids:continue
                # Conservative extra reservation for at most three model calls.
                if total_cost+0.02>args.max_cost_usd:raise RuntimeError('Estimated cost cap reached; completed cases preserved')
                start=time.perf_counter();c=OpenAIController(q.get('filter'))
                try:
                    r=run_agent(q['question'],c,runtime,filters=q.get('filter'),max_searches=2,top_k=config['top_k'],budget=config['budget_chars'])
                except Exception as error:
                    r={'status':'error','answer':'','citations':[],'events':[], 'error_type':type(error).__name__,'error':str(error)}
                searches=[e for e in r['events'] if e['event']=='search']
                record=dict(r,query_id=q['id'],config_id=config['id'],split='dev',question=q['question'],filters=q.get('filter'),
                            method=config['method'],top_k=config['top_k'],budget_chars=config['budget_chars'],max_searches=2,
                            final_context=searches[-1]['context'] if searches else '',final_context_ids=searches[-1]['context_ids'] if searches else [],
                            citation_aliases=runtime.alias_to_original,model_calls=c.calls,usage=c.cost_and_usage(),
                            completed_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-start)
                with trace_file.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')
                done.append(record);done_ids.add((config['id'],q['id']));total_cost+=record['usage']['estimated_service_cost_usd'] or 0
                progress={'completed':len(done),'expected':len(configs)*len(cases),'config':config['id'],'query':q['id'],'status':record['status'],'estimated_total_usd':total_cost,'test_executed':False,'agent_answers_reviewed':False}
                (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n')
                print(json.dumps(progress),flush=True)
                if record['status']=='error':raise RuntimeError('Real API/retrieval error recorded; stop rather than run more paid cases')
        (out/'run_manifest.json').write_text(json.dumps(dict(plan,initialization_seconds=initialization_seconds,trace_count=len(done),estimated_total_usd=total_cost,completed_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
    finally:dense.close()


if __name__=='__main__':main()
