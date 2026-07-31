# Contributing to Markbase

Thanks for considering a contribution — this is a small, focused tool, so contributing should be quick.

## Setup

```bash
git clone https://github.com/meghanadhdokku-spec/LLM-Wiki-Knowledge-Base.git
cd LLM-Wiki-Knowledge-Base
pip install -r requirements.txt
```

To test the ingest → build pipeline without an LLM API key, use the dry-run flag:

```bash
python wiki.py ingest --dry-run
python wiki.py build
python wiki.py serve
```

## Making changes

- Keep `wiki.py`, `llm.py`, and `builder.py` dependency-light — no new packages unless there's a real need
- Match the existing style: no framework CSS, no unnecessary abstractions, comments only where the *why* isn't obvious from the code
- If you touch the ingest/build pipeline, verify the full flow still works: `ingest --dry-run` → `build` → `serve`, and check the site renders correctly (search included)
- If you add a new LLM provider, follow the pattern in `llm.py` (`OPENAI_COMPATIBLE_BASE_URLS`) and `wiki.py` (`ENV_VAR_NAMES`, `DEFAULT_MODELS`) — most providers only need a base URL and a default model

## Submitting a PR

- `main` is protected — all changes go through a pull request
- Keep PRs focused; one change per PR is easier to review than a bundle
- Describe what changed and why in the PR description — the CodeQL workflow runs automatically on every PR

## Reporting bugs or security issues

- Bugs: open a GitHub issue
- Security vulnerabilities: see [SECURITY.md](SECURITY.md) — please don't file those as public issues
