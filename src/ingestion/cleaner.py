import re
from typing import Dict, List, Optional


# ============================================================
# Universal & Document-Specific Running Header/Footer Patterns
# ============================================================

RUNNING_HEADER_FOOTER_PATTERNS = [
    # --- USPSTF / JAMA Recommendation Statement ---
    r"(?i)\b\d{1,4}\s*JAMA\s*[A-Za-z]+\s*\d{1,2},?\s*\d{4}\s*Volume\s*\d+,?\s*Number\s*\d+\s*(\(Reprinted\))?\s*jama\.com\b",
    r"(?i)\bjama\.com\s*(\(Reprinted\))?\s*JAMA\s*[A-Za-z]+\s*\d{1,2},?\s*\d{4}\s*Volume\s*\d+,?\s*Number\s*\d+\s*\d{1,4}\b",
    r"(?i)\bjama\.com\s*(\(Reprinted\))?.*",
    r"(?i)\b\d{1,4}\s*JAMA\s*[A-Za-z]+\s+\d{1,2}.*jama\.com\b",
    r"(?i)JAMA\s*\|\s*US\s*Preventive\s*Services\s*Task\s*Force\s*\|\s*RECOMMENDATION\s*STATEMENT",
    r"(?i)USPSTF\s*Recommendation:\s*Screening\s*for\s*Breast\s*Cancer\s+US\s*Preventive\s*Services\s*Task\s*Force\s+Clinical\s*Review\s*&\s*Education",
    r"(?i)Clinical\s*Review\s*&\s*Education\s+US\s*Preventive\s*Services\s*Task\s*Force\s+USPSTF\s*Recommendation:\s*Screening\s*for\s*Breast\s*Cancer",
    r"(?i)USPSTF\s*Recommendation:\s*Screening\s*for\s*Breast\s*Cancer\s+Clinical\s*Review\s*&\s*Education",
    r"(?i)Clinical\s*Review\s*&\s*Education\s+USPSTF\s*Recommendation:\s*Screening\s*for\s*Breast\s*Cancer",
    r"(?i)USPSTF\s*Recommendation:\s*Screening\s*for\s*Breast\s*Cancer\b.*",
    r"(?i)[©]?\s*\d{4}\s*American\s*Medical\s*Association\.\s*All\s*rights\s*reserved.*",
    r"(?i)\bJAMA\.\s*\d{4};\s*\d+\(\d+\):\s*\d+-\d+\.\s*doi:10\.1001/jama\.\d+\.\d+",
    r"(?i)\bCME\s+at\s+jamacmelookup\.com\b",
    r"(?i)\bjamanetworkopen\.com\b",
    r"(?i)\bjamaoncology\.com\b",

    # --- AHRQ Systematic Evidence Review ---
    r"(?i)Breast\s*Cancer\s*Screening\s*[ivxldcm\d]*\s*Kaiser\s*Permanente\s*(Research\s*Affiliates\s*)?EPC",
    r"(?i)Kaiser\s*Permanente\s*(Research\s*Affiliates\s*)?EPC\s*[ivxldcm\d]*\s*Breast\s*Cancer\s*Screening",
    r"(?i)Breast\s*Cancer\s*Screening\s*Kaiser\s*Permanente\s*(Research\s*Affiliates\s*)?EPC\s*[ivxldcm\d]*",
    r"(?i)Kaiser\s*Permanente\s*(Research\s*Affiliates\s*)?EPC\s*[ivxldcm\d]*",

    # --- Frontiers in Oncology Review ---
    r"(?i)Frontiers\s+in\s+Oncology\s+frontiersin\.org\s*\d*",
    r"(?i)frontiersin\.org\s*\d*",
    r"(?i)Pasi\s+et\s+al\.\s+10\.3389/fonc\.\d+\.\d+",
    r"(?i)^\s*(OPEN ACCESS|EDITED BY|REVIEWED BY|TYPE (Review|Original Research))\b.*",
    r"(?i)DOI\s+10\.3389/fonc\.\d+\.\d+",

    # --- Nature STTT Review ---
    r"(?i)Breast\s+cancer:\s*pathogenesis\s+and\s+treatments\s+Xiong\s+et\s+al\.\s*\d*",
    r"(?i)Signal\s+Transduction\s+and\s+Targeted\s+Therapy\s*\(\d{4}\)\s*\d+:\d+",
    r"(?i)www\.nature\.com/sigtrans",
    r"(?i)SPRINGER\s+NATURE\s*",
    r"(?i)Citation:\s*Signal\s+Transduction\s+and\s+Targeted\s+Therapy\s*\(\d{4}\)\s*\d+:\d+",

    # --- NCI / NIH Patient & Professional Overview ---
    r"(?i)Page\s+\d{1,3}\s+of\s+\d{1,3}",
    r"(?i)National\s+Cancer\s+Institute\s*\|\s*cancer\.gov",
    r"(?i)National\s+Cancer\s+Institute\s*-\s*Breast\s+Cancer\s+Overview",
]


