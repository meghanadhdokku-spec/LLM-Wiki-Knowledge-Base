#!/usr/bin/env python3
"""Markbase — a self-organizing markdown wiki. Main CLI."""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

import frontmatter
from dotenv import load_dotenv
from slugify import slugify

from llm import LLMClient, DEFAULT_MODELS

CONFIG_PATH = "wiki.config.json"
INDEX_PATH = "content/_index.json"
ENV_PATH = ".env"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"


def ok(msg):
    print(f"{GREEN}{msg}{RESET}")


def err(msg):
    print(f"{RED}{msg}{RESET}")


def info(msg):
    print(f"{YELLOW}{msg}{RESET}")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Config / index persistence
# ---------------------------------------------------------------------------

def load_config():
    if not os.path.exists(CONFIG_PATH):
        err(f"No {CONFIG_PATH} found. Run 'python wiki.py setup' first.")
        sys.exit(1)
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def load_index():
    if not os.path.exists(INDEX_PATH):
        return {"last_updated": now_iso(), "document_count": 0, "documents": []}
    with open(INDEX_PATH, "r") as f:
        return json.load(f)


def save_index(index):
    index["last_updated"] = now_iso()
    index["document_count"] = len(index["documents"])
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)


ENV_VAR_NAMES = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "groq": "GROQ_API_KEY",
}


def write_env_file(provider, api_key):
    var_name = ENV_VAR_NAMES.get(provider, "OPENAI_API_KEY")
    with open(ENV_PATH, "w") as f:
        f.write(f"{var_name}={api_key}\n")


def get_api_key(provider):
    var_name = ENV_VAR_NAMES.get(provider, "OPENAI_API_KEY")
    return os.environ.get(var_name)


def make_client(config):
    provider = config["llm"]["provider"]
    model = config["llm"].get("model") or DEFAULT_MODELS.get(provider)
    api_key = get_api_key(provider)
    return LLMClient(provider, model, api_key)


def create_directories(config):
    for cat in config["categories"]:
        os.makedirs(f"{config['content_dir']}/{cat['slug']}", exist_ok=True)
    os.makedirs(config["source_dir"], exist_ok=True)


# ---------------------------------------------------------------------------
# Setup wizard
# ---------------------------------------------------------------------------

SETUP_SYSTEM_PROMPT = """You are a setup assistant for Markbase, a markdown knowledge base tool.
Your job is to interview the user to create their wiki configuration.

Ask these questions ONE AT A TIME. Wait for each answer before proceeding.

1. Ask: "What will this wiki be about? Describe the topics or domain you'll be documenting."
2. Based on their answer, suggest a wiki name. Ask if they like it or want something different.
3. Suggest 4-6 categories with short descriptions based on their domain. Show them as a numbered list. Ask if they want to add, remove, or rename any.
4. Suggest 8-12 tags based on the agreed categories. Ask if they want to modify the list.
5. When done, output the line SETUP_COMPLETE on its own line, followed by a JSON code block with the configuration.

The JSON must follow this exact schema:
{
  "name": "Wiki Name",
  "description": "One-line description",
  "categories": [
    {"name": "Display Name", "slug": "url-slug", "description": "Short description"}
  ],
  "tags": ["tag1", "tag2"]
}

Rules:
- Always include "Uncategorized" as the last category with slug "uncategorized".
- Keep slugs lowercase, hyphenated, no special characters.
- Be concise in your responses. No long explanations.
- tags should be lowercase."""


def extract_json(response):
    idx = response.find("SETUP_COMPLETE")
    tail = response[idx:] if idx != -1 else response
    start = tail.find("{")
    end = tail.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Could not find JSON config in LLM response.")
    return json.loads(tail[start:end + 1])


def build_full_config(config, provider):
    categories = config.get("categories", [])
    if not any(c.get("slug") == "uncategorized" for c in categories):
        categories.append({
            "name": "Uncategorized",
            "slug": "uncategorized",
            "description": "Documents that don't fit elsewhere",
        })
    return {
        "name": config.get("name", "My Knowledge Base"),
        "description": config.get("description", ""),
        "llm": {
            "provider": provider,
            "model": DEFAULT_MODELS.get(provider),
        },
        "categories": categories,
        "tags": sorted(set(t.lower() for t in config.get("tags", []))),
        "source_dir": "source",
        "content_dir": "content",
        "output_dir": "site",
    }


