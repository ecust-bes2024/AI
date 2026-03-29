# Poster Skill Deployment

## What this skill now is

This directory is a reusable multi-theme poster skill.

Main entrypoints:

- `poster_generator.py` - normalize input, pick theme, generate HTML, render PNG
- `capture.js` - generic Playwright HTML-to-PNG renderer
- `SKILL.md` - trigger and usage instructions for `/poster`

## Supported inputs

- Markdown
- JSON
- YAML
- HTML
- Raw text
- URL (best effort; local content is safer)

## Supported themes

- `auto`
- `research`
- `technical`
- `summary`
- `project`

## Local usage

```bash
python3 poster_generator.py report.md
python3 poster_generator.py report.md --theme technical
python3 poster_generator.py data.json --theme research --output ./report-poster.png
python3 poster_generator.py "Weekly summary: ..."
python3 poster_generator.py existing-poster.html
```

## Install notes

The renderer relies on Node Playwright from this directory's `package.json`.

If dependencies are not installed:

```bash
npm install
```

If the browser binary is missing:

```bash
npx playwright install chromium
```

## Skill behavior

When the user asks for `/poster ...` or wants a visual summary / research poster / technical poster / project poster:

1. Convert content into a local file if needed.
2. Run `poster_generator.py`.
3. Return the PNG path and show the image if useful.

## Outputs

The generator writes:

- a PNG poster
- a sibling HTML file used for rendering

Default PNG output path:

```bash
~/output/posters/
```
