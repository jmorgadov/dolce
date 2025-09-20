# Dolce

***Because broken docs leave a bitter taste.***

<a ref="https://pypi.org/project/pydolce/"><img src="https://img.shields.io/pypi/v/pydolce?color=blue&label=PyPI&logo=python&style=flat-square" alt="PyPI version"></a>


**Dolce** is a tool designed to help you maintain high-quality docstrings/documentation in your Python code. In addition, it leverages Large Language Models (LLMs) to ensure that your docstrings are semantically consistent with your code.

> [!NOTE]
> **Dolce** is still in early development. While it is functional, some features are yet to be implemented and improvements are ongoing. Your feedback and contributions are highly appreciated!

## 🚀 Quick showcase

Check docstrings issues with static and LLM-powered rules:
<img src="docs/src/statics/check.svg"/>

Suggest missing docstrings by leveraging LLMs:

<img src="docs/src/statics/sugg.svg"/>

Restyle your entire codebase docstrings to a consistent format:

<img src="docs/src/statics/restyle.svg"/>

## ✨ Features

- **Comprensive Rule Set**: Comes with a variety of built-in rules to check for common docstring issues, including:
  Static rules:
  - Missing docstrings
  - Incomplete parameter documentation
  - Signature mismatches
  .. etc

  and LLM-powered rules:
  - Consistency between code and docstring
  - Detection of undocumented critical behaviors
  ... etc

- **Generation docstrings**: Generate missing docstrings across your codebase (with the help of LLMs) by running a single command.

- **Restyling**: Automatically restyle your existing docstrings to a consistent format (Google, NumPy, ReST, Epy, etc.).

- **Customizable**: Easily configure which rules to apply, LLMs config (model, provider, url, etc.), and other settings via a `pyproject.toml` file.

... more features coming soon!

## 📦 Installation

You can install **dolce** globally via pip:

```bash
pip install pydolce
```

However, the recommended use is to install it as a dev dependency in your project environment. If you are using [uv](https://docs.astral.sh/uv/) for managing your Python projects, you can add it to your `pyproject.toml` like this:

```toml
[dependency-groups]
dev = [
    # ... your dev dependencies
    "pydolce",
]
```

> Don't forget to sync: `uv sync --all-groups`

Then you can use it by running:

```bash
uv run dolce [COMMAND]
```

## 💻 Usage

### Check docstrings

```bash
dolce check [PATH] # If no PATH is provided it will check the current directory
```

### Generate missing docstrings

```bash
dolce suggest [PATH] # If no PATH is provided it will run in the current directory
```

### Quick reference of available rules

```bash
dolce rules
```

## ⚙️ Configure

**Dolce** can be configured via `pyproject.toml` file. You can specify which rules to check and which to ignore. By default it will check all rules.

```toml
[tool.dolce]
target = [
  # Set of rules to check
  "DCE101",
]
disable = [
  # Set of rules to ignore
  "DCE102",
]
```

### Use of LLM

By default **dolce** does not make use of LLM features (like smart check rules or doccstring suggestions). To enable them you need to configure the LLM options in the `pyproject.toml` file like this:

```toml
[tool.dolce]
url = "http://localhost:11434"
model = "qwen3:8b"
provider = "ollama"
api_key = "YOUR_API_KEY_ENVIROMENT_VAR" # Optional, needed for non local providers
```

> [!TIP]
> `qwen3:8b` has relatively good performance while fitting in an RTX 4060 GPU (8GB VRAM)

You can visit the [Ollama](https://ollama.com/) to check how to install and run models locally.

## To be implemented

- Add cache system to avoid re-checking unchanged code
- Support for ignoring specific code segments, files, directories, etc
- Support parallel requests
... much more!

---

## 👩‍💻 For Developers

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