def strip_running_headers_footers(
    text: str,
    extra_patterns: Optional[List[str]] = None,
) -> str:
    """
    Remove all known running header and footer patterns from text,
    stripping matching lines and inline fragments.
    """
    patterns = list(RUNNING_HEADER_FOOTER_PATTERNS)
    if extra_patterns:
        patterns.extend(extra_patterns)

    lines = text.split("\n")
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue

        line_matches = False
        for pattern in patterns:
            if re.search(pattern, stripped):
                subbed = re.sub(pattern, "", stripped).strip()
                if not subbed or len(subbed) < 4:
                    line_matches = True
                    break
                else:
                    stripped = subbed

        if not line_matches and stripped:
            cleaned_lines.append(stripped)

    result = "\n".join(cleaned_lines)

    # Inline sweep for any remaining pattern fragments
    for pattern in patterns:
        result = re.sub(pattern, "", result)

    return result


def clean_text(text: str) -> str:
    """
    Basic text cleaning — normalize whitespace,
    collapse blank lines, fix PDF hyphenation.
    """
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Strip running headers/footers
    text = strip_running_headers_footers(text)

    # Remove repeated whitespace while preserving line structure
    text = re.sub(r"[ \t]+", " ", text)

    # Remove spaces around newlines
    text = re.sub(r" *\n *", "\n", text)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Fix intra-page PDF hyphenation ("mammo-\ngraphy" -> "mammography")
    text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

    return text.strip()


def clean_pages(
    pages: List[Dict],
    header_patterns: Optional[List[str]] = None,
    footer_patterns: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Clean each page's text, strip running headers/footers, and heal
    hyphenated words that span across page boundaries.
    """
    all_extra_patterns = []
    if header_patterns:
        all_extra_patterns.extend(header_patterns)
    if footer_patterns:
        all_extra_patterns.extend(footer_patterns)

    cleaned = []

    for page in pages:
        raw_text = page["text"]
        # Strip running headers/footers
        text = strip_running_headers_footers(raw_text, all_extra_patterns)
        text = clean_text(text)

        lines = text.split("\n")

        # Trim leading and trailing blank lines
        while lines and not lines[0].strip():
            lines = lines[1:]
        while lines and not lines[-1].strip():
            lines = lines[:-1]

        final_text = "\n".join(lines).strip()
        if final_text:
            cleaned.append(
                {
                    "page_number": page["page_number"],
                    "text": final_text,
                }
            )

    # Cross-page hyphenation recovery between page N and page N+1
    for i in range(len(cleaned) - 1):
        curr_text = cleaned[i]["text"]
        next_text = cleaned[i + 1]["text"]

        match_end = re.search(r"(\b\w+)-$", curr_text)
        match_start = re.match(r"^([a-z]\w*)\b", next_text)

        if match_end and match_start:
            word_p1 = match_end.group(1)
            word_p2 = match_start.group(1)
            merged = word_p1 + word_p2

            cleaned[i]["text"] = curr_text[: match_end.start()] + merged
            cleaned[i + 1]["text"] = next_text[match_start.end() :].lstrip()

    return cleaned