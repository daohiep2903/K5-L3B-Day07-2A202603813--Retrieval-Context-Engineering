"""Source-based test audit, never change model/runtime after seeing test results."""
import json
import hashlib
from pathlib import Path
import statistics
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'starter'))
from agent_metrics import aggregate

SELECTED={
 'd7-test-01':(1,[False],'Core scope answer is correct, but cites C002, which gives general scope use without the MUST/changed-scope condition. The actual conditional rule is in C041 in context, not cited.'),
 'd7-test-02':(2,[True],'C028 directly supports SHOULD inform resource owner and MUST NOT automatically redirect, with all missing/invalid/mismatch conditions preserved.'),
 'd7-test-03':(2,[True],'C055 supports absolute URI defined by server as grant_type plus required additional parameters.'),
 'd7-test-04':(1,[True,False,True],'Correct required-if-present/exact-value rule and example are supported by C035; C031 supports code-response setting. C015 is implicit-error-flow context, not authorization-code scope. Added CSRF rationale is not in supplied context, so not fully grounded.'),
 'd7-test-05':(2,[True],'C063 directly defines unauthorized_client for requesting an authorization code using that method.'),
}
BASE_CONTEXT={
 'd7-test-01':(1,'C002 mentions actual scope and response parameter, but the conditional MUST rule for scope changes is absent.'),
 'd7-test-02':(2,'C028 contains the complete redirect-error rule and source.'),
 'd7-test-03':(2,'C055 contains the absolute-URI grant_type rule and additional-parameter condition.'),
 'd7-test-04':(2,'C035 contains required-if-present and exact echo-value rule with code redirect example.'),
 'd7-test-05':(0,'Context contains client-credentials authentication, not the authorization-code error definition.'),
}


def hit(c,gold):
    return any(c['source_id']==g['source_id'] and c['page']==g['page'] and ' '.join(g['evidence'].split()) in ' '.join(c['text'].split()) for g in gold)


def main():
    out=ROOT/'results/agent_test'
    if (ROOT/'results/student_test_review_confirmation.json').exists():raise RuntimeError('Approved test labels exist; do not overwrite')
    traces=[json.loads(line) for line in (out/'traces.jsonl').read_text(encoding='utf-8').splitlines()]
    cases=[q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='test']
    by_id={q['id']:q for q in cases}
    chunks={c['id']:c for c in json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))}
    assert len(traces)==14 and all(t['split']=='test' for t in traces)
    reviews=[];checks=[]
    for t in traces:
        q=by_id[t['query_id']]
        r={'query_id':q['id'],'config_id':t['config_id'],'reviewer':'Source-based review; student confirmation pending','reviewed_at':'2026-11-15','citation_support':[]}
        baseline=t['config_id']=='dense_baseline'
        if q['answerable']:
            if baseline:
                assert t['status']=='abstain'
                r.update(answer_grade=0,reason='Answerable question was delivered as an abstention; rubric assigns 0, even when evidence/raw answer existed before output checks.')
                cg,cr=BASE_CONTEXT[q['id']]
                r.update(context_grade=cg,context_reason=cr)
            else:
                assert t['status']=='answered'
                grade,support,reason=SELECTED[q['id']]
                assert len(support)==len(t['citations'])
                r.update(answer_grade=grade,citation_support=support,reason=reason,context_grade=2,context_reason='Direct reading: final context contains complete evidence and traceable source for the primary question, including the exact scope condition in C041 for test-01.')
        else:
            assert t['status']=='abstain' and not t['citations']
            r.update(abstention_correct=True,reason='Actual output explicitly refuses without unsupported claims; selected source has no DPoP typ requirement or universal fixed refresh-token lifetime in days.')
        reviews.append(r)
        searches=[e for e in t['events'] if e['event']=='search']
        hitmap={c['id']:c for e in searches for c in e['results']}
        for alias,c in hitmap.items():
            original=t['citation_aliases'][alias]
            assert c['original_chunk_id']==original and c['text']==chunks[original]['text']
            assert (c['source_id'],c['page'],c['source'])==(chunks[original]['source_id'],chunks[original]['page'],chunks[original]['source'])
        last_user=json.loads(t['model_calls'][-1]['request_messages'][-1]['content'])
        assert set(last_user)=={'question','user_supplied_filters','retrieval_observations'}
        assert last_user['retrieval_observations'][-1]['context']==t['final_context']
        assert len(t['final_context'])<=t['budget_chars']
        for cid in t['citations']:assert cid in t['final_context_ids'] and f'[{cid}]' in t['answer']
        original=t['original_query_results'];first=searches[0]['results'] if searches else []
        checks.append({'query_id':q['id'],'config_id':t['config_id'],'answerable':q['answerable'],
                       'original_hit1':bool(original and hit(original[0],q['gold'])) if q['answerable'] else None,
                       'original_hit3':any(hit(c,q['gold']) for c in original[:3]) if q['answerable'] else None,
                       'agent_first_hit1':bool(first and hit(first[0],q['gold'])) if q['answerable'] else None,
                       'agent_first_hit3':any(hit(c,q['gold']) for c in first[:3]) if q['answerable'] else None,
                       'context_full_quote_hit':any(hit(hitmap[cid],q['gold']) for cid in t['final_context_ids']) if q['answerable'] else None,
                       'search_count':len(searches),'first_query_rewritten':bool(searches and searches[0]['query']!=t['question'])})
    reports=[]
    for config in dict.fromkeys(t['config_id'] for t in traces):
        ts=[t for t in traces if t['config_id']==config];rs=[r for r in reviews if r['config_id']==config]
        cs=[c for c in checks if c['config_id']==config and c['answerable']]
        report=dict(config_id=config,review_status='AI-assisted direct source review; student confirmation pending',**aggregate(cases,ts,rs))
        for label,key in [('original_query_hit1','original_hit1'),('original_query_hit3','original_hit3'),('agent_first_search_hit1','agent_first_hit1'),('agent_first_search_hit3','agent_first_hit3'),('context_full_quote_evidence','context_full_quote_hit')]:
            report[label]={'n':sum(c[key] for c in cs),'N':len(cs),'rate':sum(c[key] for c in cs)/len(cs)}
        context=[r for r in rs if 'context_grade' in r]
        report['context_review']={'0':sum(r['context_grade']==0 for r in context),'1':sum(r['context_grade']==1 for r in context),'2':sum(r['context_grade']==2 for r in context),'N':5,'mean':sum(r['context_grade'] for r in context)/5,'evidence_rate':sum(r['context_grade']==2 for r in context)/5}
        report['model_calls']=sum(len(t['model_calls']) for t in ts)
        report['retrieval_call_counts']=[c['search_count'] for c in checks if c['config_id']==config]
        report['median_seconds']=statistics.median(t['elapsed_seconds'] for t in ts)
        report['estimated_cost_usd']=sum(t['usage']['estimated_service_cost_usd'] for t in ts)
        directory=out/config;directory.mkdir(exist_ok=True)
        for name,data in [('cases.json',cases),('traces.json',ts),('reviews.json',rs),('summary.json',report)]:
            (directory/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        reports.append(report)
    for name,data in [('reviews.json',reviews),('mechanical_checks.json',checks),('summary.json',{'test_tuning':False,'review_status':'AI-assisted direct source review; student confirmation pending','configs':reports,'total_traces':14,'estimated_total_usd':sum(r['estimated_cost_usd'] for r in reports)})]:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
