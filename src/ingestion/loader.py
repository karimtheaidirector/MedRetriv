from pathlib import Path
from pypdf import PdfReader

try:
    import pdfplumber

    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def _is_garbled(text):
    """
    Detect garbled pdfplumber output where words are
    merged without spaces (e.g. 'ScreeningforBreastCancer').
    Returns True when average word length in a sample
    exceeds 15 characters.
    """
    words = text.split()
    if len(words) < 10:
        return False
    sample = words[:50]
    avg = sum(len(w) for w in sample) / len(sample)
    return avg > 15



def load_documents(data_dir="data/raw"):
    """
    Load PDF documents with per-page text extraction.
    Uses pdfplumber for pages containing tables,
    pypdf for text-only pages.

    Returns list of {source, pages: [{page_number, text}]}.
    """
    documents = []

    for file_path in Path(data_dir).glob("*.pdf"):
        pages = _extract_pages(file_path)

        documents.append(
            {
                "source": file_path.name,
                "pages": pages,
            }
        )

    return documents


def _extract_pages(file_path):
    """
    Extract text from each page of a PDF.

    Hybrid approach: pdfplumber for pages that contain
    tables, pypdf for text-only pages.
    """
    pypdf_reader = PdfReader(file_path)
    pages = []

    plumber_pdf = None
    if HAS_PDFPLUMBER:
        plumber_pdf = pdfplumber.open(file_path)

    try:
        for page_idx in range(len(pypdf_reader.pages)):
            page_number = page_idx + 1
            text = ""

            if plumber_pdf:
                plumber_page = plumber_pdf.pages[page_idx]
                tables = plumber_page.extract_tables()

                if tables:
                    text = plumber_page.extract_text() or ""
                    # Fall back to pypdf when pdfplumber
                    # merges words (garbled text)
                    if _is_garbled(text):
                        text = (
                            pypdf_reader.pages[page_idx]
                            .extract_text()
                            or ""
                        )
                else:
                    text = (
                        pypdf_reader.pages[page_idx]
                        .extract_text()
                        or ""
                    )
            else:
                text = (
                    pypdf_reader.pages[page_idx]
                    .extract_text()
                    or ""
                )

            if text.strip():
                pages.append(
                    {
                        "page_number": page_number,
                        "text": text,
                    }
                )
    finally:
        if plumber_pdf:
            plumber_pdf.close()

    return pages