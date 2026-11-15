"""Offline ranking/filter behavior; these fixtures do not measure retrieval quality."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.retrieval import LexicalRetriever,fuse_rrf


class RetrievalTests(unittest.TestCase):
    def test_rrf_rewards_cross_method_agreement_and_keeps_components(self):
        a={'id':'a','score':0.99};b={'id':'b','score':0.01};c={'id':'c','score':500.}
        result=fuse_rrf([a,b],[c,b])
        self.assertEqual(result[0]['id'],'b')
        self.assertAlmostEqual(result[0]['score'],2/62)
        self.assertEqual(result[0]['component_ranks'],{'dense':2,'lexical':2})

    def test_filter_is_applied_before_cutoff(self):
        chunks=[{'id':'a','text':'refresh token','metadata':{'top_level_section':'5'}},
                {'id':'b','text':'refresh token scope','metadata':{'top_level_section':'6'}}]
        result=LexicalRetriever(chunks).search('refresh token',filters={'top_level_section':'6'},top_k=1)
        self.assertEqual([c['id'] for c in result],['b'])

    def test_rrf_rejects_duplicate_component_ids(self):
        with self.assertRaises(ValueError):fuse_rrf([{'id':'a','score':1},{'id':'a','score':1}],[])


if __name__=='__main__':unittest.main()
