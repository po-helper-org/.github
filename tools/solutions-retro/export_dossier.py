#!/usr/bin/env python3
"""Досье слитых PR репозитория для ретро-кейсов docs/solutions/.

Запуск — там, где есть `gh` с доступом к организации (у сервера его нет):
    python3 export_dossier.py po-helper-org/<репо> > <репо>.json

В досье: номер, заголовок, описание, дата слияния, файлы (путь и объём правки),
метки, последние комментарии и список уже существующих docs/ (чтобы ссылаться на ADR).
Тексты урезаются — агенту хватает сути, а не всей переписки.
"""
import json
import subprocess
import sys

BODY_MAX = 8000
COMMENT_MAX = 800
COMMENTS_KEEP = 4
FILES_KEEP = 60


def gh(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout
    return json.loads(out) if out.strip() else None


def cut(text, limit):
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit] + "\n…[урезано]"


def docs_tree(repo):
    try:
        tree = gh("api", f"repos/{repo}/git/trees/HEAD?recursive=1")
    except subprocess.CalledProcessError:
        return []
    return [t["path"] for t in tree.get("tree", []) if t["path"].startswith("docs/") and t["type"] == "blob"]


def main(repo):
    prs = gh("pr", "list", "-R", repo, "--state", "merged", "--limit", "500", "--json",
             "number,title,body,mergedAt,url,files,labels,comments,headRefName")
    items = []
    for pr in sorted(prs, key=lambda p: p["number"]):
        files = pr.get("files") or []
        items.append({
            "number": pr["number"],
            "title": pr["title"],
            "merged_at": pr["mergedAt"][:10],
            "url": pr["url"],
            "branch": pr.get("headRefName"),
            "labels": [l["name"] for l in pr.get("labels") or []],
            "body": cut(pr.get("body"), BODY_MAX),
            "files": [f"{f['path']} (+{f['additions']}/-{f['deletions']})" for f in files[:FILES_KEEP]],
            "files_total": len(files),
            "comments": [cut(c.get("body"), COMMENT_MAX) for c in (pr.get("comments") or [])[-COMMENTS_KEEP:]],
        })
    meta = gh("repo", "view", repo, "--json", "name,visibility,description")
    json.dump({"repo": repo, "visibility": meta["visibility"], "description": meta.get("description"),
               "docs": docs_tree(repo), "prs": items}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
