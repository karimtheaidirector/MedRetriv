import re
from typing import Dict, List, Optional


def clean_text(text: str) -> str:
    """
    Basic text cleaning — normalize whitespace,
    collapse blank lines, fix PDF hyphenation.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove repeated whitespace while preserving line structure
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix common PDF hyphenation:
    # "mammo-\ngraphy" -> "mammography"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    return text.strip()


def clean_pages(
    pages: List[Dict],
    header_patterns: Optional[List[str]] = None,
    footer_patterns: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Clean each page's text and strip running headers/footers.

    Applies basic text cleaning first, then removes lines
    at the top/bottom of each page that match the given
    regex patterns.
    """
    cleaned = []

    for page in pages:
        text = clean_text(page["text"])
        lines = text.split("\n")

        # Remove leading blank lines
        while lines and not lines[0].strip():
            lines = lines[1:]

        # Strip running header lines from top of page
        if header_patterns and lines:
            while lines:
                matched = False
                for pattern in header_patterns:
                    if re.search(pattern, lines[0]):
                        lines = lines[1:]
                        matched = True
                        break
                if not matched:
                    break

        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines = lines[:-1]

        # Strip running footer lines from bottom of page
        if footer_patterns and lines:
            while lines:
                matched = False
                for pattern in footer_patterns:
                    if re.search(pattern, lines[-1]):
                        lines = lines[:-1]
                        matched = True
                        break
                if not matched:
                    break

        text = "\n".join(lines).strip()

        if text:
            cleaned.append(
                {
                    "page_number": page["page_number"],
                    "text": text,
                }
            )

    return cleaned