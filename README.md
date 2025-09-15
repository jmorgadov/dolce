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

Simple example:

```bash
dolce check tests/samples/sample1.py
```

on file:

```python
# tests/samples/sample1.py
def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number."""
    return n if n <= 1 else fibonacci(n - 1) + fibonacci(n - 2)

def add(a: int, b: int) -> int:
    """Multiply two integers."""
    return a + b

def subtract(a: int, b: int) -> int:
    return a - b
```

outputs:

```text
Dolce - 0.1.1

tests/samples/sample1.py:1:fibonacci ✓ Correct
tests/samples/sample1.py:6:add ✗ Incorrect
  - The function is documented as multiplying two numbers, but it actually adds them.
tests/samples/sample1.py:11:subtract Missing docstring.

Summary:
✓ Correct: 1
⚠ Missing: 1
✗ Incorrect: 1
```

## Configure

By default **dolce** will try to run locally `codestral` model via `ollama` provider. You can visit the [Ollama](https://ollama.com/) site for installation instructions.

> :warning: Codestral is a 22b parameter model, you can experiment with smaller models but take into account that the results may vary.

If you want to use a different model or provider you can configure the default options in the `pyproject.toml` of your project:

```toml
[tool.dolce]
url = "http://localhost:11434"
model = "codestral"
provider = "ollama"
api_key = "YOUR_API_KEY_ENVIROMENT_VAR"
```

## To be implemented

- Add cache system to avoid re-checking unchanged code
- Integrate third-party tools to check docstrings style, parameters, etc.
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