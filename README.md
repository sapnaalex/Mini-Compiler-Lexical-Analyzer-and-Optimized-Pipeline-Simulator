# Integrated Technical Micro-Project

A runnable, standard-library-only Python project that connects three core computer science subjects through small, inspectable implementations.

* **GitHub Repository:** [sapnaalex/Mini-Compiler-Lexical-Analyzer-and-Optimized-Pipeline-Simulator](https://github.com/sapnaalex/Mini-Compiler-Lexical-Analyzer-and-Optimized-Pipeline-Simulator)
* **Live Deployed App:** [Streamlit Application Link](https://mini-compiler-lexical-analyzer-and-optimized-pipeline-simulator.streamlit.app/)

---

## Run it locally

```console
python main.py
```

`main.py` runs a deterministic terminal demonstration immediately: it prints lexical tokens, performs symbol lookups, and prints a cycle-by-cycle pipeline schedule. Python 3.10 or newer is recommended (the code uses modern type annotations). 

To launch the interactive browser interface locally:
```console
python -m pip install -r requirements.txt
streamlit run app.py
```

To verify the implementation via unit tests:
```console
python -m unittest -v
```

## Streamlit interface

`app.py` provides a source-code text area and tokenization button, a comma-separated symbol-query input and binary-search results, plus a pipeline simulation button with a configurable stall-penalty multiplier. Each action displays results in the browser while reusing the implementations from `main.py`.

## Course mapping

### Module 1 — Formal Language and Automata Theory (FLAT)
`scan()` implements a DFA-style scanner. Identifier transitions accept letters/underscore initially and letters/digits/underscore thereafter. Numeric transitions recognize integers and decimal fractions. The scanner classifies keywords, operators, delimiters, and identifiers, tracks line and column positions, uses maximal munch for two-character operators, and reports malformed/unknown input with a useful location. Pass `strict=False` to collect invalid characters as `ERROR` tokens.

### Module 2 — Design and Analysis of Algorithms (DAA)
`SymbolTable` keeps names in sorted order and uses the low/high/mid binary search pattern in `lookup()`, giving O(log n) lookup time. It returns the complete symbol, including its memory slot. Insertion locates the point in O(log n), while inserting into a Python list costs O(n) due to element shifting; duplicate names are rejected.

### Module 3 — Computer Organization and Architecture (COA)
`simulate_pipeline()` models IF, ID, EX, and WB stages with overlapping instructions. It recognizes Read-After-Write (RAW) dependencies from each instruction's source registers and inserts stalls in the no-forwarding model until the producing instruction reaches WB. The returned `PipelineResult` includes total cycles, injected stall cycles, per-instruction stalls, and a readable schedule. Independent instructions overlap. `stall_penalty` scales the wait cost and defaults to one cycle per required wait cycle.

## API sketch

```python
from main import Instruction, SymbolTable, scan, simulate_pipeline

tokens = scan("int x = 4;")
symbols = SymbolTable()
symbols.insert("x", 12)
slot = symbols.memory_slot("x")
result = simulate_pipeline([
    Instruction("LOAD R1", "R1"),
    Instruction("ADD R2, R1", "R2", ("R1",)),
])
```