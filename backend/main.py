from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from parser_engine import CFGParserEngine, ParseNode

app = FastAPI(title="CFG Ambiguity Checker API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GrammarRule(BaseModel):
    lhs: str = Field(..., example="S")
    rhs: str = Field(..., example="S + S | a | b")

class AmbiguityRequest(BaseModel):
    start_symbol: str = Field(default="S", example="S")
    rules: List[GrammarRule]
    target_string: str = Field(..., example="a+a")

class AmbiguityResponse(BaseModel):
    is_in_language: bool
    is_ambiguous: bool
    trees_found: int
    status_badge: str
    explanation: str
    tokens: List[str]
    target_string: str
    parse_tree_1: Optional[Dict[str, Any]] = None
    parse_tree_2: Optional[Dict[str, Any]] = None
    trees: List[Dict[str, Any]] = []
    tree_count: int = 0
    derivation_steps_1: List[str] = []
    derivation_steps_2: List[str] = []
    earley_chart: List[Dict[str, Any]] = []
    execution_steps: List[Dict[str, Any]] = []

class GrammarValidationRequest(BaseModel):
    start_symbol: str = Field(default="S", example="S")
    rules: List[GrammarRule]
    target_string: Optional[str] = Field(default="", example="a+a")

class GrammarValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    non_terminals: List[str] = []
    terminals: List[str] = []

def parse_input_rules(raw_rules: List[GrammarRule]) -> Tuple[Dict[str, List[List[str]]], List[str]]:
    parsed: Dict[str, List[List[str]]] = {}
    known_lhs = {r.lhs.strip() for r in raw_rules if r.lhs.strip()}
    warnings: List[str] = []

    for r in raw_rules:
        lhs = r.lhs.strip()
        if not lhs:
            continue
        if lhs not in parsed:
            parsed[lhs] = []

        # Split alternations on '|'
        for alt in r.rhs.split("|"):
            tokens = CFGParserEngine.tokenize_rhs(alt, non_terminals=known_lhs)
            parsed[lhs].append(tokens)

    return parsed, warnings

@app.post("/api/validate-grammar", response_model=GrammarValidationResponse)
async def validate_grammar(payload: GrammarValidationRequest):
    errors = []
    warnings = []

    start_sym = payload.start_symbol.strip()
    if not start_sym:
        errors.append("Start symbol is required.")

    if not payload.rules:
        errors.append("At least one grammar production rule is required.")
        return GrammarValidationResponse(is_valid=False, errors=errors)

    rules_dict, _ = parse_input_rules(payload.rules)
    non_terminals = list(rules_dict.keys())

    if start_sym and start_sym not in rules_dict:
        errors.append(f"Start symbol '{start_sym}' is not defined as LHS in any production rule.")

    # Check for undefined uppercase non-terminals referenced in RHS
    engine = CFGParserEngine(start_symbol=start_sym or "S", rules=rules_dict)
    for lhs, prods in rules_dict.items():
        for prod in prods:
            for sym in prod:
                # If symbol starts with uppercase and not in non_terminals
                if sym and sym[0].isupper() and sym not in rules_dict and sym not in ["ε", "EPS", "EPSILON"]:
                    warnings.append(f"Non-terminal '{sym}' in rule '{lhs}' has no production rules defined.")

    # Target string terminal checks
    if payload.target_string:
        extracted = engine.extract_tokens(payload.target_string)
        for t in extracted:
            if t not in engine.terminals and t not in ["ε", "eps", "epsilon"]:
                warnings.append(f"Target string token '{t}' does not match any terminal defined in grammar.")

    is_valid = len(errors) == 0
    return GrammarValidationResponse(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        non_terminals=non_terminals,
        terminals=list(engine.terminals)
    )

@app.post("/api/check-ambiguity", response_model=AmbiguityResponse)
async def check_ambiguity(payload: AmbiguityRequest):
    if not payload.rules:
        raise HTTPException(status_code=400, detail="At least one grammar rule is required.")

    rules_dict, _ = parse_input_rules(payload.rules)
    start_sym = payload.start_symbol.strip()
    if start_sym not in rules_dict:
        raise HTTPException(status_code=400, detail=f"Start symbol '{start_sym}' is not defined in grammar rules.")

    engine = CFGParserEngine(start_symbol=start_sym, rules=rules_dict)
    tokens = engine.extract_tokens(payload.target_string)

    # 1. Generalized Earley Chart Parsing in O(n^3) time
    chart, execution_steps, is_recognized, internal_data = engine.generate_earley_chart(tokens)

    # 2. Reconstruct Parse Trees from Completed Earley Chart Backpointers / SPPF
    parse_trees: List[ParseNode] = []
    if is_recognized:
        parse_trees = engine.find_all_parse_trees(tokens, internal_data)

    tree_count = len(parse_trees)
    is_ambiguous = tree_count >= 2
    is_in_language = is_recognized and tree_count > 0

    # 3. Derive leftmost derivation sequences
    derivations_1 = engine.get_leftmost_derivation_steps(parse_trees[0]) if len(parse_trees) > 0 else []
    derivations_2 = engine.get_leftmost_derivation_steps(parse_trees[1]) if len(parse_trees) > 1 else []

    # 4. Determine status badge and explanation
    if is_ambiguous:
        status_badge = "AMBIGUOUS CFG"
        explanation = (
            f"The grammar is AMBIGUOUS for target string '{payload.target_string}'. "
            f"Found {tree_count} mathematically distinct parse trees generating the exact same token yield. "
            f"In Theory of Computation (TOC), a CFG is ambiguous if there exists at least one string "
            f"in L(G) that admits two or more distinct leftmost derivations or parse trees."
        )
    elif is_in_language:
        status_badge = "UNAMBIGUOUS / SINGLE TREE"
        explanation = (
            f"Strictly UNAMBIGUOUS for target string '{payload.target_string}'. "
            f"The string belongs to L(G) and yields exactly 1 unique parse tree under the grammar. "
            f"No alternative derivation path exists for this specific string."
        )
    else:
        status_badge = "NOT IN LANGUAGE"
        explanation = (
            f"Target string '{payload.target_string}' is NOT IN LANGUAGE L(G). "
            f"The Earley parser could not complete the start symbol rule over the token sequence {tokens}."
        )

    tree_1_dict = parse_trees[0].to_dict() if len(parse_trees) > 0 else None
    tree_2_dict = parse_trees[1].to_dict() if len(parse_trees) > 1 else None
    trees_list = [t.to_dict() for t in parse_trees[:2]]

    return AmbiguityResponse(
        is_in_language=is_in_language,
        is_ambiguous=is_ambiguous,
        trees_found=tree_count,
        tree_count=tree_count,
        status_badge=status_badge,
        explanation=explanation,
        tokens=tokens,
        target_string=payload.target_string,
        parse_tree_1=tree_1_dict,
        parse_tree_2=tree_2_dict,
        trees=trees_list,
        derivation_steps_1=derivations_1,
        derivation_steps_2=derivations_2,
        earley_chart=chart,
        execution_steps=execution_steps
    )

@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "CFG Ambiguity Checker Engine v2.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
