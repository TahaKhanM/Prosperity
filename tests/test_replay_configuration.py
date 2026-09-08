import ast
from pathlib import Path
import unittest
from scripts.replay_round4 import configure_trader, SOURCE


class ReplayConfigurationTests(unittest.TestCase):
    def test_changes_only_the_expiry_assignment(self):
        original=SOURCE.read_text()
        configured=configure_trader(original,6.0)
        original_tree=ast.parse(original)
        configured_tree=ast.parse(configured)
        for node in original_tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='START_TTE_DAYS' for t in node.targets):
                node.value=ast.Constant(6.0)
        self.assertEqual(ast.dump(original_tree),ast.dump(configured_tree))

    def test_missing_assignment_and_invalid_expiry_fail(self):
        with self.assertRaises(ValueError):configure_trader('class Trader: pass',6)
        for days in [0,-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError):configure_trader('START_TTE_DAYS = 7.0',days)


if __name__=='__main__':unittest.main()
