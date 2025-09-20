from docstring_parser import DocstringStyle


def extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start : i + 1]

    return None


def doc_style_from_str(style_name: str) -> DocstringStyle | None:
    style_name = style_name.lower()
    if style_name in ["google", "google style"]:
        return DocstringStyle.GOOGLE
    elif style_name in ["numpy", "numpy style"]:
        return DocstringStyle.NUMPYDOC
    elif style_name in ["sphinx", "restructuredtext", "rest"]:
        return DocstringStyle.REST
    elif style_name in ["epy"]:
        return DocstringStyle.EPYDOC
    return None
