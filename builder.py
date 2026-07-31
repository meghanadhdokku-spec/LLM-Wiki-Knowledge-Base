"""Static site generator for Markbase."""
import json
import os
import shutil

import frontmatter
import jinja2
import markdown as md


def parse_md_file(path):
    post = frontmatter.load(path)
    return post.content, post.metadata


def strip_frontmatter(path):
    post = frontmatter.load(path)
    return post.content


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_site(config):
    index_path = os.path.join(config["content_dir"], "_index.json")
    with open(index_path, "r") as f:
        index = json.load(f)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    output_dir = config["output_dir"]

    shutil.rmtree(output_dir, ignore_errors=True)
    os.makedirs(output_dir, exist_ok=True)

    docs_by_slug = {d["slug"]: d for d in index["documents"]}

    # Build each document page
    for doc in index["documents"]:
        content, fm = parse_md_file(doc["path"])
        html_body = md.markdown(content, extensions=["fenced_code", "tables", "toc"])

        related_docs = [docs_by_slug[s] for s in doc.get("related", []) if s in docs_by_slug]

        page_html = env.get_template("page.html").render(
            site=config,
            doc=doc,
            content=html_body,
            categories=config["categories"],
            current_category=doc["category"],
            related_docs=related_docs,
        )

        out_path = f"{output_dir}/{doc['category']}/{doc['slug']}.html"
        write_file(out_path, page_html)

    # Build category index pages
    for cat in config["categories"]:
        cat_docs = sorted(
            [d for d in index["documents"] if d["category"] == cat["slug"]],
            key=lambda d: d["modified"],
            reverse=True,
        )
        cat_html = env.get_template("category.html").render(
            site=config,
            category=cat,
            documents=cat_docs,
            categories=config["categories"],
            current_category=cat["slug"],
        )
        out_path = f"{output_dir}/{cat['slug']}/index.html"
        write_file(out_path, cat_html)

    # Build homepage
    recent = sorted(index["documents"], key=lambda d: d["modified"], reverse=True)[:10]
    cat_counts = {}
    for d in index["documents"]:
        cat_counts[d["category"]] = cat_counts.get(d["category"], 0) + 1

    home_html = env.get_template("home.html").render(
        site=config,
        recent=recent,
        categories=config["categories"],
        documents=index["documents"],
        cat_counts=cat_counts,
        current_category=None,
    )
    write_file(f"{output_dir}/index.html", home_html)

    # Build search index
    search_data = []
    for doc in index["documents"]:
        body = strip_frontmatter(doc["path"])
        search_data.append({
            "slug": doc["slug"],
            "title": doc["title"],
            "category": doc["category"],
            "tags": " ".join(doc.get("tags", [])),
            "summary": doc.get("summary", ""),
            "body": body[:2000],
            "url": f"{doc['category']}/{doc['slug']}.html",
        })
    write_file(f"{output_dir}/search-index.json", json.dumps(search_data, indent=2))

    # Copy static assets
    shutil.copytree("static", f"{output_dir}/static", dirs_exist_ok=True)

    print(f"Built {len(index['documents'])} pages across {len(config['categories'])} categories.")
