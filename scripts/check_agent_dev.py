"""Mechanical integrity/context checks only, never automatic semantic answer grades."""
import argparse
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def hit(chunk,gold):
    return any(chunk['source_id']==g['source_id'] and chunk['page']==g['page'] and ' '.join(g['evidence'].split()) in ' '.join(chunk['text'].split()) for g in gold)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--directory',default='agent_dev',choices=['agent_dev','agent_dev_formatted'])
    args=parser.parse_args()
    out=ROOT/'results'/args.directory
    cases={q['id']:q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='dev'}
    traces=[json.loads(line) for line in (out/'traces.jsonl').read_text(encoding='utf-8').splitlines()]
    chunks={c['id']:c for c in json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))}
    checks=[]
    for t in traces:
        assert t['split']=='dev' and t['query_id'] in cases
        q=cases[t['query_id']]
        searches=[e for e in t['events'] if e['event']=='search']
        all_hits={c['id']:c for e in searches for c in e['results']}
        for alias,c in all_hits.items():
            original=t['citation_aliases'][alias]
            assert c['original_chunk_id']==original and c['text']==chunks[original]['text']
            assert (c['source_id'],c['page'],c['source'])==(chunks[original]['source_id'],chunks[original]['page'],chunks[original]['source'])
        ids=t['final_context_ids']
        assert len(t['final_context'])<=t['budget_chars'] and len(set(ids))==len(ids)
        context_evidence=any(hit(all_hits[cid],q['gold']) for cid in ids) if q['answerable'] else None
        first=searches[0]['results'] if searches else []
        valid=[cid in ids and f'[{cid}]' in t['answer'] for cid in t['citations']]
        if t['status']=='answered':assert valid and all(valid)
        checks.append({'query_id':t['query_id'],'config_id':t['config_id'],'status':t['status'],'answerable':q['answerable'],
                       'first_search_hit1':bool(first and hit(first[0],q['gold'])) if q['answerable'] else None,
                       'first_search_hit3':any(hit(c,q['gold']) for c in first[:3]) if q['answerable'] else None,
                       'context_evidence':context_evidence,'citation_ids_valid':valid,'search_count':len(searches),
                       'first_search_query':searches[0]['query'] if searches else None,
                       'query_rewritten':bool(searches and searches[0]['query']!=t['question']),
                       'semantic_grades_computed':False})
    (out/'mechanical_checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    print(f'Checked {len(checks)} real dev traces; no semantic scores inferred from citations/metrics.')


if __name__=='__main__':main()
