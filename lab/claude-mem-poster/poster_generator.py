#!/usr/bin/env python3
"""
Reusable poster generator for markdown, JSON/YAML, HTML, URLs, and raw text.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


THEMES = {"auto", "research", "technical", "summary", "project"}


THEME_STYLES: dict[str, dict[str, str]] = {
    "research": {
        "bg_top": "#efe6d7",
        "bg_bottom": "#e6d9c4",
        "paper_top": "#fbf6ec",
        "paper_bottom": "#f7efdf",
        "ink": "#2b241e",
        "muted": "#706457",
        "line": "rgba(196, 173, 141, 0.40)",
        "accent": "#c57c2f",
        "accent_2": "#5e83bc",
        "accent_3": "#5b9270",
        "accent_4": "#7a68b1",
        "hero_glow": "rgba(255,255,255,0.45)",
    },
    "technical": {
        "bg_top": "#e8eef7",
        "bg_bottom": "#d9e3f1",
        "paper_top": "#f7faff",
        "paper_bottom": "#edf3fb",
        "ink": "#1f2630",
        "muted": "#5d6b7c",
        "line": "rgba(113, 137, 172, 0.30)",
        "accent": "#4b7bd3",
        "accent_2": "#2f9d8f",
        "accent_3": "#8a65d6",
        "accent_4": "#d98546",
        "hero_glow": "rgba(255,255,255,0.40)",
    },
    "summary": {
        "bg_top": "#f0ebe2",
        "bg_bottom": "#e7dfd1",
        "paper_top": "#fffaf3",
        "paper_bottom": "#fbf4ea",
        "ink": "#32271f",
        "muted": "#756659",
        "line": "rgba(205, 182, 148, 0.35)",
        "accent": "#d27f54",
        "accent_2": "#7a96d8",
        "accent_3": "#76ad8b",
        "accent_4": "#c08abf",
        "hero_glow": "rgba(255,255,255,0.48)",
    },
    "project": {
        "bg_top": "#ece6d8",
        "bg_bottom": "#ddd6c7",
        "paper_top": "#fdf9f0",
        "paper_bottom": "#f8f0e5",
        "ink": "#2a2520",
        "muted": "#70675f",
        "line": "rgba(191, 176, 149, 0.34)",
        "accent": "#cb8750",
        "accent_2": "#5683b3",
        "accent_3": "#73a979",
        "accent_4": "#9277c9",
        "hero_glow": "rgba(255,255,255,0.40)",
    },
}


def load_yaml(path: Path) -> Any:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "YAML input requires PyYAML. Install it with: pip install pyyaml"
        ) from exc

    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate poster PNG or HTML from structured content."
    )
    parser.add_argument("input", help="Path, URL, or raw text content")
    parser.add_argument(
        "--theme",
        default="auto",
        choices=sorted(THEMES),
        help="Poster theme: auto, research, technical, summary, project",
    )
    parser.add_argument("--output", help="Output PNG path")
    parser.add_argument("--html-output", help="Optional output HTML path")
    parser.add_argument("--title", help="Override title")
    parser.add_argument("--subtitle", help="Override subtitle")
    parser.add_argument("--width", type=int, default=820, help="Poster width in pixels")
    return parser.parse_args(argv)


def is_url(text: str) -> bool:
    return bool(re.match(r"^https?://", text.strip(), re.IGNORECASE))


def sanitize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def strip_html(text: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|li|h[1-6]|section|article)>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def fetch_url_content(url: str) -> dict[str, Any]:
    try:
        with urlopen(url, timeout=20) as response:
            body = response.read().decode("utf-8", errors="ignore")
            content_type = response.headers.get_content_type()
    except URLError as exc:
        raise RuntimeError(
            f"Failed to fetch URL '{url}'. Provide local content or fetch it before running /poster."
        ) from exc

    if "html" in content_type:
        title_match = re.search(r"<title>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
        title = strip_html(title_match.group(1)) if title_match else url
        text = strip_html(body)
        return parse_text_content(text, source_type="url", title_hint=title, source_name=url)

    return parse_text_content(body, source_type="url", title_hint=url, source_name=url)


def parse_markdown(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    title = path.stem
    subtitle = ""
    intro_lines: list[str] = []
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] | None = None

    for index, raw_line in enumerate(lines):
        line = raw_line.rstrip()
        previous_line = lines[index - 1].strip() if index > 0 else ""
        next_nonempty_line = next(
            (candidate.strip() for candidate in lines[index + 1 :] if candidate.strip()),
            "",
        )
        if not line.strip():
            if current_section is not None:
                current_section.setdefault("blocks", []).append("")
            continue

        if line.startswith("# "):
            title = line[2:].strip()
            continue

        if line.startswith("## "):
            current_section = {"title": line[3:].strip(), "blocks": []}
            sections.append(current_section)
            continue

        if line.startswith("### "):
            if current_section is None:
                current_section = {"title": "Details", "blocks": []}
                sections.append(current_section)
            current_section["blocks"].append(f"__subhead__:{line[4:].strip()}")
            continue

        if is_plain_section_heading(line, previous_line, next_nonempty_line):
            current_section = {"title": line.strip(), "blocks": []}
            sections.append(current_section)
            continue

        if current_section is None:
            intro_lines.append(line.strip())
        else:
            current_section["blocks"].append(line.strip())

    subtitle = intro_lines[0] if intro_lines else ""
    summary = " ".join(intro_lines[1:] if len(intro_lines) > 1 else intro_lines)

    normalized_sections = [normalize_section_from_blocks(section) for section in sections]
    return normalize_document(
        {
            "title": title,
            "subtitle": subtitle,
            "summary": summary,
            "sections": normalized_sections,
            "source_type": "markdown",
            "source_name": str(path),
        }
    )


def is_plain_section_heading(line: str, previous_line: str, next_nonempty_line: str) -> bool:
    text = line.strip()
    if not text or previous_line:
        return False
    if text.startswith(("#", "-", "*", "```")):
        return False
    if re.match(r"^\d+\.\s+", text):
        return False
    if re.search(r"https?://|<[^>]+>", text):
        return False
    if any(marker in text for marker in [":", "："]):
        return False
    if len(text) > 32:
        return False
    if not next_nonempty_line:
        return False
    if next_nonempty_line.startswith(("#", "```")):
        return False
    if re.search(r"https?://|<[^>]+>", next_nonempty_line):
        return False
    return True


def normalize_section_from_blocks(section: dict[str, Any]) -> dict[str, Any]:
    paragraphs: list[str] = []
    bullets: list[str] = []
    subheads: list[str] = []
    current_paragraph: list[str] = []

    def flush_paragraph() -> None:
        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph).strip())
            current_paragraph.clear()

    for block in section.get("blocks", []):
        if not block:
            flush_paragraph()
            continue
        if block.startswith("__subhead__:"):
            flush_paragraph()
            subheads.append(block.split(":", 1)[1].strip())
            continue
        if re.match(r"^[-*]\s+", block):
            flush_paragraph()
            bullets.append(re.sub(r"^[-*]\s+", "", block).strip())
            continue
        if re.match(r"^\d+\.\s+", block):
            flush_paragraph()
            bullets.append(re.sub(r"^\d+\.\s+", "", block).strip())
            continue
        current_paragraph.append(block)

    flush_paragraph()
    if paragraphs:
        body = paragraphs[0]
        extra = paragraphs[1:]
    elif bullets:
        body = bullets[0]
        extra = []
        bullets = bullets[1:]
    else:
        body = ""
        extra = []
    return {
        "title": sanitize_text(section.get("title") or "Section"),
        "body": body,
        "bullets": bullets,
        "paragraphs": extra,
        "subheads": subheads,
    }


def parse_text_content(
    text: str,
    source_type: str = "text",
    title_hint: str | None = None,
    source_name: str | None = None,
) -> dict[str, Any]:
    clean = text.strip()
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", clean) if part.strip()]
    title = title_hint or "Poster Summary"
    subtitle = paragraphs[0][:96] if paragraphs else ""
    summary = paragraphs[0] if paragraphs else ""

    sections: list[dict[str, Any]] = []
    if len(paragraphs) > 1:
        for idx, paragraph in enumerate(paragraphs[1:5], start=1):
            sections.append(
                {
                    "title": f"Key Point {idx}",
                    "body": paragraph,
                    "bullets": [],
                    "paragraphs": [],
                    "subheads": [],
                }
            )
    else:
        sentences = [item.strip() for item in re.split(r"(?<=[。！？.!?])\s+", clean) if item.strip()]
        summary = sentences[0] if sentences else clean
        for idx, sentence in enumerate(sentences[1:5], start=1):
            sections.append(
                {
                    "title": f"Key Point {idx}",
                    "body": sentence,
                    "bullets": [],
                    "paragraphs": [],
                    "subheads": [],
                }
            )

    return normalize_document(
        {
            "title": title,
            "subtitle": subtitle,
            "summary": summary,
            "sections": sections,
            "source_type": source_type,
            "source_name": source_name or title,
        }
    )


def parse_input(input_value: str) -> dict[str, Any]:
    path = Path(input_value).expanduser()
    suffix = path.suffix.lower()

    if path.exists():
        if suffix == ".json":
            with path.open(encoding="utf-8") as handle:
                return normalize_document(json.load(handle) or {})
        if suffix in {".yaml", ".yml"}:
            return normalize_document(load_yaml(path) or {})
        if suffix == ".md":
            return parse_markdown(path)
        if suffix in {".html", ".htm"}:
            return {
                "type": "html",
                "title": path.stem,
                "html": path.read_text(encoding="utf-8"),
                "source_type": "html",
                "source_name": str(path),
            }
        return parse_text_content(path.read_text(encoding="utf-8"), source_type="text-file", title_hint=path.stem, source_name=str(path))

    if is_url(input_value):
        return fetch_url_content(input_value)

    return parse_text_content(input_value, source_type="text", title_hint="Poster Summary", source_name="raw text")


def normalize_document(data: dict[str, Any]) -> dict[str, Any]:
    title = sanitize_text(data.get("title")) or "Untitled Poster"
    subtitle = sanitize_text(data.get("subtitle"))
    summary = sanitize_text(data.get("summary"))
    date = sanitize_text(data.get("date")) or datetime.now().strftime("%Y-%m-%d")
    tags = [sanitize_text(item) for item in data.get("tags", []) if sanitize_text(item)]
    source_type = sanitize_text(data.get("source_type")) or "structured"
    source_name = sanitize_text(data.get("source_name")) or title
    footer = sanitize_text(data.get("footer"))

    sections = normalize_sections(data.get("sections", []))
    stats = normalize_stats(data.get("stats", []))
    decisions = normalize_cards(data.get("decisions", []), fallback_kicker="Decision")
    evidence = normalize_cards(data.get("evidence", []), fallback_kicker="Evidence")

    if not summary and sections:
        summary = sections[0]["body"] or "Structured content poster"
    if not subtitle:
        subtitle = summary[:96]

    if not tags:
        tags = default_tags(title, sections, source_type)

    if not stats:
        stats = fallback_stats(source_type, sections)

    if not decisions:
        decisions = derive_decisions(sections)

    if not evidence:
        evidence = derive_evidence(sections)

    return {
        "type": "document",
        "title": title,
        "subtitle": subtitle,
        "summary": summary,
        "date": date,
        "tags": tags,
        "stats": stats,
        "sections": sections,
        "decisions": decisions,
        "evidence": evidence,
        "footer": footer or f"Generated from {source_type} · {date}",
        "source_type": source_type,
        "source_name": source_name,
    }


def normalize_sections(raw_sections: Any) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_sections or [], start=1):
        if isinstance(raw, str):
            sections.append(
                {
                    "title": f"Section {index}",
                    "body": sanitize_text(raw),
                    "bullets": [],
                    "paragraphs": [],
                    "subheads": [],
                }
            )
            continue
        if not isinstance(raw, dict):
            continue

        bullets = [sanitize_text(item) for item in raw.get("bullets", []) if sanitize_text(item)]
        paragraphs = [sanitize_text(item) for item in raw.get("paragraphs", []) if sanitize_text(item)]
        subheads = [sanitize_text(item) for item in raw.get("subheads", []) if sanitize_text(item)]
        body = sanitize_text(raw.get("body"))
        sections.append(
            {
                "title": sanitize_text(raw.get("title")) or f"Section {index}",
                "body": body,
                "bullets": bullets,
                "paragraphs": paragraphs,
                "subheads": subheads,
            }
        )
    return sections


def normalize_stats(raw_stats: Any) -> list[dict[str, str]]:
    stats: list[dict[str, str]] = []
    for raw in raw_stats or []:
        if not isinstance(raw, dict):
            continue
        value = sanitize_text(raw.get("value"))
        label = sanitize_text(raw.get("label"))
        if not value or not label:
            continue
        stats.append(
            {
                "value": value,
                "label": label,
                "note": sanitize_text(raw.get("note")),
            }
        )
    return stats[:4]


def normalize_cards(raw_cards: Any, fallback_kicker: str) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for index, raw in enumerate(raw_cards or [], start=1):
        if isinstance(raw, str):
            cards.append(
                {
                    "kicker": f"{fallback_kicker} {index}",
                    "title": raw[:48],
                    "body": raw,
                }
            )
            continue
        if not isinstance(raw, dict):
            continue
        body = sanitize_text(raw.get("body"))
        title = sanitize_text(raw.get("title")) or body[:48]
        if not title:
            continue
        cards.append(
            {
                "kicker": sanitize_text(raw.get("kicker")) or f"{fallback_kicker} {index}",
                "title": title,
                "body": body,
            }
        )
    return cards[:4]


def default_tags(title: str, sections: list[dict[str, Any]], source_type: str) -> list[str]:
    tags = [source_type.upper()]
    title_lower = title.lower()
    if any(word in title_lower for word in ["research", "调研", "analysis", "report"]):
        tags.append("Research")
    if any(word in title_lower for word in ["tech", "技术", "architecture", "system", "api"]):
        tags.append("Technical")
    if any(word in title_lower for word in ["summary", "总结", "recap"]):
        tags.append("Summary")
    if len(tags) < 3 and sections:
        tags.append(sections[0]["title"])
    return tags[:4]


def fallback_stats(source_type: str, sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    bullet_count = sum(len(section.get("bullets", [])) for section in sections)
    return [
        {"value": source_type.upper(), "label": "Input Type", "note": "auto-detected"},
        {"value": str(len(sections)), "label": "Sections", "note": "normalized blocks"},
        {"value": str(bullet_count), "label": "Bullet Points", "note": "key takeaways"},
        {
            "value": datetime.now().strftime("%m-%d"),
            "label": "Build Date",
            "note": "poster render time",
        },
    ]


def derive_decisions(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    for index, section in enumerate(sections[:4], start=1):
        cards.append(
            {
                "kicker": f"Takeaway {index}",
                "title": section["title"],
                "body": section["body"] or "See poster body for details.",
            }
        )
    return cards


def derive_evidence(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for index, section in enumerate(sections[:4], start=1):
        text = section["body"] or "Structured evidence block"
        evidence.append(
            {
                "kicker": f"Evidence {index}",
                "title": section["title"],
                "body": text[:140],
            }
        )
    return evidence


def infer_theme(document: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested

    text = " ".join(
        [
            document.get("title", ""),
            document.get("subtitle", ""),
            document.get("summary", ""),
            " ".join(section.get("title", "") for section in document.get("sections", [])),
        ]
    ).lower()

    research_markers = ["research", "调研", "analysis", "compare", "benchmark", "report", "study"]
    technical_markers = ["technical", "技术", "architecture", "system", "api", "debug", "infra", "code"]
    summary_markers = ["summary", "总结", "recap", "weekly", "overview", "one-pager", "brief"]
    project_markers = ["project", "roadmap", "milestone", "launch", "delivery", "initiative"]

    if any(marker in text for marker in technical_markers):
        return "technical"
    if any(marker in text for marker in research_markers):
        return "research"
    if any(marker in text for marker in summary_markers):
        return "summary"
    if any(marker in text for marker in project_markers):
        return "project"
    return "summary"


def tone(index: int) -> str:
    return ["accent", "accent-2", "accent-3", "accent-4"][index % 4]


def esc(text: str) -> str:
    return html.escape(sanitize_text(text))


def render_metric_cards(stats: list[dict[str, str]]) -> str:
    cards = []
    for index, stat in enumerate(stats[:4]):
        metric_value = sanitize_text(stat["value"])
        metric_class = "metric-value"
        if len(metric_value) >= 6:
            metric_class += " compact"
        cards.append(
            f"""
            <article class="metric-card">
                <div class="metric-index">{index + 1:02d}</div>
                <div class="{metric_class} tone-{index % 4}">{esc(metric_value)}</div>
                <div class="metric-label">{esc(stat['label'])}</div>
                <div class="metric-note">{esc(stat.get('note', ''))}</div>
            </article>
            """
        )
    return "\n".join(cards)


def render_summary_cards(document: dict[str, Any]) -> str:
    sections = document["sections"][:4]
    cards: list[str] = []
    for index, section in enumerate(sections):
        cards.append(
            f"""
            <article class="summary-card">
                <div class="summary-label">Block {index + 1:02d}</div>
                <div class="summary-title tone-{index % 4}">{esc(section['title'])}</div>
                <div class="summary-text">{esc(section['body'] or 'See the detailed section below.')}</div>
            </article>
            """
        )
    if cards:
        return "\n".join(cards)
    return f"""
        <article class="summary-card">
            <div class="summary-label">Summary</div>
            <div class="summary-title">{esc(document['title'])}</div>
            <div class="summary-text">{esc(document['summary'] or 'No structured sections were parsed from the source.')}</div>
        </article>
    """


def render_section_cards(document: dict[str, Any], heading: str) -> str:
    cards: list[str] = []
    for index, section in enumerate(document["sections"][:4]):
        bullets = "".join(f"<li>{esc(item)}</li>" for item in section["bullets"][:3])
        paragraphs = "".join(f"<p>{esc(item)}</p>" for item in section["paragraphs"][:2])
        cards.append(
            f"""
            <article class="detail-card">
                <div class="detail-kicker">{heading} {index + 1:02d}</div>
                <div class="detail-title tone-{index % 4}">{esc(section['title'])}</div>
                <div class="detail-body">{esc(section['body'])}</div>
                {f'<ul class="detail-list">{bullets}</ul>' if bullets else ''}
                {f'<div class="detail-extra">{paragraphs}</div>' if paragraphs else ''}
            </article>
            """
        )
    return "\n".join(cards)


def render_info_cards(cards: list[dict[str, str]], card_class: str) -> str:
    rendered = []
    for index, card in enumerate(cards[:4]):
        rendered.append(
            f"""
            <article class="{card_class}">
                <div class="card-kicker">{esc(card['kicker'])}</div>
                <div class="card-headline tone-{index % 4}">{esc(card['title'])}</div>
                <div class="card-copy">{esc(card['body'])}</div>
            </article>
            """
        )
    return "\n".join(rendered)


def render_optional_section(heading: str, content: str) -> str:
    if not content.strip():
        return ""
    return f"""
        <section>
            <div class="section-heading">{heading}</div>
            {content}
        </section>
    """


def render_theme(document: dict[str, Any], theme: str, width: int) -> str:
    style = THEME_STYLES[theme]
    detail_heading = {
        "research": "Finding",
        "technical": "System",
        "summary": "Point",
        "project": "Track",
    }[theme]
    hero_badges = "".join(f"<span class='hero-tag'>{esc(tag)}</span>" for tag in document["tags"][:4])

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{esc(document['title'])}</title>
    <style>
        :root {{
            --bg-top: {style['bg_top']};
            --bg-bottom: {style['bg_bottom']};
            --paper-top: {style['paper_top']};
            --paper-bottom: {style['paper_bottom']};
            --ink: {style['ink']};
            --muted: {style['muted']};
            --line: {style['line']};
            --accent: {style['accent']};
            --accent-2: {style['accent_2']};
            --accent-3: {style['accent_3']};
            --accent-4: {style['accent_4']};
            --hero-glow: {style['hero_glow']};
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
            background:
                radial-gradient(circle at top left, var(--hero-glow), transparent 28%),
                linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
            color: var(--ink);
            padding: 22px 0 34px;
            line-height: 1.6;
        }}
        .poster {{
            width: {width}px;
            margin: 0 auto;
            padding: 0 14px;
        }}
        .paper {{
            position: relative;
            background: linear-gradient(180deg, var(--paper-top), var(--paper-bottom));
            border: 1px solid var(--line);
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(79, 63, 40, 0.10);
            overflow: hidden;
        }}
        .paper::after {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                linear-gradient(180deg, rgba(255,255,255,0.34), transparent 20%),
                radial-gradient(circle at top right, rgba(255,255,255,0.22), transparent 20%);
            pointer-events: none;
        }}
        .hero {{
            padding: 22px 20px 16px;
            margin-bottom: 14px;
        }}
        .hero-tags {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }}
        .hero-tag {{
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            color: var(--muted);
            background: rgba(255,255,255,0.74);
            border: 1px solid var(--line);
        }}
        h1 {{
            font-size: 44px;
            line-height: 1.06;
            letter-spacing: -0.05em;
            margin-bottom: 8px;
        }}
        .hero-subtitle {{
            font-size: 14px;
            color: var(--muted);
            margin-bottom: 10px;
        }}
        .hero-summary {{
            font-size: 13px;
            color: var(--ink);
            opacity: 0.84;
            line-height: 1.75;
            margin-bottom: 12px;
        }}
        .meta-row {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 14px;
        }}
        .meta-pill {{
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 11px;
            color: var(--muted);
            background: rgba(255,255,255,0.68);
            border: 1px solid var(--line);
        }}
        .summary-grid,
        .metrics-grid,
        .detail-grid,
        .insight-grid,
        .decision-grid {{
            display: grid;
            gap: 10px;
            margin-bottom: 14px;
        }}
        .summary-grid, .metrics-grid {{
            grid-template-columns: repeat(4, 1fr);
        }}
        .detail-grid, .insight-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .decision-grid {{
            grid-template-columns: repeat(2, 1fr);
        }}
        .summary-card,
        .metric-card,
        .detail-card,
        .insight-card,
        .decision-card {{
            position: relative;
            background: rgba(255,255,255,0.74);
            border: 1px solid var(--line);
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(97, 77, 46, 0.06);
            overflow: hidden;
        }}
        .summary-card, .metric-card {{
            padding: 13px 12px 14px;
            min-height: 102px;
        }}
        .detail-card, .insight-card, .decision-card {{
            padding: 14px 14px 16px;
        }}
        .summary-card::after, .insight-card::after, .decision-card::after {{
            content: "";
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent), var(--accent-2));
            opacity: 0.9;
        }}
        .summary-label, .detail-kicker, .card-kicker, .metric-index {{
            font-size: 10px;
            color: var(--muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 8px;
        }}
        .summary-title, .detail-title, .card-headline, .metric-label {{
            font-weight: 850;
            line-height: 1.3;
            margin-bottom: 8px;
        }}
        .summary-title {{ font-size: 13px; }}
        .metric-value {{
            font-size: 36px;
            font-weight: 900;
            line-height: 0.98;
            letter-spacing: -0.045em;
            margin-bottom: 6px;
            overflow-wrap: anywhere;
            word-break: break-word;
        }}
        .metric-value.compact {{
            font-size: 24px;
            line-height: 1.02;
            letter-spacing: -0.035em;
        }}
        .metric-label {{ font-size: 13px; }}
        .summary-text, .metric-note, .detail-body, .card-copy, .detail-extra {{
            font-size: 11px;
            color: var(--muted);
            line-height: 1.7;
        }}
        .detail-title, .card-headline {{ font-size: 16px; }}
        .detail-body, .card-copy {{ font-size: 12px; color: rgba(0,0,0,0.68); }}
        .detail-list {{
            margin-top: 10px;
            padding-left: 16px;
            font-size: 11px;
            color: var(--muted);
            line-height: 1.7;
        }}
        .detail-extra p {{
            margin-top: 8px;
        }}
        .section-heading {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 22px;
            font-weight: 850;
            letter-spacing: -0.03em;
            margin: 0 0 10px;
        }}
        .section-heading::after {{
            content: "";
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, var(--accent), transparent);
            opacity: 0.45;
        }}
        .tone-0 {{ color: var(--accent); }}
        .tone-1 {{ color: var(--accent-2); }}
        .tone-2 {{ color: var(--accent-3); }}
        .tone-3 {{ color: var(--accent-4); }}
        .footer {{
            margin-top: 2px;
            padding: 8px 4px 0;
            font-size: 10px;
            color: var(--muted);
            letter-spacing: 0.04em;
            line-height: 1.8;
        }}
        .footer-rule {{
            height: 1px;
            margin-bottom: 8px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            opacity: 0.35;
        }}
        code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            background: rgba(255,255,255,0.62);
            padding: 1px 5px;
            border-radius: 5px;
            color: var(--accent);
        }}
    </style>
</head>
<body>
    <div class="poster">
        <section class="paper hero">
            <div class="hero-tags">{hero_badges}</div>
            <h1>{esc(document['title'])}</h1>
            <div class="hero-subtitle">{esc(document['subtitle'])}</div>
            <div class="hero-summary">{esc(document['summary'])}</div>
            <div class="meta-row">
                <span class="meta-pill">Theme: {theme}</span>
                <span class="meta-pill">Source: {esc(document['source_type'])}</span>
                <span class="meta-pill">Date: {esc(document['date'])}</span>
                <span class="meta-pill">Sections: {len(document['sections'])}</span>
            </div>
            <div class="summary-grid">{render_summary_cards(document)}</div>
        </section>

        {render_optional_section("Key Metrics", f"<div class='metrics-grid'>{render_metric_cards(document['stats'])}</div>")}
        {render_optional_section("Detailed Sections", f"<div class='detail-grid'>{render_section_cards(document, detail_heading)}</div>")}
        {render_optional_section("Evidence / Highlights", f"<div class='insight-grid'>{render_info_cards(document['evidence'], 'insight-card')}</div>")}
        {render_optional_section("Decisions / Next Moves", f"<div class='decision-grid'>{render_info_cards(document['decisions'], 'decision-card')}</div>")}

        <div class="footer">
            <div class="footer-rule"></div>
            {esc(document['footer'])}
        </div>
    </div>
</body>
</html>
"""


