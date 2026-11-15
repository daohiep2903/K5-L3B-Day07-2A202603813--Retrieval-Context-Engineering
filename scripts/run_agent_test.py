"""Evaluate only frozen baseline/selected configs on test; no test-driven tuning."""
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
from src.formatted_controller import FormattedOpenAIController
from src.dense import DenseRetriever
from src.retrieval import LexicalRetriever,HybridRetriever
from src.citation_aliases import CitationAliasRetriever
from scripts.run_agent_demo import load_env
from agentic import run_agent


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_frozen(selection):
    if 'student_approved' not in selection['status']:raise ValueError('Dev selection has not been approved')
    for filename,expected in selection['runtime_code_sha256'].items():
        if digest(ROOT/filename)!=expected:raise ValueError('Frozen runtime changed: '+filename)
    if digest(ROOT/'benchmark/questions.json')!=selection['benchmark_sha256']:raise ValueError('Benchmark changed since dev selection')
    if digest(ROOT/'data/chunks.json')!=selection['chunks_sha256']:raise ValueError('Corpus changed since dev selection')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-path',required=True,type=Path)
    parser.add_argument('--max-cost-usd',type=float,default=0.2)
    args=parser.parse_args()
    selection=json.loads((ROOT/'results/dev_selection.json').read_text())
    validate_frozen(selection)
    load_env();controller=OpenAIController()
    if controller.model!=selection['agent_model']:raise ValueError('Agent model differs from frozen dev model')
    rates=json.loads((ROOT/'results/agent_dev/plan.json').read_text())
    os.environ['AGENT_INPUT_USD_PER_MILLION']=str(rates['input_rate_usd_per_million'])
    os.environ['AGENT_OUTPUT_USD_PER_MILLION']=str(rates['output_rate_usd_per_million'])
    cases=[q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='test']
    assert len(cases)==7 and sum(q['answerable'] for q in cases)==5
    chunks=json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))
    configs=[dict(selection['baseline_runtime'],id=selection['baseline_config']),dict(selection['selected_runtime'],id=selection['selected_config'])]
    out=ROOT/'results/agent_test';out.mkdir(exist_ok=True,parents=True)
    plan={'stage':'test_frozen_no_tuning','model':controller.model,'configs':configs,
          'benchmark_sha256':selection['benchmark_sha256'],'chunks_sha256':selection['chunks_sha256'],
          'runtime_code_sha256':selection['runtime_code_sha256'],'input_rate_usd_per_million':rates['input_rate_usd_per_million'],
          'output_rate_usd_per_million':rates['output_rate_usd_per_million'],'test_case_count':7,
          'gold_sent_to_model':False,'selection_status_before_test':selection['status']}
    plan_path=out/'plan.json'
    if plan_path.exists() and json.loads(plan_path.read_text())!=plan:raise ValueError('Existing test run has different identity; do not overwrite')
    plan_path.write_text(json.dumps(plan,indent=2)+'\n')
    if not (out/'dev_selection_snapshot.json').exists():(out/'dev_selection_snapshot.json').write_text(json.dumps(selection,indent=2)+'\n')
    trace_file=out/'traces.jsonl'
    done=[json.loads(line) for line in trace_file.read_text(encoding='utf-8').splitlines()] if trace_file.exists() else []
    ids={(t['config_id'],t['query_id']) for t in done}
    if len(ids)!=len(done):raise ValueError('Duplicate test traces')
    cost=sum(t['usage']['estimated_service_cost_usd'] or 0 for t in done)
    init=time.perf_counter();dense=DenseRetriever(args.model_path,ROOT/'local_vectors')
    lexical=LexicalRetriever(chunks);hybrid=HybridRetriever(dense,lexical)
    init_seconds=time.perf_counter()-init
    retrievers={'dense':dense,'lexical':lexical,'hybrid':hybrid}
    try:
        for config in configs:
            runtime=CitationAliasRetriever(retrievers[config['method']],chunks)
            factory={'OpenAIController':OpenAIController,'FormattedOpenAIController':FormattedOpenAIController}[config['controller']]
            for q in cases:
                if (config['id'],q['id']) in ids:continue
                if cost+0.02>args.max_cost_usd:raise RuntimeError('Estimated test cost cap reached')
                original_start=time.perf_counter()
                original=runtime.search(q['question'],filters=q.get('filter'),top_k=config['top_k'])
                original_ms=(time.perf_counter()-original_start)*1000
                c=factory(q.get('filter'));start=time.perf_counter()
                try:r=run_agent(q['question'],c,runtime,filters=q.get('filter'),max_searches=config['max_searches'],top_k=config['top_k'],budget=config['budget_chars'])
                except Exception as error:r={'status':'error','answer':'','citations':[],'events':[],'error_type':type(error).__name__,'error':str(error)}
                searches=[e for e in r['events'] if e['event']=='search']
                record=dict(r,query_id=q['id'],config_id=config['id'],split='test',question=q['question'],filters=q.get('filter'),
                            runtime=config,original_query_results=original,original_query_elapsed_ms=original_ms,
                            final_context=searches[-1]['context'] if searches else '',final_context_ids=searches[-1]['context_ids'] if searches else [],
                            budget_chars=config['budget_chars'],citation_aliases=runtime.alias_to_original,model_calls=c.calls,
                            formatting_events=getattr(c,'formatting_events',[]),usage=c.cost_and_usage(),
                            elapsed_seconds=time.perf_counter()-start,completed_at_utc=datetime.now(timezone.utc).isoformat())
                with trace_file.open('a',encoding='utf-8') as stream:stream.write(json.dumps(record,ensure_ascii=False)+'\n')
                done.append(record);ids.add((config['id'],q['id']));cost+=record['usage']['estimated_service_cost_usd'] or 0
                progress={'completed':len(done),'expected':14,'query_id':q['id'],'config':config['id'],'status':record['status'],'estimated_total_usd':cost,'test_tuning':False}
                (out/'progress.json').write_text(json.dumps(progress,indent=2)+'\n');print(json.dumps(progress),flush=True)
                if record['status']=='error':raise RuntimeError('Actual API/retrieval error recorded; stop instead of inventing a result')
        (out/'run_manifest.json').write_text(json.dumps(dict(plan,trace_count=len(done),estimated_total_usd=cost,initialization_seconds=init_seconds,completed_at_utc=datetime.now(timezone.utc).isoformat()),indent=2)+'\n')
    finally:dense.close()


if __name__=='__main__':main()
