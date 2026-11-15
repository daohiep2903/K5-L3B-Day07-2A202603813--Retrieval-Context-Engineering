"""Run one real OpenAI agent demo. No benchmark labels, test loop or fake answers."""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'starter'))
from src.openai_controller import OpenAIController
from src.dense import DenseRetriever
from src.citation_aliases import CitationAliasRetriever
from src.retrieval import LexicalRetriever,HybridRetriever
from agentic import run_agent


def load_env():
    path=ROOT/'.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key,value=line.split('=',1)
                os.environ.setdefault(key.strip(),value.strip().strip('"').strip("'"))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--model-path',required=True,type=Path)
    parser.add_argument('--query',default='How does the client obtain an access token?')
    parser.add_argument('--method',choices=['dense','lexical','hybrid'],default='hybrid')
    parser.add_argument('--top-k',type=int,default=6)
    parser.add_argument('--budget',type=int,default=3000)
    parser.add_argument('--max-searches',type=int,default=2)
    parser.add_argument('--section',default=None)
    args=parser.parse_args()
    load_env()
    filters={'top_level_section':args.section} if args.section else None
    controller=OpenAIController(filters)  # Fail before loading embeddings if key is missing.
    dense=None
    out=ROOT/'results/agent_demo';out.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter()
    try:
        chunks=json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))
        lexical=LexicalRetriever(chunks)
        if args.method!='lexical':dense=DenseRetriever(args.model_path,ROOT/'local_vectors')
        retriever={'dense':dense,'lexical':lexical,'hybrid':HybridRetriever(dense,lexical)}[args.method]
        retriever=CitationAliasRetriever(retriever,chunks)
        result=run_agent(args.query,controller,retriever,filters=filters,max_searches=args.max_searches,top_k=args.top_k,budget=args.budget)
        searches=[e for e in result['events'] if e['event']=='search']
        final_context=searches[-1]['context'] if searches else ''
        record=dict(result,kind='real_agent_demo_not_benchmark',question=args.query,method=args.method,filters=filters,
                    top_k=args.top_k,budget_chars=args.budget,max_searches=args.max_searches,
                    completed_at_utc=datetime.now(timezone.utc).isoformat(),elapsed_seconds=time.perf_counter()-started,
                    final_context=final_context,citation_aliases=retriever.alias_to_original,model_calls=controller.calls,usage=controller.cost_and_usage(),
                    note='Citation IDs validated by code only; semantic citation support and answer quality still require review. This is not a test benchmark query.')
        (out/'trace.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'status':result['status'],'answer':result['answer'],'citations':result['citations'],'model_calls':len(controller.calls),'usage':record['usage']},ensure_ascii=False,indent=2))
    except Exception as error:
        record={'status':'error','kind':'real_agent_demo_not_benchmark','error_type':type(error).__name__,'error':str(error),
                'model_calls':controller.calls,'usage':controller.cost_and_usage(),'elapsed_seconds':time.perf_counter()-started}
        (out/'error.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        raise
    finally:
        if dense is not None:dense.close()


if __name__=='__main__':main()
