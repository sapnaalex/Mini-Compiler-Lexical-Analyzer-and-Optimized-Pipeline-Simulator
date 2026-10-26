"""Polished Streamlit interface for the FLAT, DAA, and COA modules.

Run with: streamlit run app.py
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from main import Instruction, Symbol, SymbolTable, scan, simulate_pipeline

st.set_page_config(
    page_title="Mini-Compiler & Pipeline Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Lightweight visual system: navy typography, blue actions, bright cards.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    :root { --navy:#10233f; --blue:#2563eb; }
    html, body, [class*="st-"] { font-family:Inter,'Segoe UI',sans-serif; }
    .stApp { background:linear-gradient(180deg,#f4f7fc 0%,#fff 90%); }
    .block-container { max-width:1380px; padding-top:4.5rem; padding-bottom:3rem; }
    h1,h2,h3 { color:var(--navy); letter-spacing:-.035em; }
    h1 { font-weight:800; line-height:1.12; }
    .kicker,.module-label { color:var(--blue); font-weight:700; text-transform:uppercase; }
    .kicker { font-size:.78rem; letter-spacing:.14em; margin-bottom: 0.5rem; display: block; }
    .module-label { font-size:.75rem; letter-spacing:.12em; }
    .hero-copy { color:#52647d; font-size:1.03rem; line-height:1.6; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:#fff; border:1px solid #dce5f0; border-radius:18px; box-shadow:0 10px 28px rgba(16,35,63,.055); }
    div.stButton>button { border:1px solid #1d4ed8; border-radius:10px; background:linear-gradient(135deg,#2563eb,#1d4ed8); color:white; font-weight:650; transition:transform .15s,box-shadow .15s; }
    div.stButton>button:hover { border-color:#1e40af; background:#1e40af; color:white; transform:translateY(-1px); box-shadow:0 7px 16px #2563eb38; }
    div[data-testid="stMetric"] { background:#f5f8ff; border:1px solid #e1e9f6; border-radius:12px; padding:.8rem 1rem; }
    div[data-testid="stDataFrame"] { border:1px solid #e1e9f6; border-radius:10px; overflow:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="kicker">Course Systems Lab · FLAT · DAA · COA</div>', unsafe_allow_html=True)
st.title("Mini-Compiler Lexical Analyzer and Optimized Pipeline Simulator")
st.markdown(
    '<p class="hero-copy">An integrated system combining a DFA Lexical Analyzer, Binary Search Symbol Table, and 4-Stage CPU Pipeline Hazard Simulator.</p>',
    unsafe_allow_html=True,
)
st.divider()

table = SymbolTable([
    Symbol("count", 0), Symbol("limit", 4), Symbol("result", 12),
    Symbol("total", 8), Symbol("value", 16),
])
left, right = st.columns(2, gap="large")

with left:
    with st.container(border=True):
        st.markdown('<div class="module-label">Module 1 · FLAT</div>', unsafe_allow_html=True)
        st.subheader("DFA Lexical Analyzer")
        st.info("Scan source into keywords, identifiers, numbers, operators, and delimiters. Each token includes its line and column.")
        code = st.text_area(
            "Source code",
            value="int total = 12;\nif (total >= 10) total = total + 1;",
            height=150,
            help="The DFA recognizes identifiers and numeric literals, and uses maximal munch for two-character operators.",
        )
        if st.button("Run lexical scan", type="primary", key="scan", help="Tokenize the source with the DFA scanner."):
            try:
                tokens = scan(code)
                if tokens:
                    st.success(f"Recognized {len(tokens)} tokens.")
                    st.dataframe(pd.DataFrame([
                        {"Token type": t.kind, "Lexeme": t.lexeme, "Line": t.line, "Column": t.column}
                        for t in tokens
                    ]), hide_index=True, use_container_width=True)
                else:
                    st.info("The input contains no tokens.")
            except (TypeError, ValueError) as error:
                st.error(str(error))

with right:
    with st.container(border=True):
        st.markdown('<div class="module-label">Module 2 · DAA</div>', unsafe_allow_html=True)
        st.subheader("Binary Search Symbol Table")
        st.info("Names are sorted; each lookup takes O(log n) comparisons. The table maps symbols to memory slots.")
        st.dataframe(pd.DataFrame([
            {"Symbol": item.name, "Memory slot": item.slot} for item in table
        ]), hide_index=True, use_container_width=True)
        query_text = st.text_input(
            "Symbol queries",
            value="limit, total, missing",
            help="Enter comma-separated names. Spaces around each name are ignored.",
        )
        if st.button("Search symbols", type="primary", key="lookup", help="Look up each name using binary search."):
            names = [value.strip() for value in query_text.split(",") if value.strip()]
            if names:
                rows = []
                for name in names:
                    match = table.lookup(name)
                    rows.append({"Query": name, "Found": match is not None,
                                 "Memory slot": match.slot if match else "—"})
                found = sum(row["Found"] for row in rows)
                st.success(f"Found {found} of {len(rows)} queried symbols.")
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            else:
                st.info("Enter at least one symbol name to search.")

with st.container(border=True):
    st.markdown('<div class="module-label">Module 3 · COA</div>', unsafe_allow_html=True)
    st.subheader("COA Pipeline & RAW Hazards Simulator")
    st.info("View instructions through IF → ID → EX → WB cycle by cycle. This no-forwarding model detects Read-After-Write hazards and inserts required stalls.")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.caption("Sample instruction stream: LOAD → ADD → SUB → STORE, with dependent register reads.")
    with c2:
        penalty = st.number_input(
            "Stall penalty multiplier", min_value=0, max_value=5, value=1, step=1,
            help="Scales wait cycles for RAW dependencies. Use 1 for the base no-forwarding model.",
        )
    if st.button("Run pipeline simulation", type="primary", key="pipeline", help="Generate the cycle schedule and runtime metrics."):
        program = [
            Instruction("LOAD R1, [A]", "R1"),
            Instruction("ADD R2, R1, R3", "R2", ("R1", "R3")),
            Instruction("SUB R4, R2, R5", "R4", ("R2", "R5")),
            Instruction("STORE [B], R4", None, ("R4",)),
        ]
        result = simulate_pipeline(program, stall_penalty=int(penalty))
        a, b, c = st.columns(3)
        a.metric("Total clock cycles", result.cycles)
        b.metric("Injected stall cycles", result.stalls)
        c.metric("Instructions", len(program))
        schedule = []
        for cycle, events in enumerate(result.stage_schedule, 1):
            row = {"Cycle": cycle, "IF": "—", "ID": "—", "EX": "—", "WB": "—"}
            for event in events:
                instruction_id, stage = event.split(":", maxsplit=1)
                row[stage] = instruction_id
            schedule.append(row)
        st.dataframe(pd.DataFrame(schedule), hide_index=True, use_container_width=True)
        st.caption("Cells show the instruction in each stage; empty stages are marked — and inserted stalls extend the schedule.")

