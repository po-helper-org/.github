#!/usr/bin/env python3
"""Проверка ретро-кейсов: формат по SOLUTIONS.md, покрытие PR, обезличивание публичных репо.

    python3 lint_solutions.py <OUT> <досье.json>

OUT — каталог, где лежат docs/solutions/ и retro-report.md. Код выхода 1 — есть ошибки.
Предупреждения (возможные ФИО) — на глаз человеку, код не меняют.
"""
import json
import os
import re
import sys
from pathlib import Path

REQUIRED_KEYS = ("title", "date", "kind", "area", "prs", "source")
KINDS = {"bug", "incident", "feature", "perf", "ops", "security"}
SECTIONS = ("## Ситуация", "## Причина", "## Решение", "## Как проверить")
NAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(-[a-z0-9]+)*\.md$")

# Явные утечки для публичных репо — ошибка. Внутренние домены, ключи задач и имена,
# которые нельзя публиковать даже в этом файле, — в приватном списке регулярок
# (по строке на шаблон), путь — переменная SOLUTIONS_LINT_PRIVATE.
LEAKS = {
    "IP-адрес": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "комната Matrix": re.compile(r"![A-Za-z]{12,}"),
    "учётка Matrix": re.compile(r"@[\w.-]+:[\w.-]+"),
    "e-mail": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.]+\b"),
}
_private = os.environ.get("SOLUTIONS_LINT_PRIVATE")
if _private and Path(_private).exists():
    for i, line in enumerate(Path(_private).read_text().splitlines()):
        if line.strip() and not line.startswith("#"):
            LEAKS[f"приватный шаблон {i + 1}"] = re.compile(line.strip(), re.I)
# Похоже на ключ задачи трекера — предупреждение (бывают и ADR-0001, UTF-8).
TICKET_RE = re.compile(r"\b[A-Z]{2,10}-\d{1,6}\b")
# Похоже на «Имя Фамилия» — предупреждение.
PERSON_RE = re.compile(r"\b[А-ЯЁ][а-яё]{2,} [А-ЯЁ][а-яё]+(?:ов|ев|ёв|ин|ын|ий|ой|ова|ева|ина|ына|ская|ский|ко|ук|юк|ян)\b")


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            meta[k.strip()] = v.split("#", 1)[0].strip()
    return meta, text[m.end():]


def main(out, dossier_path):
    out = Path(out)
    dossier = json.loads(Path(dossier_path).read_text())
    public = dossier.get("visibility") == "PUBLIC"
    numbers = {p["number"] for p in dossier["prs"]}
    sol = out / "docs" / "solutions"
    errors, warnings, covered = [], [], set()

    cases = sorted(p for p in sol.glob("*.md") if p.name != "README.md")
    for path in cases:
        text = path.read_text()
        where = path.name
        if not NAME_RE.match(path.name):
            errors.append(f"{where}: имя не по шаблону ГГГГ-ММ-ДД-slug.md")
        meta, body = frontmatter(text)
        if meta is None:
            errors.append(f"{where}: нет frontmatter")
            continue
        for k in REQUIRED_KEYS:
            if not meta.get(k):
                errors.append(f"{where}: нет поля {k}")
        if meta.get("kind") and meta["kind"] not in KINDS:
            errors.append(f"{where}: kind={meta['kind']} не из {sorted(KINDS)}")
        prs = {int(n) for n in re.findall(r"\d+", meta.get("prs", ""))}
        if not prs:
            errors.append(f"{where}: пустой prs")
        if prs - numbers:
            errors.append(f"{where}: PR {sorted(prs - numbers)} нет в досье")
        covered |= prs
        for s in SECTIONS:
            if s not in body:
                errors.append(f"{where}: нет раздела «{s[3:]}»")
        if public:
            for label, rx in LEAKS.items():
                for hit in set(rx.findall(text)):
                    errors.append(f"{where}: {label}: {hit if isinstance(hit, str) else hit[0]}")
            for hit in set(TICKET_RE.findall(text)) - {"UTF-8"}:
                warnings.append(f"{where}: похоже на ключ задачи: {hit}")
            for hit in set(PERSON_RE.findall(text)):
                warnings.append(f"{where}: похоже на ФИО: {hit}")

    readme = sol / "README.md"
    if not readme.exists():
        errors.append("docs/solutions/README.md: нет индекса")
    else:
        idx = readme.read_text()
        for path in cases:
            if path.name not in idx:
                errors.append(f"README.md: в индексе нет {path.name}")

    report = out / "retro-report.md"
    reported = set()
    if not report.exists():
        errors.append("retro-report.md: нет отчёта")
    else:
        for line in report.read_text().splitlines():
            m = re.match(r"^\s*[-*]?\s*#(\d+)\s*→\s*(.+)$", line)
            if m:
                reported.add(int(m.group(1)))
                if m.group(2).startswith("пропуск") and ":" not in m.group(2):
                    errors.append(f"retro-report.md: #{m.group(1)} — пропуск без причины")
    missing = numbers - covered - reported
    if missing:
        errors.append(f"PR без кейса и без строки в отчёте: {sorted(missing)}")

    for w in warnings:
        print("ПРЕДУПРЕЖДЕНИЕ", w)
    for e in errors:
        print("ОШИБКА", e)
    print(f"кейсов: {len(cases)}, PR в кейсах: {len(covered & numbers)}/{len(numbers)}, "
          f"ошибок: {len(errors)}, предупреждений: {len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
