"""Streamlit interface for the integrated FLAT, DAA, and COA demonstration.

Launch with ``streamlit run app.py`` from the project directory.
"""

import streamlit as st

from main import Instruction, Symbol, SymbolTable, scan, simulate_pipeline


st.set_page_config(page_title="FLAT · DAA · COA Lab", page_icon="🧪", layout="wide")
st.title("Integrated Technical Micro-Project")
st.caption("Explore a DFA scanner, binary-search symbol table, and four-stage CPU pipeline.")

left, right = st.columns(2)
with left:
    st.subheader("Module 1 · DFA Lexical Analyzer")
    source_code = st.text_area(
        "Source code to scan",
        value="int total = 12;\nif (total >= 10) total = total + 1;",
        height=170,
        help="Enter code using identifiers, numbers, keywords, operators, and delimiters.",
    )
    if st.button("Tokenize source", type="primary", key="tokenize"):
        try:
            tokens = scan(source_code)
            if tokens:
                st.write("Recognized tokens (source order):")
                st.text("\n".join(f"{t.line}:{t.column}  {t.kind:<10} {t.lexeme}" for t in tokens))
            else:
                st.info("No tokens found. Enter some source code to scan.")
        except (TypeError, ValueError) as error:
            st.error(str(error))

with right:
    st.subheader("Module 2 · Binary Search Symbol Table")
    st.write("The sample table maps variable names to memory slots; lookup uses O(log n) binary search.")
    symbol_table = SymbolTable([
        Symbol("count", 0), Symbol("limit", 4), Symbol("result", 12),
        Symbol("total", 8), Symbol("value", 16),
    ])
    st.text("Sorted symbols: " + ", ".join(f"{item.name} → slot {item.slot}" for item in symbol_table))
    queries = st.text_input(
        "Symbol queries (comma-separated)",
        value="limit, total, missing",
        help="Enter one or more names. Whitespace around names is ignored.",
    )
    if st.button("Look up symbols", key="lookup"):
        names = [name.strip() for name in queries.split(",") if name.strip()]
        if not names:
            st.info("Enter at least one symbol name to search.")
        else:
            st.write("Binary-search results:")
            for name in names:
                found = symbol_table.lookup(name)
                st.write(f"{name}: memory slot {found.slot}" if found else f"{name}: not found")

st.divider()
st.subheader("Module 3 · COA Pipeline and RAW Hazards")
st.write("Four-stage IF → ID → EX → WB simulation. This example assumes no forwarding.")
stall_penalty = st.number_input("Stall penalty multiplier", min_value=0, max_value=5, value=1, step=1)
if st.button("Run pipeline simulation", key="pipeline"):
    program = [
        Instruction("LOAD R1, [A]", "R1"),
        Instruction("ADD R2, R1, R3", "R2", ("R1", "R3")),
        Instruction("SUB R4, R2, R5", "R4", ("R2", "R5")),
        Instruction("STORE [B], R4", None, ("R4",)),
    ]
    result = simulate_pipeline(program, stall_penalty=int(stall_penalty))
    st.write("Instruction sequence:")
    st.text("\n".join(f"I{index}: {instruction.text}" for index, instruction in enumerate(program, 1)))
    st.write("Cycle-by-cycle pipeline log:")
    st.text("\n".join(
        f"Cycle {cycle:>2}: {' | '.join(events) if events else 'STALL / idle'}"
        for cycle, events in enumerate(result.stage_schedule, 1)
    ))
    st.write(f"Total clock cycles: {result.cycles} · Injected stall cycles: {result.stalls}")
