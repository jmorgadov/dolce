# Dolce

*Because broken docs leave a bitter taste.*

**Dolce** is a tool designed to help you maintain high-quality docstrings in your Python code. It leverages Large Language Models (LLMs) to ensure that your docstrings are consistent with your code.

## Installation

```bash
pip install pydolce
```

## Usage

```bash
dolce check # Check docstrings in all python files in the current directory and subdirectories
dolce check src # Check in specific directory
dolce check src/myproject/main.py # Check in specific file
```

### Example

```bash
dolce check tests/samples
```

outputs:

```text
[ ERROR ] tests/samples/wrong_descr.py:1 add
  ![#f03c15]- DOC300: Docstring states the function does something that the code does not do. (The docstring claims the function multiplies integers, but the code performs addition.)[/#f03c15]
[ ERROR ] tests/samples/behavior.py:4 post_multiplication
  - DOC300: Docstring states the function does something that the code does not do. (The docstring summary 'Add two integers' does not match the code which performs multiplication and an HTTP POST request.)
  - DOC301: Docstring omits a critical behavior that the code performs. (The code performs a critical behavior (HTTP POST request) but the docstring does not mention this behavior.)
[ ERROR ] tests/samples/typos.py:1 add
  - DOC200: Docstring description contains spelling errors. (The docstring DESCRIPTION contains typo: 'intgers' instead of 'integers'.)
  - DOC201: Docstring parameter description contains spelling errors. (The parameter 'a' description contains typo: 'Te' instead of 'The'.)
[ ERROR ] tests/samples/simple.py:1 fibonacci
  - SIG203: parameters missing
  - SIG503: return missing from docstring
[  OK   ] tests/samples/simple.py:6 subtract

Summary:
✓ Correct: 1
✗ Incorrect: 4
```

## Configure

Right now **dolce** can be configured via `pyproject.toml` file. You can specify which rules to check and which to ignore. By default it will check all rules.

```toml
[tool.dolce]
target = [
  # Set of rules to check
  "DOC300",
]
disable = [
  # Set of rules to ignore
  "SIG201",
]
```

### Rules checked with LLM

Some rules require an LLM to check docstrings (e.g., docstring spelling, docstring description vs code behavior, etc.). By default **dolce** will try to run locally `qwen3:8b` model via `ollama` provider. You can visit the [Ollama](https://ollama.com/) site for installation instructions.

`qwen3:8b` has relatively good performance while fitting in an RTX 4060 GPU (8GB VRAM). However, if you want to use a different model or provider you can configure the default options in the `pyproject.toml` of your project like this:

```toml
[tool.dolce]
url = "http://localhost:11434"
model = "codestral"
provider = "ollama"
api_key = "YOUR_API_KEY_ENVIROMENT_VAR"
```

### Signature check

Signature check is done vía [docsig](https://docsig.readthedocs.io/en/latest/index.html). If you add a `[tool.docsig]` config section in your `pyproject.toml` file, **dolce** will load it to configure the signature check.

```toml
# Example from docsign documentation 
# https://docsig.readthedocs.io/en/latest/usage/configuration.html
[tool.docsig]
check-dunders = false
check-overridden = false
check-protected = false
disable = [
    "SIG101",
    "SIG102",
    "SIG402",
]
target = [
    "SIG202",
    "SIG203",
    "SIG201",
]
```

## To be implemented

- Add cache system to avoid re-checking unchanged code
- Support for ignoring specific code segments, files, directories, etc
- Support parallel requests
... much more!

---

## 📦 For Developers

Make sure you have the following tools installed before working with the project:

- [**uv**](https://docs.astral.sh/uv/) → Python project and environment management
- [**make**](https://www.gnu.org/software/make/) → run common project tasks via the `Makefile`

### Getting Started

Install dependencies into a local virtual environment:

```bash
uv sync --all-groups
```

This will create a `.venv` folder and install everything declared in `pyproject.toml`.

Then, you can activate the environment manually depending on your shell/OS:

- **Linux / macOS (bash/zsh):**

  ```bash
  source .venv/bin/activate
  ```

- **Windows (PowerShell):**

  ```powershell
  .venv\Scripts\Activate.ps1
  ```

- **Windows (cmd.exe):**

  ```cmd
  .venv\Scripts\activate.bat
  ```

### Running

```bash
uv run dolce check path/to/your/code
```

### Linting, Formatting, and Type Checking

```bash
make qa
```

Runs **Ruff** for linting and formatting, and **Mypy** for type checking.

### Running Unit Tests

Before running tests, override any required environment variables in the `.env.test` file.

```bash
make test
```

Executes the test suite using **Pytest**.

### Building the Project

```bash
make build
```

Generates a distribution package inside the `dist/` directory.

### Cleaning Up

```bash
make clean
```

Removes build artifacts, caches, and temporary files to keep your project directory clean.

### Building docs

```bash
make docs
```

Generates the project documentation inside the `dist/docs` folder.

When building the project (`make build`) the docs will also be generated automatically and
included in the distribution package.

## 🤝 Contributing

Contributions are welcome!
Please ensure all QA checks and tests pass before opening a pull request.

---

<sub>🚀 Project starter provided by [Cookie Pyrate](https://github.com/gvieralopez/cookie-pyrate)</sub>