def cmd_setup(args):
    valid_providers = tuple(ENV_VAR_NAMES.keys())
    provider = input(f"LLM provider ({'/'.join(valid_providers)}): ").strip().lower()
    while provider not in valid_providers:
        provider = input(f"Please enter one of: {', '.join(valid_providers)}: ").strip().lower()

    api_key = input(f"Enter your {provider} API key: ").strip()
    write_env_file(provider, api_key)
    ok(f"Saved API key to {ENV_PATH}")

    client = LLMClient(provider, DEFAULT_MODELS[provider], api_key)

    messages = ["I want to set up my wiki. Let's go."]
    config = None

    while True:
        try:
            response = client.chat(SETUP_SYSTEM_PROMPT, messages)
        except ValueError as e:
            err(str(e))
            sys.exit(1)

        messages.append(response)
        print(f"\nMarkbase: {response}\n")

        if "SETUP_COMPLETE" in response:
            config = extract_json(response)
            break

        user_input = input("You: ").strip()
        messages.append(user_input)

    full_config = build_full_config(config, provider)
    save_config(full_config)
    create_directories(full_config)
    save_index({"last_updated": now_iso(), "document_count": 0, "documents": []})

    ok("\nSetup complete!")
    print(f"Wiki: {full_config['name']}")
    print(f"Categories: {', '.join(c['slug'] for c in full_config['categories'])}")
    print("\nNext steps:")
    print("  1. Drop .md files into source/")
    print("  2. Run 'python wiki.py ingest'")
    print("  3. Run 'python wiki.py build'")
    print("  4. Run 'python wiki.py serve'")


# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

INGEST_SYSTEM_PROMPT = """You are a document categorizer for a Markbase wiki.
Analyze the given markdown document and return structured metadata.

Available categories:
{categories}

Existing tags in the wiki:
{tags}

Existing documents (title | slug | category):
{index_summary}

Instructions:
- Pick the single best category slug. Use "uncategorized" only as last resort.
- Reuse existing tags when they fit. Create at most 2 new tags if needed.
- Summary: one sentence, under 120 characters, no period at the end.
- Related: pick 0-3 existing document slugs that cover similar topics.
- Title: use the document's first heading if it has one, otherwise generate a clear title.

Return ONLY valid JSON with no markdown fences and no extra text:
{{"title": "string", "category": "category-slug", "tags": ["tag1"], "summary": "string", "related": ["slug1"]}}"""


def build_index_summary(index):
    if not index["documents"]:
        return "(none yet)"
    lines = [f"{d['title']} | {d['slug']} | {d['category']}" for d in index["documents"]]
    return "\n".join(lines)


DRY_RUN_KEYWORDS = {
    "devops": ["docker", "container", "ci/cd", "pipeline", "deploy", "kubernetes"],
    "databases": ["postgres", "sql", "index", "query", "database", "gin", "b-tree"],
    "programming": ["python", "javascript", "async", "function", "comprehension", "code"],
}

DRY_RUN_TAGS = {
    "devops": ["docker", "tutorial"],
    "databases": ["reference"],
    "programming": ["python", "javascript"],
}


def dry_run_categorize(body, config, index):
    """Hardcoded categorization used when --dry-run is passed (no LLM call)."""
    title = None
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if not title:
        title = "Untitled Document"

    cat_slugs = {c["slug"] for c in config["categories"]}
    lower = body.lower()

    category = "uncategorized"
    best_score = 0
    for slug, keywords in DRY_RUN_KEYWORDS.items():
        if slug not in cat_slugs:
            continue
        score = sum(1 for kw in keywords if kw in lower)
        if score > best_score:
            best_score = score
            category = slug
    if best_score == 0:
        category = "programming" if "programming" in cat_slugs else next(iter(cat_slugs), "uncategorized")

    body_lines = [l.strip() for l in body.strip().splitlines() if l.strip() and not l.strip().startswith("#")]
    summary = body_lines[0] if body_lines else title
    summary = summary.rstrip(".")[:120]

    tags = [t for t in DRY_RUN_TAGS.get(category, []) if t in config["tags"]]
    if not tags:
        tags = config["tags"][:1] if config["tags"] else []

    return {
        "title": title,
        "category": category,
        "tags": tags,
        "summary": summary,
        "related": [],
    }


def update_index(index, final_fm, dest):
    entry = {
        "slug": final_fm["slug"],
        "title": final_fm["title"],
        "category": final_fm["category"],
        "tags": final_fm["tags"],
        "summary": final_fm["summary"],
        "path": dest,
        "created": final_fm["created"],
        "modified": final_fm["modified"],
        "related": final_fm["related"],
    }
    index["documents"] = [d for d in index["documents"] if d["slug"] != entry["slug"]]
    index["documents"].append(entry)


