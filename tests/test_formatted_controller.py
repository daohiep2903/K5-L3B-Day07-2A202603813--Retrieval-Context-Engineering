import sys
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.formatted_controller import FormattedOpenAIController


class FormattingTests(unittest.TestCase):
    def controller(self):
        c=object.__new__(FormattedOpenAIController);c.formatting_events=[];return c

    def test_only_declared_context_ids_are_rendered(self):
        action={'action':'answer','answer':'Claim.','citations':['C001']}
        with patch('src.openai_controller.OpenAIController.decide',return_value=action):
            result=self.controller().decide('q',[{'context_ids':['C001']}])
        self.assertEqual(result['answer'],'Claim. [C001]')
        self.assertEqual(action['answer'],'Claim.')

    def test_unknown_citation_is_not_repaired(self):
        action={'action':'answer','answer':'Claim.','citations':['C999']}
        c=self.controller()
        with patch('src.openai_controller.OpenAIController.decide',return_value=action):
            result=c.decide('q',[{'context_ids':['C001']}])
        self.assertEqual(result,action);self.assertEqual(c.formatting_events,[])

    def test_abstention_gets_no_citations(self):
        action={'action':'answer','answer':'No evidence.','citations':[]}
        with patch('src.openai_controller.OpenAIController.decide',return_value=action):
            result=self.controller().decide('q',[{'context_ids':['C001']}])
        self.assertEqual(result,action)


if __name__=='__main__':unittest.main()
