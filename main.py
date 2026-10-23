"""Integrated FLAT, DAA, and COA course demonstration.

Run ``python main.py`` for a deterministic demonstration of all three modules.
The implementation uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Module 1 — FLAT: DFA-based lexical analyzer
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Token:
    """A token recognized by the scanner, with its 1-based source location."""

    kind: str
    lexeme: str
    line: int
    column: int


KEYWORDS = frozenset({"if", "else", "while", "for", "int", "float", "return", "print", "var"})
OPERATORS = ("==", "!=", "<=", ">=", "&&", "||", "=", "+", "-", "*", "/", "%", "<", ">", "!", "&", "|")
SINGLE_OPERATORS = frozenset(op for op in OPERATORS if len(op) == 1)
DOUBLE_OPERATORS = frozenset(op for op in OPERATORS if len(op) == 2)
DELIMITERS = frozenset("(){}[],;:")


def _letter(ch: str) -> bool:
    return ch == "_" or ch.isalpha()


def _digit(ch: str) -> bool:
    return ch.isascii() and ch.isdigit()


def scan(source: str, *, strict: bool = True) -> list[Token]:
    """Tokenize source using explicit DFA states for identifiers and numbers.

    Identifier DFA: START --letter/_--> IDENTIFIER --letter/digit/_--> IDENTIFIER.
    Number DFA: START --digit--> INTEGER --digit--> INTEGER; a decimal point
    transitions to FRACTION, which accepts one or more digits. Operators use
    maximal munch (two-character operators are checked before one-character
    operators). Illegal input raises ValueError by default; with strict=False,
    it is returned as an ERROR token so callers can build diagnostic tooling.
    """
    if not isinstance(source, str):
        raise TypeError("source must be a string")
    tokens: list[Token] = []
    i = 0
    line = column = 1

    def advance(text: str) -> None:
        nonlocal line, column
        newlines = text.count("\n")
        if newlines:
            line += newlines
            column = len(text) - text.rfind("\n")
        else:
            column += len(text)

    def emit(kind: str, start: int, end: int, token_line: int, token_column: int) -> None:
        tokens.append(Token(kind, source[start:end], token_line, token_column))

    while i < len(source):
        ch = source[i]
        if ch.isspace():
            advance(ch)
            i += 1
            continue
        start, token_line, token_column = i, line, column

        # DFA walk: START -> IDENTIFIER; final state is reclassified as keyword.
        if _letter(ch):
            i += 1
            while i < len(source) and (_letter(source[i]) or _digit(source[i])):
                i += 1
            text = source[start:i]
            emit("KEYWORD" if text in KEYWORDS else "IDENTIFIER", start, i, token_line, token_column)
            advance(text)
            continue

        # DFA walk: START -> INTEGER -> FRACTION. A trailing dot is invalid.
        if _digit(ch):
            i += 1
            while i < len(source) and _digit(source[i]):
                i += 1
            kind = "INTEGER"
            if i < len(source) and source[i] == ".":
                if i + 1 >= len(source) or not _digit(source[i + 1]):
                    bad = source[start:i + 1]
                    if strict:
                        raise ValueError(f"Malformed number {bad!r} at {token_line}:{token_column}")
                    i += 1
                    emit("ERROR", start, i, token_line, token_column)
                    advance(source[start:i])
                    continue
                kind = "FLOAT"
                i += 1
                while i < len(source) and _digit(source[i]):
                    i += 1
            emit(kind, start, i, token_line, token_column)
            advance(source[start:i])
            continue

        pair = source[i:i + 2]
        if pair in DOUBLE_OPERATORS:
            i += 2
            emit("OPERATOR", start, i, token_line, token_column)
            advance(pair)
            continue
        if ch in SINGLE_OPERATORS:
            i += 1
            emit("OPERATOR", start, i, token_line, token_column)
            advance(ch)
            continue
        if ch in DELIMITERS:
            i += 1
            emit("DELIMITER", start, i, token_line, token_column)
            advance(ch)
            continue

        if strict:
            raise ValueError(f"Unexpected character {ch!r} at {line}:{column}")
        i += 1
        emit("ERROR", start, i, token_line, token_column)
        advance(ch)
    return tokens


# ---------------------------------------------------------------------------
# Module 2 — DAA: sorted symbol table and binary search
# ---------------------------------------------------------------------------
@dataclass(frozen=True, order=True)
class Symbol:
    """A named variable and its assigned memory slot."""

    name: str
    slot: int


class SymbolTable:
    """Sorted symbol table; lookup is O(log n), insertion O(n) due to shifting."""

    def __init__(self, symbols: Iterable[Symbol] = ()) -> None:
        self._symbols: list[Symbol] = []
        for symbol in symbols:
            self.insert(symbol.name, symbol.slot)

    def insert(self, name: str, slot: int) -> None:
        if not name or not isinstance(name, str):
            raise ValueError("symbol name must be a non-empty string")
        if not isinstance(slot, int) or isinstance(slot, bool) or slot < 0:
            raise ValueError("slot must be a non-negative integer")
        # Find insertion point with binary search; preserve sorted unique names.
        lo, hi = 0, len(self._symbols)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._symbols[mid].name < name:
                lo = mid + 1
            else:
                hi = mid
        if lo < len(self._symbols) and self._symbols[lo].name == name:
            raise ValueError(f"duplicate symbol: {name}")
        self._symbols.insert(lo, Symbol(name, slot))

    def lookup(self, name: str) -> Symbol | None:
        """Return a symbol using classic low/high/mid binary search in O(log n)."""
        lo, hi = 0, len(self._symbols) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            current = self._symbols[mid]
            if current.name == name:
                return current
            if current.name < name:
                lo = mid + 1
            else:
                hi = mid - 1
        return None

    def memory_slot(self, name: str) -> int | None:
        result = self.lookup(name)
        return result.slot if result else None

    def __iter__(self):
        return iter(self._symbols)

    def __len__(self) -> int:
        return len(self._symbols)


# ---------------------------------------------------------------------------
# Module 3 — COA: four-stage pipeline and RAW hazard stalls
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Instruction:
    """An instruction with one optional destination and zero or more sources."""

    text: str
    destination: str | None
    sources: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("instruction text cannot be empty")
        if self.destination == "":
            raise ValueError("destination must be None or a non-empty register name")


@dataclass(frozen=True)
class PipelineResult:
    cycles: int
    stalls: int
    stall_cycles: tuple[int, ...]
    stage_schedule: tuple[tuple[str, ...], ...]


def simulate_pipeline(instructions: Sequence[Instruction], *, stall_penalty: int = 1) -> PipelineResult:
    """Schedule IF/ID/EX/WB stages and inject stalls for each RAW dependency.

    This educational model assumes no forwarding: a consumer waits until the
    producer's WB cycle. A dependency on an instruction ``distance`` positions
    back costs max(0, 4 - distance) cycles. Multiple outstanding dependencies
    on one instruction are covered by the longest wait, not summed. Independent
    instructions overlap normally. Empty input takes zero cycles.
    """
    if not isinstance(stall_penalty, int) or isinstance(stall_penalty, bool) or stall_penalty < 0:
        raise ValueError("stall_penalty must be a non-negative integer")
    ready: dict[str, int] = {}
    fetch: list[int] = []
    per_instruction_stalls: list[int] = []
    # A stall delays the consumer's fetch so the producer's value is available
    # at ID. Base schedule starts consecutive instructions one cycle apart.
    for index, instruction in enumerate(instructions):
        start = (fetch[-1] + 1) if fetch else 1
        # ID is one cycle after IF. Delay until ID reaches the producer's WB.
        required_wait = max((max(0, ready.get(reg, -1) - (start + 1)) for reg in instruction.sources), default=0)
        stalls = required_wait * stall_penalty
        start += stalls
        fetch.append(start)
        per_instruction_stalls.append(stalls)
        if instruction.destination:
            # In the no-forwarding model, operand may be read on WB cycle.
            ready[instruction.destination] = start + 3
    if not instructions:
        return PipelineResult(0, 0, (), ())
    last_cycle = fetch[-1] + 3
    stages = ("IF", "ID", "EX", "WB")
    schedule: list[tuple[str, ...]] = []
    for cycle in range(1, last_cycle + 1):
        active = []
        for idx, start in enumerate(fetch):
            offset = cycle - start
            if 0 <= offset < len(stages):
                active.append(f"I{idx + 1}:{stages[offset]}")
        schedule.append(tuple(active))
    total_stalls = sum(per_instruction_stalls)
    return PipelineResult(last_cycle, total_stalls, tuple(per_instruction_stalls), tuple(schedule))


def _demo() -> None:
    print("=== Integrated Technical Micro-Project ===")
    print("\n[FLAT / Module 1] DFA lexical scan")
    sample = "int total = 12; if (total >= 10) total = total + 1;"
    for token in scan(sample):
        print(f"{token.line}:{token.column} {token.kind:<10} {token.lexeme}")

    print("\n[DAA / Module 2] Binary-search symbol table")
    table = SymbolTable([Symbol("count", 0), Symbol("limit", 4), Symbol("total", 8)])
    for name in ("limit", "missing"):
        result = table.lookup(name)
        print(f"{name}: {result if result else 'not found'}")

    print("\n[COA / Module 3] Four-stage pipeline (no forwarding)")
    program = [
        Instruction("LOAD R1, [A]", "R1"),
        Instruction("ADD R2, R1, R3", "R2", ("R1", "R3")),
        Instruction("SUB R4, R2, R5", "R4", ("R2", "R5")),
        Instruction("STORE [B], R4", None, ("R4",)),
    ]
    result = simulate_pipeline(program)
    for cycle, events in enumerate(result.stage_schedule, 1):
        print(f"cycle {cycle:>2}: {' | '.join(events) if events else 'STALL / idle'}")
    print(f"Total cycles: {result.cycles} (injected stall cycles: {result.stalls})")


if __name__ == "__main__":
    _demo()