def cmd_ingest(args):
    config = load_config()
    index = load_index()

    if args.file:
        files = [args.file] if os.path.exists(args.file) else []
        if not files:
            err(f"File not found: {args.file}")
            sys.exit(1)
    else:
        files = sorted(glob.glob(os.path.join(config["source_dir"], "*.md")))

    if not files:
        print("No files to ingest.")
        sys.exit(0)

    client = None
    if not args.dry_run:
        client = make_client(config)

    for f in files:
        post = frontmatter.load(f)
        existing_fm = dict(post.metadata)
        body = post.content

        if args.dry_run:
            metadata = dry_run_categorize(body, config, index)
        else:
            categories = json.dumps(config["categories"], indent=2)
            tags = ", ".join(config["tags"]) or "(none yet)"
            index_summary = build_index_summary(index)
            system_prompt = INGEST_SYSTEM_PROMPT.format(
                categories=categories, tags=tags, index_summary=index_summary
            )
            metadata = client.chat_json(system_prompt, body)

        final_fm = {**metadata, **existing_fm}
        final_fm.setdefault("title", metadata.get("title", "Untitled"))
        final_fm["slug"] = existing_fm.get("slug") or slugify(final_fm["title"])
        final_fm["category"] = final_fm.get("category", "uncategorized")
        final_fm["tags"] = [t.lower() for t in final_fm.get("tags", [])]
        final_fm["summary"] = final_fm.get("summary", "")[:120]
        final_fm["related"] = final_fm.get("related", [])
        final_fm["created"] = existing_fm.get("created", today())
        final_fm["modified"] = today()
        final_fm["status"] = "published"

        cat_slugs = {c["slug"] for c in config["categories"]}
        if final_fm["category"] not in cat_slugs:
            config["categories"].append({
                "name": final_fm["category"].replace("-", " ").title(),
                "slug": final_fm["category"],
                "description": "Auto-created category",
            })

        cat_dir = f"{config['content_dir']}/{final_fm['category']}"
        os.makedirs(cat_dir, exist_ok=True)

        dest = f"{cat_dir}/{final_fm['slug']}.md"
        new_post = frontmatter.Post(body, **final_fm)
        with open(dest, "wb") as out:
            out.write(frontmatter.dumps(new_post).encode("utf-8"))

        update_index(index, final_fm, dest)

        if os.path.abspath(f) != os.path.abspath(dest):
            os.remove(f)

        new_tags = set(final_fm["tags"]) - set(config["tags"])
        if new_tags:
            config["tags"].extend(sorted(new_tags))

        ok(f"  ✓ {final_fm['title']} → {final_fm['category']}/{final_fm['slug']}")

    save_index(index)
    save_config(config)
    print(f"\nIngested {len(files)} file(s).")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def cmd_build(args):
    config = load_config()
    from builder import build_site
    build_site(config)


# ---------------------------------------------------------------------------
# Serve
# ---------------------------------------------------------------------------

def cmd_serve(args):
    config = load_config()
    from builder import build_site
    build_site(config)

    import functools
    import http.server

    output_dir = config["output_dir"]
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=output_dir)
    httpd = http.server.HTTPServer(("", args.port), handler)
    print(f"Serving {output_dir}/ at http://localhost:{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

def cmd_status(args):
    config = load_config()
    index = load_index()

    print(f"{BOLD}{config['name']}{RESET}")
    print(f"Total documents: {len(index['documents'])}")

    print("\nDocuments per category:")
    counts = {}
    for d in index["documents"]:
        counts[d["category"]] = counts.get(d["category"], 0) + 1
    for cat in config["categories"]:
        print(f"  {cat['slug']}: {counts.get(cat['slug'], 0)}")

    print("\nMost used tags:")
    tag_counts = {}
    for d in index["documents"]:
        for t in d.get("tags", []):
            tag_counts[t] = tag_counts.get(t, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    if top_tags:
        for tag, count in top_tags:
            print(f"  {tag}: {count}")
    else:
        print("  (none)")

    pending = glob.glob(os.path.join(config["source_dir"], "*.md"))
    print(f"\nFiles waiting in {config['source_dir']}/: {len(pending)}")

    output_index = os.path.join(config["output_dir"], "index.html")
    if os.path.exists(output_index):
        mtime = datetime.fromtimestamp(os.path.getmtime(output_index), tz=timezone.utc)
        print(f"Last build: {mtime.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        print("Last build: never")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    load_dotenv()

    parser = argparse.ArgumentParser(prog="wiki.py", description="Markbase — LLM-powered markdown knowledge base")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("setup", help="Interactive first-time setup")

    p_ingest = sub.add_parser("ingest", help="Ingest files from source/ into content/")
    p_ingest.add_argument("file", nargs="?", default=None, help="Ingest a single file instead of all of source/")
    p_ingest.add_argument("--dry-run", action="store_true", help="Categorize using hardcoded rules instead of calling the LLM")

    sub.add_parser("build", help="Generate the static site")

    p_serve = sub.add_parser("serve", help="Build and serve the site locally")
    p_serve.add_argument("--port", type=int, default=8000, help="Port to serve on (default 8000)")

    sub.add_parser("status", help="Show wiki stats")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "setup":
            cmd_setup(args)
        elif args.command == "ingest":
            cmd_ingest(args)
        elif args.command == "build":
            cmd_build(args)
        elif args.command == "serve":
            cmd_serve(args)
        elif args.command == "status":
            cmd_status(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        err(f"Error: {e}")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