def apply_overrides(document: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if args.title:
        document["title"] = args.title
    if args.subtitle:
        document["subtitle"] = args.subtitle
    return document


def default_output_path(input_value: str) -> Path:
    output_dir = Path.home() / "output" / "posters"
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(input_value).stem if Path(input_value).suffix else "poster"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{stem}-{stamp}.png"


def write_html(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_html(document: dict[str, Any], args: argparse.Namespace) -> tuple[str, str]:
    theme = infer_theme(document, args.theme)
    html_content = render_theme(document, theme, args.width)
    return html_content, theme


def capture_html(html_path: Path, output_path: Path, width: int) -> None:
    script_dir = Path(__file__).parent
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "node",
            str(script_dir / "capture.js"),
            str(html_path),
            str(output_path),
            str(width),
        ],
        check=True,
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    document = parse_input(args.input)
    document = apply_overrides(document, args)

    output_path = Path(args.output).expanduser() if args.output else default_output_path(args.input)

    if document.get("type") == "html":
        html_path = Path(args.html_output).expanduser() if args.html_output else output_path.with_suffix(".html")
        write_html(html_path, document["html"])
        capture_html(html_path, output_path, args.width)
        print(f"✅ Poster generated: {output_path}")
        return 0

    html_content, theme = render_html(document, args)
    html_path = Path(args.html_output).expanduser() if args.html_output else output_path.with_suffix(".html")
    write_html(html_path, html_content)
    capture_html(html_path, output_path, args.width)
    print(f"✅ Theme used: {theme}")
    print(f"✅ Poster generated: {output_path}")
    print(f"📄 HTML saved: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
