"""Offline parser tests only; no paid API calls or model-quality claims."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.openai_controller import interpret


def message(name,args):
    return {'tool_calls':[{'function':{'name':name,'arguments':json.dumps(args)}}]}


class ControllerTests(unittest.TestCase):
    def test_search_query_is_taken_from_real_tool_arguments(self):
        self.assertEqual(interpret(message('search',{'query':'refresh token'})),{'action':'search','query':'refresh token'})

    def test_abstention_never_keeps_model_citations(self):
        result=interpret(message('finish',{'status':'abstain','answer':'No evidence','citations':['bad']}))
        self.assertEqual(result['citations'],[])

    def test_missing_or_multiple_tools_are_rejected(self):
        with self.assertRaises(ValueError):interpret({'content':'unstructured answer'})
        one=message('search',{'query':'x'})['tool_calls'][0]
        with self.assertRaises(ValueError):interpret({'tool_calls':[one,one]})

    def test_gold_like_extra_search_parameters_are_rejected(self):
        with self.assertRaises(ValueError):interpret(message('search',{'query':'x','gold':'answer'}))


if __name__=='__main__':unittest.main()
