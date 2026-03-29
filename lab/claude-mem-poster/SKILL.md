---
name: poster-dev
description: Development source for the poster skill. Use this only when maintaining or testing the poster skill implementation itself, not for normal /poster usage.
---

# Poster Skill Source

Generate PNG poster outputs from content the user already has, or from structured notes you prepare first.

## Trigger

Use this skill when the user wants any of the following:

- `/poster ...`
- A visual summary / infographic / poster from existing content
- A research report poster
- A technical report poster
- A project update poster
- A one-page summary from markdown, JSON/YAML, HTML, URL content, or raw text

## Input Types

The generator supports these inputs:

1. Markdown files
2. JSON / YAML structured documents
3. HTML files
4. Raw text passed as one quoted argument
5. URLs

If the user gives you a URL and live fetching is unreliable, browse first, save the useful content as markdown or JSON, then call the generator on that local file.

If the user gives content directly in chat instead of a file:

1. Save the content into a temporary markdown or JSON file.
2. Run the generator on that temp file.

## Themes

The CLI supports:

- `auto`
- `research`
- `technical`
- `summary`
- `project`

Default to `auto` unless the user explicitly asks for a specific style.

Theme selection guidance:

- `research`: comparisons, evaluations, landscape scans, tool analysis, benchmark writeups
- `technical`: architecture notes, API/system reports, engineering investigations, debugging summaries
- `summary`: one-page recap, executive summary, weekly digest, concise status overview
- `project`: roadmap, launch update, milestone report, initiative overview

## Run

Primary command:

```bash
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py <input> [--theme <theme>] [--output <path>] [--title <title>] [--subtitle <subtitle>]
```

Examples:

```bash
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py report.md
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py report.md --theme technical
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py data.json --theme research --output /tmp/report-poster.png
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py "Project launch summary: ..."
python3 /Users/jerry_hu/AI/claude-mem-poster/poster_generator.py poster.html
```

The generator writes:

- a PNG poster
- a sibling HTML file used for rendering

If `--output` is omitted, it writes to `~/output/posters/`.

## Workflow

1. Decide whether the user input is already usable as markdown / JSON / YAML / HTML / raw text.
2. If needed, convert chat content or scraped content into a local markdown or JSON file first.
3. Pick `--theme` or leave it at `auto`.
4. Run the generator.
5. Return the PNG path and show the image when helpful.

## Notes

- HTML input is passed through and rendered directly.
- YAML support requires `PyYAML`; markdown, JSON, HTML, and raw text do not.
- Rendering uses the bundled Playwright screenshot script.
- The current generator is strongest on long-form editorial posters, not tiny social-media cards.
