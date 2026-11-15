"""Test-stage guards without network/model calls."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_agent_test import validate_frozen


class FrozenTests(unittest.TestCase):
    def test_changes_to_runtime_or_labels_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ['src/runtime.py','benchmark/questions.json','data/chunks.json']:
                p=root/name;p.parent.mkdir(exist_ok=True,parents=True);p.write_text('original')
            digest=hashlib.sha256(b'original').hexdigest()
            selection={'status':'dev_selected_and_student_approved','runtime_code_sha256':{'src/runtime.py':digest},'benchmark_sha256':digest,'chunks_sha256':digest}
            with patch('scripts.run_agent_test.ROOT',root):
                validate_frozen(selection)
                (root/'src/runtime.py').write_text('changed')
                with self.assertRaises(ValueError):validate_frozen(selection)
                (root/'src/runtime.py').write_text('original')
                (root/'benchmark/questions.json').write_text('changed')
                with self.assertRaises(ValueError):validate_frozen(selection)

    def test_unapproved_selection_is_rejected(self):
        with self.assertRaises(ValueError):validate_frozen({'status':'pending'})


if __name__=='__main__':unittest.main()
