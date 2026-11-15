"""Import the actual Day 6 B corpus without importing held-out questions."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--day6', required=True, type=Path)
    args = parser.parse_args()
    day6 = args.day6.resolve()
    source_path = day6 / 'data/oauth2_sections_2_to_7.txt'
    source = source_path.read_text(encoding='utf-8')
    raw_path = day6 / 'results/chunks_B.jsonl'
    raw = [json.loads(line) for line in raw_path.read_text(encoding='utf-8').splitlines()]
    units = [json.loads(line) for line in (day6 / 'data/corpus_units.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(units) >= 30 and all(len(u['text'].strip()) >= 1500 for u in units)
    assert ''.join(u['text'] for u in units) == source
    chunks = []
    headings = list(re.finditer(r'^(\d+)(?:\.\d+)*\.  .+$', source, re.M))
    for c in raw:
        meta = c['metadata']
        start, end = meta['char_start'], meta['char_end_exclusive']
        assert source[start:end] == c['text']
        unit = units[c['page']-1]
        assert unit['char_start'] <= start < end <= unit['char_end_exclusive']
        actual_section = [h.group(1) for h in headings if h.start() <= start][-1]
        assert meta['top_level_section'] == actual_section
        chunks.append({'id': c['chunk_id'], 'source_id': c['document_id'], 'source': c['source'],
                       'page': c['page'], 'text': c['text'], 'metadata': dict(meta)})
    assert len(chunks) == 116 and len({c['id'] for c in chunks}) == len(chunks)
    destination = ROOT / 'data'
    destination.mkdir(exist_ok=True)
    output = destination / 'chunks.json'
    if output.exists():
        existing = json.loads(output.read_text(encoding='utf-8'))
        if existing != chunks:
            raise ValueError('Existing chunks.json differs; refusing to overwrite a changed corpus')
    output.write_text(json.dumps(chunks, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    copied = []
    for name in ['data_tu_tim.txt','oauth2_sections_2_to_7.txt','corpus_units.jsonl','manifest.json','corpus_selection.json','RFC6749_NOTICES.txt','RIGHTS_REVIEW.md']:
        target = destination / name
        original = day6 / 'data' / name
        if target.exists() and target.read_bytes() != original.read_bytes():
            raise ValueError(f'Existing file differs: {target.name}')
        shutil.copyfile(original, target)
        copied.append(name)
    run = json.loads((day6 / 'results/run_dev.json').read_text(encoding='utf-8'))
    model = json.loads((day6 / 'results/model_manifest.json').read_text(encoding='utf-8'))
    record = {'source_project': day6.name, 'strategy': 'B', 'chunk_count': len(chunks), 'source_unit_count': len(units),
              'source_url': 'https://www.rfc-editor.org/rfc/rfc6749.txt',
              'embedding_model': model['model_id'], 'model_revision': run['revision'], 'dimensions':run['dimensions'],
              'vector_store':run['backend'], 'collection_to_reuse':'day6_B',
              'input_chunks_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
              'selected_source_sha256':hashlib.sha256(source_path.read_bytes()).hexdigest(),
              'output_chunks_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
              'copied_files':copied, 'checks':['unique IDs','exact source offsets','unit containment','section heading','complete corpus units'],
              'page_semantics':'Sequential source unit, not original RFC physical page',
              'status':'Corpus imported and validated; vector connection and Day 7 benchmark not yet implemented',
              'benchmark_imported':False, 'note':'Day 6 held-out questions were not imported. Prepare a separate Day 7 benchmark before tuning.'}
    (destination / 'day6_import.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Imported and validated {len(chunks)} chunks, {len(units)} source units. No questions or model benchmark results imported.')


if __name__ == '__main__':
    main()
