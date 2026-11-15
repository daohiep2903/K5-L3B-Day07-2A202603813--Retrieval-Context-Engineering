"""Deterministic citation rendering after model decision; never invent a source."""
from src.openai_controller import OpenAIController


class FormattedOpenAIController(OpenAIController):
    def __init__(self,filters=None):
        super().__init__(filters)
        self.formatting_events=[]

    def decide(self,question,history):
        action=super().decide(question,history)
        if action['action']=='answer' and action.get('citations'):
            ids=set(history[-1].get('context_ids',[])) if history else set()
            if all(cid in ids for cid in action['citations']):
                missing=[cid for cid in action['citations'] if f'[{cid}]' not in action['answer']]
                if missing:
                    original=action['answer']
                    action=dict(action,answer=original+' '+' '.join(f'[{cid}]' for cid in missing))
                    self.formatting_events.append({'kind':'render_declared_citations','ids':missing,'raw_answer':original,'rendered_answer':action['answer']})
        return action
