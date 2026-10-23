"""Verification suite for the FLAT, DAA, and COA course modules.

Run with ``python -m unittest -v``. Uses only Python's standard library.
"""

import unittest

from main import Instruction, Symbol, SymbolTable, scan, simulate_pipeline


class ScannerTests(unittest.TestCase):
    def test_token_kinds_and_positions(self):
        tokens = scan("int value = 42;\nvalue >= 3.5")
        self.assertEqual(
            [(t.kind, t.lexeme) for t in tokens],
            [("KEYWORD", "int"), ("IDENTIFIER", "value"), ("OPERATOR", "="),
             ("INTEGER", "42"), ("DELIMITER", ";"), ("IDENTIFIER", "value"),
             ("OPERATOR", ">="), ("FLOAT", "3.5")],
        )
        self.assertEqual((tokens[-1].line, tokens[-1].column), (2, 10))

    def test_invalid_character_and_number(self):
        with self.assertRaises(ValueError):
            scan("x @ 2")
        with self.assertRaises(ValueError):
            scan("12.")
        self.assertEqual(scan("@", strict=False)[0].kind, "ERROR")


class SymbolTableTests(unittest.TestCase):
    def test_binary_search_lookup_and_order(self):
        table = SymbolTable([Symbol("zeta", 9), Symbol("alpha", 1), Symbol("mu", 4)])
        self.assertEqual([s.name for s in table], ["alpha", "mu", "zeta"])
        self.assertEqual(table.lookup("mu"), Symbol("mu", 4))
        self.assertEqual(table.memory_slot("unknown"), None)

    def test_duplicate_rejected(self):
        table = SymbolTable([Symbol("x", 0)])
        with self.assertRaises(ValueError):
            table.insert("x", 1)


class PipelineTests(unittest.TestCase):
    def test_raw_dependency_injects_stall(self):
        program = [Instruction("LOAD R1", "R1"), Instruction("ADD R2, R1", "R2", ("R1",))]
        result = simulate_pipeline(program)
        self.assertEqual(result.stalls, 1)
        self.assertEqual(result.cycles, 6)

    def test_independent_instructions_overlap(self):
        program = [Instruction("A", "R1"), Instruction("B", "R2")]
        result = simulate_pipeline(program)
        self.assertEqual(result.stalls, 0)
        self.assertEqual(result.cycles, 5)

    def test_empty_program(self):
        self.assertEqual(simulate_pipeline([]).cycles, 0)


if __name__ == "__main__":
    unittest.main()
