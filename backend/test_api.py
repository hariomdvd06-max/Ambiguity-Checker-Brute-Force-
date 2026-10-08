import asyncio
from main import check_ambiguity, validate_grammar, AmbiguityRequest, GrammarRule, GrammarValidationRequest

async def main():
    print("Testing Case 1: Arithmetic E -> E + E | E * E | a with 'a + a * a + a'...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="E",
        rules=[GrammarRule(lhs="E", rhs="E + E | E * E | a")],
        target_string="a + a * a + a"
    ))
    print("  is_in_language:", resp.is_in_language)
    print("  is_ambiguous:", resp.is_ambiguous)
    print("  trees_found:", resp.trees_found)
    print("  status_badge:", resp.status_badge)
    print("  tokens:", resp.tokens)
    print("  has parse_tree_1:", resp.parse_tree_1 is not None)
    print("  has parse_tree_2:", resp.parse_tree_2 is not None)
    print("  derivations_1 count:", len(resp.derivation_steps_1))
    print("  derivations_2 count:", len(resp.derivation_steps_2))
    assert resp.is_ambiguous is True
    assert resp.trees_found == 2
    assert resp.status_badge == "AMBIGUOUS CFG"

    print("\nTesting Case 2: Dangling Else S -> if c then S else S | if c then S | a with 'if c then if c then a else a'...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="S",
        rules=[GrammarRule(lhs="S", rhs="if c then S else S | if c then S | a")],
        target_string="if c then if c then a else a"
    ))
    print("  is_in_language:", resp.is_in_language)
    print("  is_ambiguous:", resp.is_ambiguous)
    print("  trees_found:", resp.trees_found)
    print("  status_badge:", resp.status_badge)
    assert resp.is_ambiguous is True
    assert resp.trees_found == 2
    assert resp.status_badge == "AMBIGUOUS CFG"

    print("\nTesting Case 3: Unambiguous S -> ( S ) | a with '( ( a ) )'...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="S",
        rules=[GrammarRule(lhs="S", rhs="( S ) | a")],
        target_string="( ( a ) )"
    ))
    print("  is_in_language:", resp.is_in_language)
    print("  is_ambiguous:", resp.is_ambiguous)
    print("  trees_found:", resp.trees_found)
    print("  status_badge:", resp.status_badge)
    print("  has parse_tree_1:", resp.parse_tree_1 is not None)
    print("  has parse_tree_2:", resp.parse_tree_2 is None)
    assert resp.is_in_language is True
    assert resp.is_ambiguous is False
    assert resp.trees_found == 1
    assert resp.status_badge == "UNAMBIGUOUS / SINGLE TREE"

    print("\nTesting Case 4: Palindrome S -> a S a | b S b | ε with 'a b a' (Not in language)...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="S",
        rules=[GrammarRule(lhs="S", rhs="a S a | b S b | ε")],
        target_string="a b a"
    ))
    print("  is_in_language:", resp.is_in_language)
    print("  is_ambiguous:", resp.is_ambiguous)
    print("  trees_found:", resp.trees_found)
    print("  status_badge:", resp.status_badge)
    assert resp.is_in_language is False
    assert resp.is_ambiguous is False
    assert resp.trees_found == 0
    assert resp.status_badge == "NOT IN LANGUAGE"

    print("\nTesting Case 5: Odd Palindrome S -> a S a | b S b | a | b | ε with 'a b a'...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="S",
        rules=[GrammarRule(lhs="S", rhs="a S a | b S b | a | b | ε")],
        target_string="a b a"
    ))
    print("  is_in_language:", resp.is_in_language)
    print("  trees_found:", resp.trees_found)
    print("  status_badge:", resp.status_badge)
    assert resp.is_in_language is True

    print("\nTesting Case 6: Compact input 'a+a*a+a'...")
    resp = await check_ambiguity(AmbiguityRequest(
        start_symbol="E",
        rules=[GrammarRule(lhs="E", rhs="E + E | E * E | a")],
        target_string="a+a*a+a"
    ))
    assert resp.is_ambiguous is True
    print("  Tokens:", resp.tokens)

    print("\nTesting Validation Endpoint...")
    v_resp = await validate_grammar(GrammarValidationRequest(
        start_symbol="S",
        rules=[
            GrammarRule(lhs="S", rhs="A + B"),
            GrammarRule(lhs="A", rhs="a")
        ],
        target_string="a + b"
    ))
    print("  Warnings:", v_resp.warnings)
    assert any("B" in w for w in v_resp.warnings)

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(main())
