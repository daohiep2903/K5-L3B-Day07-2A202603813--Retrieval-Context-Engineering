import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.citation_aliases import CitationAliasRetriever


class AliasTests(unittest.TestCase):
    def test_alias_is_reversible_and_source_content_unchanged(self):
        chunks=[{'id':'long-original-b','text':'evidence','source_id':'doc','page':1}]
        class Retriever:
            def search(self,query,**kwargs):return chunks
        r=CitationAliasRetriever(Retriever(),chunks)
        hit=r.search('q')[0]
        self.assertEqual(hit['id'],'C001')
        self.assertEqual(r.alias_to_original['C001'],chunks[0]['id'])
        self.assertEqual(hit['original_chunk_id'],chunks[0]['id'])
        self.assertEqual(hit['text'],chunks[0]['text'])
        self.assertEqual(chunks[0]['id'],'long-original-b')


if __name__=='__main__':unittest.main()
