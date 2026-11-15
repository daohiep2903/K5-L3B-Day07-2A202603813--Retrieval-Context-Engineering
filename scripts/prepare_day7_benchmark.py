"""Build Day 7 labels without retrieval calls or passing gold to the agent."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def normalize(s):
    return ' '.join(s.split())


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--day6',required=True,type=Path)
    args=parser.parse_args()
    source=(ROOT/'data/oauth2_sections_2_to_7.txt').read_text(encoding='utf-8')
    chunks=json.loads((ROOT/'data/chunks.json').read_text(encoding='utf-8'))
    old=[json.loads(line) for line in (args.day6/'benchmark/questions.jsonl').read_text(encoding='utf-8').splitlines()]
    headings=list(re.finditer(r'^(\d+(?:\.\d+)*)\.  .+$',source,re.M))
    paragraphs=list(re.finditer(r'\S[^\n]*(?:\n(?![ \t]*\n)[^\n]*)*',source))

    def resolve(quote,section=None):
        matches=[]
        for m in re.finditer(re.escape(quote),source):
            actual=[h.group(1) for h in headings if h.start()<=m.start()][-1]
            if section and actual!=section:continue
            contained=[c for c in chunks if c['metadata']['char_start']<=m.start() and m.end()<=c['metadata']['char_end_exclusive']]
            if not contained:raise ValueError('Evidence not contained in any chunk')
            for c in contained:
                matches.append({'source_id':c['source_id'],'page':c['page'],'evidence':quote,'section':actual,'chunk_id':c['id'],'char_start':m.start(),'char_end_exclusive':m.end()})
        if not matches:raise ValueError('Cannot resolve evidence in source')
        return list({(g['page'],g['char_start'],g['evidence']):g for g in matches}.values())

    questions=[]
    restrict={'q05':'2.3.1','q06':'3.1'}
    for q in old:
        if q['split']!='dev':continue
        gold=[]
        for g in q['gold_evidence']:
            if q['id'] in restrict and g['section']!=restrict[q['id']]:continue
            quote=g['evidence_quote']
            if q['id']=='q08':
                m=re.search(r'A\s+maximum authorization code lifetime of 10 minutes is\s+RECOMMENDED\.',quote)
                if not m:raise ValueError('Missing complete code lifetime recommendation')
                quote=m.group()
            gold+=resolve(quote,g['section'])
        gold=list({(g['page'],g['char_start'],g['evidence']):g for g in gold}.values())
        questions.append({'id':'d7-dev-'+q['id'],'split':'dev','answerable':True,'question':q['question'],
                          'expected_answer':q['expected_answer'],'gold':gold,'filter':q.get('filter'),
                          'expected_behavior':'search_and_answer','origin':'Day 6 dev question, reviewed for Day 7; never claimed unseen',
                          'annotation_note':'Context-inappropriate alternatives removed; q08 complete recommendation sentence selected.'})

    test_specs=[
      ('scope is different from the one requested','3.3','According to section 3, what must the server include when the granted access-token scope differs from the requested scope?','The scope response parameter, to inform the client of the actual scope granted.','3'),
      ('automatically redirect the user-agent to the invalid redirection URI.','3.1.2.4','According to section 3, what should happen when an authorization request has a missing, invalid, or mismatching redirect URI?','The server SHOULD inform the resource owner of the error and MUST NOT automatically redirect to the invalid URI.','3'),
      ('using an absolute URI (defined by the authorization server)','4.5','How does a client identify an extension grant type at the token endpoint?','Use an absolute URI defined by the authorization server as grant_type and add required additional parameters.',None),
      ('The exact value received from the client.','4.1.2','In an authorization-code response, when is state required and what value must it carry?','When state was present in the client authorization request; return the exact received value.',None),
      ('The client is not authorized to request an authorization code','4.1.2.1','Which authorization-code error means the client is not authorized to request a code using that method?','unauthorized_client.',None),
    ]
    for i,(anchor,section,query,answer,filt) in enumerate(test_specs,1):
        found=[]
        for m in paragraphs:
            quote=m.group().strip()
            actual=[h.group(1) for h in headings if h.start()<=m.start()][-1]
            if actual==section and anchor in normalize(quote):found+=resolve(quote,section)
        if not found:raise ValueError('Test evidence missing: '+anchor)
        questions.append({'id':f'd7-test-{i:02d}','split':'test','answerable':True,'question':query,'expected_answer':answer,
                          'gold':found,'filter':{'top_level_section':filt} if filt else None,'expected_behavior':'search_and_answer',
                          'origin':'New Day 7 question; not reused from Day 6 test'})
    absent=[
      ('dev','Which exact code_verifier length does this corpus require for the PKCE S256 flow?', ['PKCE','code_verifier','code_challenge','S256'], 'The selected RFC sections contain no PKCE S256 or code_verifier requirements.'),
      ('dev','Which JWT signing algorithm does this corpus require for access tokens?', ['JWT','RS256','HS256','ES256'], 'No JWT signing algorithm is specified in the selected text. Token examples are not a mandate for a JWT algorithm.'),
      ('test','Which typ header value does this corpus mandate for a DPoP proof JWT?', ['DPoP','dpop+jwt'], 'No DPoP proof format or mandated typ value is specified in the selected text.'),
      ('test','What fixed maximum refresh-token lifetime in days does this corpus mandate for every client?', ['refresh token','lifetime','expires','days'], 'The source discusses refresh-token binding, replacement and invalid/expired tokens, but supplies no universal fixed maximum refresh-token lifetime in days. Do not substitute the code lifetime or access-token examples.'),
    ]
    absence_reviews=[]
    for i,(split,query,terms,reason) in enumerate(absent,1):
        qid=f'd7-{split}-abs-{i:02d}'
        checks={term:len(list(re.finditer(re.escape(term),source,re.I))) for term in terms}
        questions.append({'id':qid,'split':split,'answerable':False,'question':query,'gold':[],
                          'expected_behavior':'search_and_abstain','expected_answer':'The supplied corpus does not provide sufficient evidence to answer this question.',
                          'absence_reason':reason,'filter':None})
        absence_reviews.append({'query_id':qid,'absence_reason':reason,'scope':'Entire selected sections 2-7, not the whole Internet or all OAuth specifications',
                                'method':'AI-assisted reading of selected source and relevant sections plus full-corpus keyword checks; not inferred from failed top-k retrieval',
                                'keyword_counts':checks,'reviewer':'AI-assisted; student review pending'})
    assert len(questions)==24
    for split,a,b in [('dev',15,2),('test',5,2)]:
        assert sum(q['split']==split and q['answerable'] for q in questions)==a
        assert sum(q['split']==split and not q['answerable'] for q in questions)==b
    assert len({q['id'] for q in questions})==24
    assert len({normalize(q['question']).lower() for q in questions})==24
    for q in questions:
        for g in q['gold']:
            assert source[g['char_start']:g['char_end_exclusive']]==g['evidence']
            assert any(c['source_id']==g['source_id'] and c['page']==g['page'] and g['evidence'] in c['text'] for c in chunks)
            if q['filter']:assert g['section'].split('.')[0]==q['filter']['top_level_section']
    destination=ROOT/'benchmark';destination.mkdir(exist_ok=True)
    output=destination/'questions.json'
    if output.exists() and json.loads(output.read_text(encoding='utf-8'))!=questions:
        raise ValueError('Refusing to overwrite a modified benchmark; preserve frozen labels')
    output.write_text(json.dumps(questions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cases=[{k:q[k] for k in ['id','split','answerable','question','expected_behavior']} for q in questions]
    # Runtime runner must still pass only question/filter to the agent, never cases labels.
    (destination/'cases.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (destination/'absence_review.json').write_text(json.dumps(absence_reviews,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    record={'question_count':24,'dev':{'answerable':15,'unanswerable':2},'test':{'answerable':5,'unanswerable':2},
            'benchmark_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
            'source_sha256':hashlib.sha256((ROOT/'data/oauth2_sections_2_to_7.txt').read_bytes()).hexdigest(),
            'exact_evidence_verified':True,'chunk_containment_verified':True,'filter_scope_verified':True,
            'queries_run_against_benchmark':False,'agent_run':False,'gold_review':'AI-assisted; student review pending',
            'caveat':'New test questions have not been retrieved or tuned against, but share a document with known Day 6 topics and are visible to the dataset author. Not blind external validation.'}
    (destination/'validation.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
