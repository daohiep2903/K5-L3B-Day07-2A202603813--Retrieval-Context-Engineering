"""Encode explicitly inspected dev answer reviews; abstentions follow rubric, not Hit@3."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'starter'))
from agent_metrics import aggregate

# Decisions after directly reading the saved answers and every cited source chunk.
DECISIONS={
 ('dense_baseline','d7-dev-q02'):(0,[False],'Incorrectly says there is no explicit limit; section 2.3 prohibits more than one method. C090 discusses other methods, not that limit.'),
 ('dense_baseline','d7-dev-q15'):(1,[False],'Partially recognizes the need to understand token type, but only infers it from token-type definitions; cited C068 does not supply the explicit MUST NOT rule.'),
 ('lexical_baseline','d7-dev-q15'):(1,[False],'Concludes should not use an unknown token type but weakens the explicit MUST NOT rule and infers the prohibition from C062 rather than citing the direct rule.'),
 ('hybrid_baseline','d7-dev-q15'):(0,[False],'Explicitly says specification does not forbid use; this contradicts section 7.1. C068 does not support that claim.'),
 ('dense_context_3000','d7-dev-q01'):(2,[True,True],'Correctly states non-secret identifier and MUST NOT use alone; C071 supports it, and C059 supports the additional confidential/public-client qualifications.'),
 ('hybrid_top6_context_3000','d7-dev-q01'):(1,[True],'C071 supports the core identifier answer. Grade reduced because an additional generalized secret/password requirement is not supported; valid citation IDs/references do not establish complete claim coverage.'),
 ('hybrid_top6_context_3000','d7-dev-q04'):(2,[True],'Correct body-only placement, URI prohibition and NOT RECOMMENDED caveat, all supported by C066.'),
 ('hybrid_top6_context_3000','d7-dev-q09'):(2,[True],'Correctly states implicit grant does not issue refresh tokens; C091 directly supports it.'),
 ('hybrid_top6_context_3000','d7-dev-q15'):(2,[True],'Preserves explicit MUST NOT for unknown token type, directly supported by C076.'),
}


def main():
    if (ROOT/'results/student_dev_review_confirmation.json').exists():
        raise RuntimeError('Student-approved labels exist; preserve them and write any new review to a separate experiment version.')
    out=ROOT/'results/agent_dev'
    traces=[json.loads(line) for line in (out/'traces.jsonl').read_text(encoding='utf-8').splitlines()]
    cases=[q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='dev']
    by_id={q['id']:q for q in cases}
    reviews=[]
    for t in traces:
        q=by_id[t['query_id']]
        r={'query_id':q['id'],'config_id':t['config_id'],'reviewer':'AI-assisted direct source review; student confirmation pending','citation_support':[], 'reviewed_at':'2026-11-15'}
        if q['answerable']:
            if t['status']=='abstain':
                event=t['events'][-1]['event'] if t['events'] else 'no_event'
                r.update(answer_grade=0,reason='Answerable question was refused; rubric assigns 0. Final controller event: '+event+'. Even when raw model text contains the right answer, the delivered output is an abstention.')
            elif t['status']=='answered':
                grade,support,reason=DECISIONS[(t['config_id'],q['id'])]
                assert len(support)==len(t['citations'])
                r.update(answer_grade=grade,citation_support=support,reason=reason)
            else:continue
        else:
            r.update(abstention_correct=t['status']=='abstain' and not t['citations'],reason='Selected corpus does not supply requested PKCE/JWT requirement; delivered output explicitly refuses without additional unsupported claims.' if t['status']=='abstain' else 'Agent did not abstain on missing-evidence case.')
        reviews.append(r)
    reports=[]
    for config in dict.fromkeys(t['config_id'] for t in traces):
        ts=[t for t in traces if t['config_id']==config];rs=[r for r in reviews if r['config_id']==config]
        directory=out/config;directory.mkdir(exist_ok=True)
        for name,data in [('cases.json',cases),('traces.json',ts),('reviews.json',rs)]:
            (directory/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        report=dict(config_id=config,review_status='AI-assisted direct reading; not yet student-confirmed',**aggregate(cases,ts,rs))
        (directory/'summary.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
        reports.append(report)
    (out/'review_summaries.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(reports,indent=2))


if __name__=='__main__':main()
