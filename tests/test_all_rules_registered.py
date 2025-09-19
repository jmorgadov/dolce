from pathlib import Path

import pydolce.core.rules.checkers


def test_al_rules_registered() -> None:
    registered_rules = set(pydolce.core.rules.rules.Rule.all_rules.keys())

    checkers_path = Path(pydolce.core.rules.checkers.__path__[0])

    # Get all rule codes from the checkers modules
    expected_rules = set()
    for checker_file in checkers_path.glob("*.py"):
        if checker_file.name == "__init__.py":
            continue
        module = checker_file.stem
        # count all functions in module that has Rule.register or Rule.llm_register decorator
        checker_module = __import__(
            f"pydolce.core.rules.checkers.{module}", fromlist=[""]
        )
        for attr_name in dir(checker_module):
            attr = getattr(checker_module, attr_name)
            if callable(attr) and hasattr(attr, "rule_ref"):
                expected_rules.add(attr.rule_ref)

    assert len(expected_rules) > 0, "No rules found in checkers."

    outside_checkers = registered_rules - expected_rules
    assert len(outside_checkers) == 0, (
        f"Rules {outside_checkers} seem to be registered outside checkers submodule."
    )

    not_registered = expected_rules - set(registered_rules)
    assert len(not_registered) == 0, f"Rules {not_registered} are not registered."
