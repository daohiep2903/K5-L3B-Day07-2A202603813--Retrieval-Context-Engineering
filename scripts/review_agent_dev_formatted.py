"""Explicit source-based AI review of the second real dev experiment."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'starter'))
from agent_metrics import aggregate

# Read all 15 answers and all 17 cited excerpts, not inferred from Hit@3.
DECISIONS={
 'd7-dev-q01':(1,[True,False],'Identifier non-secret/MUST NOT alone is correct and supported by C071. Added generic requirement for secret/password authentication overgeneralizes C073, which is qualified to confidential/credentialed clients.'),
 'd7-dev-q02':(2,[True],'Preserves explicit MUST NOT use more than one authentication method in one request; C059 contains the direct rule.'),
 'd7-dev-q03':(2,[True],'Correct HTTP Basic support requirement for clients issued a password; encoding and username/password mapping supported by C048.'),
 'd7-dev-q04':(1,[True,True],'Correct main placement/URI rule and NOT RECOMMENDED caveat (C066), and TLS/POST rules (C011). Added form/UTF-8 encoding detail is not established by these cited excerpts, so not fully grounded; reference validity does not equal full claim coverage.'),
 'd7-dev-q05':(0,[False],'Says brute force but cites C054 in resource-owner password credentials flow, not client-password authentication. This reproduces the gold-context pitfall; source does not establish the intended client-password rule.'),
 'd7-dev-q06':(2,[True],'Direct fragment prohibition for authorization endpoint, supported by C042 in section 3.1.'),
 'd7-dev-q07':(2,[True],'POST requirement is explicit in C011.'),
 'd7-dev-q08':(2,[True],'Correct 10-minute RECOMMENDED maximum, not overstated as MUST; C031 contains the complete recommendation despite later text being clipped.'),
 'd7-dev-q09':(2,[True],'C091 directly states implicit grant does not support issuance of refresh tokens.'),
 'd7-dev-q10':(2,[True],'C088 directly requires discarding resource-owner credentials once access token is obtained.'),
 'd7-dev-q11':(2,[True],'C009 explicitly limits client credentials grant to confidential clients.'),
 'd7-dev-q12':(2,[True],'C074 supports both required headers and sensitive-response condition.'),
 'd7-dev-q13':(2,[True],'C104 defines invalid_grant including expired/revoked grant and refresh token conditions.'),
 'd7-dev-q14':(2,[True],'C101 supports discard-and-replace, optional revocation and identical replacement scope, preserving conditions.'),
 'd7-dev-q15':(2,[True],'C076 directly states the MUST NOT use unknown token type rule.'),
}


def main():
    if (ROOT/'results/student_dev_review_confirmation.json').exists():
        raise RuntimeError('Student-approved labels exist; preserve them and write any new review to a separate experiment version.')
    out=ROOT/'results/agent_dev_formatted'
    traces=[json.loads(line) for line in (out/'traces.jsonl').read_text(encoding='utf-8').splitlines()]
    cases=[q for q in json.loads((ROOT/'benchmark/questions.json').read_text(encoding='utf-8')) if q['split']=='dev']
    by_id={q['id']:q for q in cases}
    assert len(traces)==17 and all(t['split']=='dev' for t in traces)
    reviews=[]
    for t in traces:
        r={'query_id':t['query_id'],'reviewer':'AI-assisted direct source review; student confirmation pending','reviewed_at':'2026-11-15'}
        if by_id[t['query_id']]['answerable']:
            grade,support,reason=DECISIONS[t['query_id']]
            assert t['status']=='answered' and len(support)==len(t['citations'])
            r.update(answer_grade=grade,citation_support=support,reason=reason,context_grade=1 if t['query_id']=='d7-dev-q05' else 2,context_reason='AI-assisted direct context review: q05 lacks the intended client-password scope; q09 has valid equivalent evidence at section 4.2; other primary questions have supporting evidence.')
        else:
            assert t['status']=='abstain' and not t['citations']
            r.update(citation_support=[],abstention_correct=True,reason='Delivered output explicitly refuses unsupported PKCE/JWT requirement and adds no unsupported claims; checked against selected corpus absence review.')
        reviews.append(r)
    report=dict(config_id=traces[0]['config_id'],review_status='AI-assisted direct reading; not student-confirmed',**aggregate(cases,traces,reviews))
    for name,data in [('cases.json',cases),('traces.json',traces),('reviews.json',reviews),('summary.json',report)]:
        (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
