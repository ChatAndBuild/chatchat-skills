---
id: book-translation
category: Content & Media
author: f
name: Book Translation
description: Use this skill when translating a book, chapter, or long-form document into another language while preserving structure, formatting, terminology consistency, and document continuity.
---

# Book Translation

Use this skill when the user wants to translate a book, chapter, or other long-form document into another language.

## Before you translate (collect constraints)

Ask for (or infer from context) the minimum required details:
- Target language and locale (e.g. `fr-FR` vs `fr-CA`)
- Audience and reading level (general, academic, YA, technical)
- Tone and style (literal, literary, businesslike)
- Scope (entire book vs specific chapters/sections)
- Output format (Markdown, plain text, bilingual, chapter-per-file)
- Terminology preferences (terms to keep in the source language, preferred translations)
- Whether to translate code blocks / inline code (default: do not translate code)

## Workflow

### 1) Ingest the source

- If the user provides **a PDF**:
  - Determine whether the PDF has extractable text or needs OCR (scanned images).
  - Extract the text in reading order.
  - Remove repeated headers/footers where possible.
  - Keep page numbers or section markers so the translation can be traced back to the source.

- If the user provides **text** (or Markdown):
  - Preserve structure (headings, lists, numbering, quotes).
  - Preserve markup (Markdown syntax, links, emphasis).

### 2) Build a translation glossary

Create a short glossary of:
- Proper nouns (people, places, organizations)
- Technical terms
- Recurring phrases

If there are ambiguous terms, present 2–3 options and recommend one for consistency.

### 3) Translate in chunks

Translate section-by-section to maintain coherence and avoid drift:
- Preserve headings and numbering
- Preserve citations, footnotes markers, and references
- Keep code blocks and inline code unchanged unless explicitly asked

### 4) Quality pass

Run a consistency pass:
- Terminology consistency (glossary adherence)
- Names and capitalization
- Locale-appropriate punctuation/typography
- Flag unclear/ambiguous sentences and provide alternatives

### 5) Deliverables

Provide:
- The translated text (in the requested output format)
- A short “translation notes” section including glossary decisions and any open questions

## Output defaults

- Default output is **Markdown** (if structure is present).
- If the user wants a bilingual version, output “Original” and “Translation” per section.
