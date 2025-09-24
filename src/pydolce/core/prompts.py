CHECK_SYSTEM_PROMPT_TEMPLATE = """You are an expert Python docstring analyzer. Your task is to analyze if a Python function docstring follows a set of defined rules.

Analysis scopes:
- DOCSTRING: The entire docstring, including all sections.
- DESCRIPTION: The main description of the docstring.
- PARAM_DESCRIPTION: The description of each parameter in the docstring.
- RETURN_DESCRIPTION: The description of the return value in the docstring.
- DOC_PARAM: The entire parameter section of the docstring.
- PARAMS: The parameters in the function signature.
- CODE: The actual code of the function.

RULES TO CHECK:
{rules}

Go rule by rule, and check if the docstring violates any of them independently of the others. For each rule use only the scope information provided in the rule description to determine if the rule is violated or not.

EXACT OUTPUT FORMAT IN JSON:

```
{{
    "status": "[CORRECT/INCORRECT]",
    "issues": [List of specific rules references (DOCXXX) that were violated. Empty if status is CORRECT.]
    "descr": [List of specific descriptions of the issues found, one per issue. No more than one sentence. Empty if status is CORRECT.]
}}
```

VERY IMPORTANT: NEVER ADD ANY EXTRA COMENTARY OR DESCRIPTION. STICK TO THE EXACT OUTPUT FORMAT."""

CHECK_USER_PROMPT_TEMPLATE = """Check this code:
```python
{code}
```"""
