# Security Policy

## Supported Versions

This project is a single evolving codebase — there are no separately maintained
release branches. Security fixes are applied to the default branch only.

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use GitHub's private reporting flow:

1. Go to the **Security** tab of this repository
2. Click **Report a vulnerability**
3. Describe the issue, its impact, and steps to reproduce it

You should receive an acknowledgement within a few days. Once a fix is
available it will be released on the default branch and, where relevant,
noted in the commit message.

## Scope Notes

Markbase is a local CLI tool that generates a static site from your own
markdown notes. It does not run a server, accept untrusted input over a
network, or handle authentication — the main things worth reporting are:

- Your LLM provider API key ever being written somewhere other than `.env`
  (which is gitignored)
- Generated HTML/JS in `site/` executing anything beyond rendering your own
  content (e.g. unescaped injection from document content or filenames)
- Dependency vulnerabilities in `requirements.txt`
