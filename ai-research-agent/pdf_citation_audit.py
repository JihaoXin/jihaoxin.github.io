"""End-to-end Chain-of-Evidence citation audit for PDF research reports.

Pipeline: extract per-page text with ``pypdf`` -> locate the References /
Bibliography / 参考文献 section heuristically -> re-assemble the numbered
``[n]`` entries (which usually span multiple extracted lines) -> build
:class:`citation_checker.Citation` objects with the shared reference-entry
parser -> run :meth:`citation_checker.CitationChecker.verify_report` -> print
the same aligned audit table as the Markdown/BibTeX CLI.

``pypdf`` is the only third-party dependency and is imported lazily: when it
is missing, the tool prints a clear installation hint and exits with code 3,
but the module itself stays importable so tests can inject mocks.

Exit codes: 0 all ACCEPT, 1 some HUMAN_REVIEW, 2 some REJECT (or usage /
empty-bibliography error), 3 missing pypdf dependency.
"""

from __future__ import annotations

import re
import sys
from typing import Optional

from citation_checker import (
    Citation,
    CitationChecker,
    EmptyBibliographyError,
    ReportAudit,
    audit_exit_code,
    format_audit_table,
    parse_reference_entry,
)

try:
    import pypdf
except ImportError:  # pragma: no cover - depends on the environment
    pypdf = None

# Maximum characters the LAST numbered entry may span; PDF text after the
# bibliography (appendices, page footers) would otherwise be swallowed.
_MAX_TAIL_ENTRY_CHARS = 600

_REFERENCES_HEADING_RE = re.compile(
    r"(?:^|\n)[^\S\n]*(?:(?:\d+|[ivxlc]+)[.\s]{0,3})?"
    r"(?:r\s*eferences|bibliography|参考文献)[^\S\n]*(?=\n|\[)",
    re.I,
)


def _require_pypdf() -> None:
    """Exit with code 3 and a clear hint when pypdf is not installed."""
    if pypdf is None:
        print(
            "error: this tool requires the 'pypdf' package to read PDF files.\n"
            "install it with:  pip install pypdf",
            file=sys.stderr,
        )
        sys.exit(3)


def extract_pdf_text(path: str) -> str:
    """Extract and concatenate the text of every page of a PDF file."""
    _require_pypdf()
    reader = pypdf.PdfReader(path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def find_references_section(text: str) -> str:
    """Heuristically locate the bibliography section of extracted PDF text.

    Matches the LAST standalone ``References`` / ``Bibliography`` /
    ``参考文献`` heading (optionally prefixed by a section number, tolerant of
    the spaced small-caps artefact ``R EFERENCES``) and returns everything
    after it. Returns an empty string when no heading is found.
    """
    last = None
    for match in _REFERENCES_HEADING_RE.finditer(text):
        last = match
    return text[last.end() :] if last is not None else ""


def split_numbered_entries(section: str) -> list[tuple[int, str]]:
    """Split a bibliography section into (number, entry_text) pairs.

    Repairs hyphenation across line breaks, then keeps the ``[n]`` markers
    that form a sequential run starting at ``[1]`` (this filters out inline
    cross-citations and page numbers) and treats the text between consecutive
    markers as one entry, with whitespace collapsed. The final entry is
    truncated defensively so trailing appendix text is not swallowed.
    """
    section = re.sub(r"-\s*\n\s*", "", section)  # de-hyphenate wrapped words
    expected = 1
    markers: list[re.Match[str]] = []
    for match in re.finditer(r"\[\s*(\d{1,4})\s*\]", section):
        if int(match.group(1)) == expected:
            markers.append(match)
            expected += 1
    entries: list[tuple[int, str]] = []
    for i, match in enumerate(markers):
        if i + 1 < len(markers):
            end = markers[i + 1].start()
        else:
            end = min(len(section), match.end() + _MAX_TAIL_ENTRY_CHARS)
        entry_text = re.sub(r"\s+", " ", section[match.end() : end]).strip()
        if entry_text:
            entries.append((int(match.group(1)), entry_text))
    return entries


def extract_citations_from_pdf(path: str) -> list[Citation]:
    """Extract the numbered bibliography of a PDF as Citation objects.

    Reuses :func:`citation_checker.parse_reference_entry` so PDF and Markdown
    inputs share one parsing behaviour. Claims are not attached: reliably
    aligning body sentences with ``[n]`` markers in reflowed PDF text is out
    of scope for this heuristic extractor.
    """
    text = extract_pdf_text(path)
    section = find_references_section(text)
    return [
        parse_reference_entry(number, entry)
        for number, entry in split_numbered_entries(section)
    ]


def audit_pdf(path: str, checker: Optional[CitationChecker] = None) -> ReportAudit:
    """Run the end-to-end Chain-of-Evidence audit on a PDF report.

    Args:
        path: Path to the PDF file.
        checker: Optional pre-configured :class:`CitationChecker`; tests can
            inject one with mocked fetchers. Defaults to a live checker
            querying CrossRef/OpenAlex.

    Returns:
        The aggregated :class:`ReportAudit`.

    Raises:
        EmptyBibliographyError: when no references could be extracted --
            either the PDF has no recognizable bibliography or every entry
            failed to parse; both must block publication.
    """
    checker = checker or CitationChecker()
    return checker.verify_report(extract_citations_from_pdf(path))


def main(argv: list[str]) -> int:
    """CLI entry point: ``python pdf_citation_audit.py <report.pdf>``."""
    if len(argv) != 2:
        print("usage: python pdf_citation_audit.py <report.pdf>", file=sys.stderr)
        return 2
    _require_pypdf()
    try:
        audit = audit_pdf(argv[1])
    except FileNotFoundError:
        print(f"error: file not found: {argv[1]}", file=sys.stderr)
        return 2
    except EmptyBibliographyError as err:
        print(
            f"error: {err} (no numbered references found in the PDF)",
            file=sys.stderr,
        )
        return 2
    print(format_audit_table(audit))
    return audit_exit_code(audit)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
