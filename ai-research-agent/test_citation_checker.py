"""Offline unit tests for the Chain-of-Evidence citation verifier.

These tests answer interview question #6: how do we PROVE that every citation
in the generated report exists, that the claim-evidence support check runs,
and that the HIGH/ACCEPT - MEDIUM/HUMAN_REVIEW - LOW/REJECT confidence router
behaves -- including its fail-safe behaviour under backend outages.

No real network traffic is ever generated:

* every ``CitationChecker`` instance is built with injected fake
  ``fetch_json`` / ``fetch_text`` callables (the module's designed test seam);
* the PDF end-to-end smoke test injects a fully mocked checker;
* as a belt-and-braces guard, ``urllib.request.urlopen`` is patched in every
  test to raise immediately, so an accidental real HTTP call fails loudly
  (``AssertionError`` is deliberately not part of the retry-caught exception
  set in ``CitationChecker._http_get``).

Run from this directory with:

    python3 -m unittest test_citation_checker -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
import urllib.parse
from unittest import mock

import pdf_citation_audit
from citation_checker import (
    Action,
    Citation,
    CitationChecker,
    Confidence,
    EmptyBibliographyError,
    LookupBackendError,
    NotFoundError,
    ReportAudit,
    Verification,
    extract_from_markdown,
    parse_bibtex,
    route_verification,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

TITLE = "Attention Is All You Need"
DOI = "10.5555/3295222.3295349"
YEAR = 2017
AUTHORS = ["Ashish Vaswani", "Noam Shazeer"]
CLAIM = "The Transformer architecture relies entirely on attention mechanisms."

# Lexically covers CLAIM -> default_support_judge score ~0.89 (>= 0.45).
SUPPORTING_ABSTRACT = (
    "We propose the Transformer, a network architecture based entirely on "
    "attention mechanisms, dispensing with recurrence and convolutions."
)
# Zero token overlap with CLAIM -> support score 0.0 (< 0.45).
UNRELATED_ABSTRACT = (
    "Quantum key distribution over metropolitan fiber links achieves record "
    "secret bit rates."
)
# High topical overlap with CLAIM but a negation flip -> the default judge
# must flag a CONTRADICTION, and the router must REJECT the citation.
CONTRADICTING_ABSTRACT = (
    "We show the Transformer architecture does not rely entirely on "
    "attention mechanisms; recurrence remains essential in practice."
)

# What the official CrossRef BibTeX transform endpoint would return; tests
# assert this exact string is what ends up in Verification.bibtex, proving
# the record came from provenance (fetch_text) and not from generation.
OFFICIAL_BIBTEX = (
    "@inproceedings{Vaswani_2017,\n"
    "  title={Attention Is All You Need},\n"
    f"  doi={{{DOI}}},\n"
    "  year={2017}\n"
    "}\n"
)


def crossref_item(
    title: str = TITLE,
    year: int = YEAR,
    family: str = "Vaswani",
    doi: str = DOI,
    abstract: str | None = None,
) -> dict:
    """Build one CrossRef work record in the real API shape."""
    item = {
        "title": [title],
        "issued": {"date-parts": [[year]]},
        "author": [{"family": family, "given": "A."}],
        "DOI": doi,
    }
    if abstract is not None:
        item["abstract"] = f"<jats:p>{abstract}</jats:p>"
    return item


def crossref_search(*items: dict) -> dict:
    """Wrap work records as a CrossRef ``?query.bibliographic=`` response."""
    return {"message": {"items": list(items)}}


def openalex_search(*records: dict) -> dict:
    """Wrap work records as an OpenAlex ``?search=`` response."""
    return {"results": list(records)}


class FakeFetcher:
    """URL-routing fake for the injected fetch_json / fetch_text seams.

    Routes are (url_substring, payload) pairs; a payload that is an Exception
    instance is raised instead of returned. Any URL that matches no route
    fails the test immediately -- this both prevents real network access and
    catches the checker querying a backend it should not have queried.
    """

    def __init__(self, routes: list[tuple[str, object]]) -> None:
        self.routes = list(routes)
        self.calls: list[str] = []

    def __call__(self, url: str) -> object:
        self.calls.append(url)
        for fragment, outcome in self.routes:
            if fragment in url:
                if isinstance(outcome, Exception):
                    raise outcome
                return outcome
        raise AssertionError(f"unexpected URL requested by checker: {url}")


class NoNetworkTestCase(unittest.TestCase):
    """Base class: any accidental urllib call fails the test loudly."""

    def setUp(self) -> None:
        patcher = mock.patch(
            "urllib.request.urlopen",
            side_effect=AssertionError("real network access attempted in a unit test"),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_checker(
        self,
        json_routes: list[tuple[str, object]],
        text_routes: list[tuple[str, object]] | None = None,
    ) -> tuple[CitationChecker, FakeFetcher, FakeFetcher, mock.Mock]:
        """Build a checker wired to fake fetchers and a mock HITL hook."""
        fetch_json = FakeFetcher(json_routes)
        fetch_text = FakeFetcher(
            text_routes
            if text_routes is not None
            else [("/transform/application/x-bibtex", OFFICIAL_BIBTEX)]
        )
        hitl = mock.Mock(name="on_human_review")
        checker = CitationChecker(
            fetch_json=fetch_json,
            fetch_text=fetch_text,
            on_human_review=hitl,
        )
        return checker, fetch_json, fetch_text, hitl


# ---------------------------------------------------------------------------
# Core verification scenarios (interview question #6, scenarios 1-3)
# ---------------------------------------------------------------------------


class VerifyOneScenarioTests(NoNetworkTestCase):
    """The three canonical outcomes: real+supported, real+unsupported, fake."""

    def test_real_citation_supports_claim(self) -> None:
        """Real paper whose abstract supports the claim -> HIGH / ACCEPT."""
        checker, fetch_json, fetch_text, hitl = self.make_checker(
            [
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(abstract=SUPPORTING_ABSTRACT)),
                )
            ]
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, claim=CLAIM
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)
        self.assertIs(v.confidence, Confidence.HIGH)
        self.assertIs(v.action, Action.ACCEPT)
        self.assertEqual(v.matched_source, "crossref")
        self.assertEqual(v.matched_doi, DOI)
        self.assertGreaterEqual(v.title_similarity, 0.95)
        self.assertIs(v.year_consistent, True)
        self.assertIs(v.author_consistent, True)
        self.assertIs(v.supports_claim, True)
        self.assertGreaterEqual(v.support_score, checker.support_threshold)
        # Provenance-only BibTeX: non-empty, byte-identical to what the fake
        # CrossRef transform endpoint served, fetched exactly once for the
        # matched DOI -- never composed by the checker (or an LLM) itself.
        self.assertTrue(v.bibtex)
        self.assertEqual(v.bibtex, OFFICIAL_BIBTEX)
        self.assertEqual(len(fetch_text.calls), 1)
        self.assertIn("/transform/application/x-bibtex", fetch_text.calls[0])
        self.assertIn(urllib.parse.quote(DOI, safe="/"), fetch_text.calls[0])
        hitl.assert_not_called()
        # The strong CrossRef hit means OpenAlex must not have been queried.
        self.assertTrue(all("openalex" not in url for url in fetch_json.calls))

    def test_real_citation_does_not_support_claim(self) -> None:
        """Real paper, unrelated abstract -> exists but MEDIUM / HUMAN_REVIEW."""
        checker, _fetch_json, _fetch_text, hitl = self.make_checker(
            [
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(abstract=UNRELATED_ABSTRACT)),
                )
            ]
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, claim=CLAIM
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)  # provenance succeeded: the paper is real
        self.assertGreaterEqual(v.title_similarity, 0.95)
        self.assertIs(v.supports_claim, False)
        self.assertLess(v.support_score, checker.support_threshold)
        self.assertIs(v.confidence, Confidence.MEDIUM)
        self.assertIs(v.action, Action.HUMAN_REVIEW)
        self.assertTrue(
            any("support" in reason for reason in v.reasons),
            f"expected a claim-support reason, got: {v.reasons}",
        )
        # The HITL notification hook must fire exactly once, with this verdict.
        hitl.assert_called_once()
        self.assertIs(hitl.call_args[0][0], v)

    def test_nonexistent_citation_rejected(self) -> None:
        """No candidates in CrossRef nor OpenAlex -> LOW / REJECT, no BibTeX."""
        checker, fetch_json, fetch_text, hitl = self.make_checker(
            [
                ("query.bibliographic", crossref_search()),  # CrossRef: empty
                ("api.openalex.org", openalex_search()),  # OpenAlex: empty
            ]
        )
        citation = Citation(
            key="ghost2024",
            title="A Fabricated Paper That Does Not Exist Anywhere",
            year=2024,
        )

        v = checker.verify_one(citation)

        self.assertFalse(v.exists)
        self.assertIs(v.confidence, Confidence.LOW)
        self.assertIs(v.action, Action.REJECT)
        self.assertIsNone(v.bibtex)
        self.assertEqual(fetch_text.calls, [])  # no provenance -> no BibTeX pull
        hitl.assert_not_called()  # REJECT is final; no human review ping
        self.assertTrue(
            any("not found" in reason for reason in v.reasons),
            f"expected a provenance-failure reason, got: {v.reasons}",
        )
        # Both backends were actually consulted before rejecting.
        self.assertTrue(any("crossref" in url for url in fetch_json.calls))
        self.assertTrue(any("openalex" in url for url in fetch_json.calls))


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class VerifyOneEdgeCaseTests(NoNetworkTestCase):
    """Boundary behaviour: empty bibliography, fuzzy band, outages, bad DOIs."""

    def test_empty_bibliography_raises(self) -> None:
        """verify_report([]) must raise: a report never ships without refs."""
        checker, _fetch_json, _fetch_text, _hitl = self.make_checker([])
        with self.assertRaises(EmptyBibliographyError):
            checker.verify_report([])

    def test_ambiguous_fuzzy_match_goes_to_human_review(self) -> None:
        """Title similarity inside [0.80, 0.95) must never auto-ACCEPT."""
        near_title = "Attention Is All You Need Redux"
        # Precondition: the fixture really sits inside the ambiguous band.
        sim = CitationChecker._similarity(TITLE, near_title)
        self.assertTrue(0.80 <= sim < 0.95, f"fixture out of band: {sim}")

        checker, _fetch_json, fetch_text, hitl = self.make_checker(
            [
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(title=near_title)),
                )
            ]
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)  # resolvable, but only fuzzily
        self.assertTrue(0.80 <= v.title_similarity < 0.95)
        self.assertIs(v.confidence, Confidence.MEDIUM)
        self.assertIs(v.action, Action.HUMAN_REVIEW)
        self.assertNotEqual(v.action, Action.ACCEPT)
        self.assertIsNone(v.bibtex)  # weak match earns no provenance BibTeX
        self.assertEqual(fetch_text.calls, [])
        hitl.assert_called_once()
        self.assertTrue(
            any("fuzzy" in reason for reason in v.reasons),
            f"expected a fuzzy-match reason, got: {v.reasons}",
        )

    def test_backend_failure_never_accepts(self) -> None:
        """Total backend outage -> fail-safe HUMAN_REVIEW, never ACCEPT."""
        fetch_json = mock.Mock(
            side_effect=LookupBackendError("simulated CrossRef/OpenAlex outage")
        )
        fetch_text = FakeFetcher([])  # must never be reached
        hitl = mock.Mock(name="on_human_review")
        checker = CitationChecker(
            fetch_json=fetch_json, fetch_text=fetch_text, on_human_review=hitl
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, doi=DOI
        )

        v = checker.verify_one(citation)

        self.assertNotEqual(v.action, Action.ACCEPT)  # the fail-safe invariant
        self.assertIs(v.action, Action.HUMAN_REVIEW)
        self.assertIs(v.confidence, Confidence.MEDIUM)
        self.assertTrue(v.backend_failed)
        self.assertIsNone(v.bibtex)
        self.assertEqual(fetch_text.calls, [])
        self.assertTrue(
            any("backend" in reason.lower() for reason in v.reasons),
            f"expected a backend-outage reason, got: {v.reasons}",
        )
        hitl.assert_called_once()

    def test_contradicting_abstract_rejected(self) -> None:
        """Abstract that negates the claim -> LOW / REJECT, never 'weak support'.

        Regression for code-review finding #2: with the old flat threshold, a
        'X does not improve Y' abstract still cleared the bar for a claim
        'X improves Y' and the citation was auto-accepted.
        """
        checker, _fetch_json, fetch_text, hitl = self.make_checker(
            [
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(abstract=CONTRADICTING_ABSTRACT)),
                )
            ]
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, claim=CLAIM
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)  # the paper itself is real...
        self.assertIs(v.claim_contradicted, True)
        self.assertIs(v.supports_claim, False)
        self.assertIs(v.confidence, Confidence.LOW)  # ...but its use is banned
        self.assertIs(v.action, Action.REJECT)
        self.assertIsNone(v.bibtex)  # a rejected use earns no BibTeX pull
        self.assertEqual(fetch_text.calls, [])
        hitl.assert_not_called()
        self.assertTrue(
            any("contradict" in reason for reason in v.reasons),
            f"expected a contradiction reason, got: {v.reasons}",
        )

    def test_title_only_match_requires_corroboration(self) -> None:
        """A bare-title citation must not auto-ACCEPT on title similarity alone.

        Regression for code-review finding #1: 'not contradicted' is not
        'confirmed' -- with no year, no authors and no DOI to corroborate,
        a perfect title match could still be a different, similarly-titled
        work, so the router must demand human review.
        """
        checker, _fetch_json, fetch_text, hitl = self.make_checker(
            [("query.bibliographic", crossref_search(crossref_item()))]
        )
        citation = Citation(key="titleonly", title=TITLE)  # no year/authors/DOI

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)
        self.assertGreaterEqual(v.title_similarity, 0.95)
        self.assertIsNone(v.year_consistent)  # nothing to corroborate with
        self.assertIsNone(v.author_consistent)
        self.assertIs(v.confidence, Confidence.MEDIUM)
        self.assertIs(v.action, Action.HUMAN_REVIEW)
        self.assertIsNone(v.bibtex)
        self.assertEqual(fetch_text.calls, [])
        hitl.assert_called_once()
        self.assertTrue(
            any("corroborating" in reason for reason in v.reasons),
            f"expected a no-corroboration reason, got: {v.reasons}",
        )

    def test_accept_requires_provenance_bibtex(self) -> None:
        """A strong, supported citation without pulled BibTeX cannot ACCEPT.

        Regression for code-review finding #3: silently accepting with
        bibtex=None invites downstream LLM fabrication of the entry, which
        Chain-of-Evidence principle #1 forbids.
        """
        checker, _fetch_json, _fetch_text, hitl = self.make_checker(
            [
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(abstract=SUPPORTING_ABSTRACT)),
                )
            ],
            text_routes=[
                (
                    "/transform/application/x-bibtex",
                    LookupBackendError("transform endpoint down"),
                )
            ],
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, claim=CLAIM
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)
        self.assertIs(v.supports_claim, True)  # everything else is perfect
        self.assertIsNone(v.bibtex)  # but provenance BibTeX is missing
        self.assertIs(v.confidence, Confidence.MEDIUM)
        self.assertIs(v.action, Action.HUMAN_REVIEW)
        hitl.assert_called_once()
        self.assertTrue(
            any("BibTeX" in reason for reason in v.reasons),
            f"expected a missing-BibTeX reason, got: {v.reasons}",
        )

    def test_invalid_doi_falls_back_to_title_search(self) -> None:
        """DOI 404 is recorded, but a strong title hit still verifies."""
        bad_doi = "10.9999/does-not-resolve"
        checker, fetch_json, _fetch_text, _hitl = self.make_checker(
            [
                (
                    urllib.parse.quote(bad_doi, safe="/"),
                    NotFoundError(f"HTTP 404 for {bad_doi}"),
                ),
                (
                    "query.bibliographic",
                    crossref_search(crossref_item(abstract=SUPPORTING_ABSTRACT)),
                ),
            ]
        )
        citation = Citation(
            key="vaswani2017", title=TITLE, authors=AUTHORS, year=YEAR, doi=bad_doi
        )

        v = checker.verify_one(citation)

        self.assertTrue(v.exists)
        self.assertIs(v.action, Action.ACCEPT)
        self.assertEqual(v.matched_doi, DOI)  # the real DOI from provenance
        self.assertTrue(
            any("invalid DOI" in reason for reason in v.reasons),
            f"expected the invalid-DOI note to be recorded, got: {v.reasons}",
        )
        # The DOI endpoint was tried first, then the title search.
        self.assertIn(urllib.parse.quote(bad_doi, safe="/"), fetch_json.calls[0])
        self.assertTrue(any("query.bibliographic" in url for url in fetch_json.calls))


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


class ParserTests(NoNetworkTestCase):
    """BibTeX and Markdown extraction produce faithful Citation objects."""

    def test_parse_bibtex_roundtrip(self) -> None:
        """Fields survive parsing, and re-parsing ``raw`` is a fixed point."""
        bib = (
            "% stray comment line\n"
            "@comment{this whole block is ignored}\n"
            "@article{vaswani2017attention,\n"
            "  title   = {Attention Is All You {Need}},\n"
            "  author  = {Vaswani, Ashish and Shazeer, Noam},\n"
            "  year    = {2017},\n"
            f"  doi     = {{{DOI}}},\n"
            "  journal = {Advances in Neural Information Processing Systems},\n"
            "}\n"
        )
        citations = parse_bibtex(bib)

        self.assertEqual(len(citations), 1)  # @comment must be skipped
        c = citations[0]
        self.assertEqual(c.key, "vaswani2017attention")
        self.assertEqual(c.title, TITLE)  # nested braces stripped
        self.assertEqual(c.authors, ["Vaswani, Ashish", "Shazeer, Noam"])
        self.assertEqual(c.year, 2017)
        self.assertEqual(c.doi, DOI)
        self.assertEqual(c.venue, "Advances in Neural Information Processing Systems")
        # Roundtrip: parsing the captured raw entry reproduces the citation.
        reparsed = parse_bibtex(c.raw)
        self.assertEqual(reparsed, [c])

    def test_extract_from_markdown(self) -> None:
        """Numbered refs and the claim sentence citing them are extracted."""
        md = (
            "# 研究报告\n"
            "\n"
            "Transformer 完全依赖注意力机制,不使用循环结构 [1]。\n"
            "\n"
            "## References\n"
            "\n"
            "[1] A. Vaswani, N. Shazeer. Attention Is All You Need.\n"
            f"    NeurIPS, 2017. doi:{DOI}\n"
        )
        citations = extract_from_markdown(md)

        self.assertEqual(len(citations), 1)
        c = citations[0]
        self.assertEqual(c.key, "ref1")
        self.assertEqual(c.title, TITLE)  # continuation line was merged
        self.assertEqual(c.year, 2017)
        self.assertEqual(c.doi, DOI)
        self.assertEqual(c.venue, "NeurIPS")
        self.assertEqual(c.authors, ["A. Vaswani", "N. Shazeer"])
        self.assertIsNotNone(c.claim)
        self.assertIn("注意力机制", c.claim)
        self.assertNotIn("[1]", c.claim)  # citation marker stripped from claim


# ---------------------------------------------------------------------------
# Pure routing function
# ---------------------------------------------------------------------------


def make_verification(
    exists: bool = True,
    similarity: float = 1.0,
    claim: str | None = None,
    supports_claim: bool | None = None,
    backend_failed: bool = False,
    year_consistent: bool | None = True,
    author_consistent: bool | None = None,
    claim_contradicted: bool | None = None,
    bibtex: str | None = OFFICIAL_BIBTEX,
) -> Verification:
    """Hand-build a Verification for direct routing-boundary tests.

    Defaults describe a fully corroborated, provenance-complete strong match
    (year agrees, official BibTeX pulled) so individual cases only override
    the dimension under test.
    """
    v = Verification(citation=Citation(key="k", title="t", claim=claim))
    v.exists = exists
    v.title_similarity = similarity
    v.supports_claim = supports_claim
    v.backend_failed = backend_failed
    v.year_consistent = year_consistent
    v.author_consistent = author_consistent
    v.claim_contradicted = claim_contradicted
    v.bibtex = bibtex
    return v


class RouteVerificationTests(NoNetworkTestCase):
    """route_verification is a pure function with exact three-way boundaries."""

    def test_route_is_pure(self) -> None:
        cases = [
            # (verification, expected_confidence, expected_action, label)
            (
                make_verification(backend_failed=True),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "backend outage overrides everything (fail-safe)",
            ),
            (
                make_verification(exists=False, similarity=0.0),
                Confidence.LOW,
                Action.REJECT,
                "not found anywhere",
            ),
            (
                make_verification(),
                Confidence.HIGH,
                Action.ACCEPT,
                "strong match, no claim attached",
            ),
            (
                make_verification(similarity=0.95),
                Confidence.HIGH,
                Action.ACCEPT,
                "strong threshold is inclusive at exactly 0.95",
            ),
            (
                make_verification(similarity=0.9499),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "just below the strong threshold",
            ),
            (
                make_verification(claim="c", supports_claim=True),
                Confidence.HIGH,
                Action.ACCEPT,
                "strong match, claim supported",
            ),
            (
                make_verification(claim="c", supports_claim=False),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "strong match, claim NOT supported",
            ),
            (
                make_verification(claim="c", supports_claim=None),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "strong match, claim support unknown (no abstract)",
            ),
            (
                make_verification(year_consistent=False),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "perfect title but year contradiction",
            ),
            (
                make_verification(author_consistent=False),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "perfect title but first-author contradiction",
            ),
            (
                make_verification(year_consistent=None, author_consistent=None),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "title-only match with zero corroborating metadata never ACCEPTs",
            ),
            (
                make_verification(
                    claim="c", supports_claim=False, claim_contradicted=True
                ),
                Confidence.LOW,
                Action.REJECT,
                "abstract contradicts the claim -> REJECT, not weak support",
            ),
            (
                make_verification(bibtex=None),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "ACCEPT requires the provenance BibTeX to have been pulled",
            ),
            (
                make_verification(claim="c", supports_claim=True, bibtex=None),
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                "supported claim still cannot ACCEPT without provenance BibTeX",
            ),
        ]
        for v, expected_confidence, expected_action, label in cases:
            with self.subTest(label=label):
                # Poison the mutable outputs so mutation would be detected.
                v.confidence = Confidence.LOW
                v.action = Action.REJECT
                confidence, action, extra_reasons = route_verification(v)
                self.assertIs(confidence, expected_confidence)
                self.assertIs(action, expected_action)
                self.assertIsInstance(extra_reasons, list)
                # Purity: the input object was not mutated ...
                self.assertIs(v.confidence, Confidence.LOW)
                self.assertIs(v.action, Action.REJECT)
                self.assertEqual(v.reasons, [])
                # ... and the function is deterministic.
                self.assertEqual(
                    route_verification(v), (confidence, action, extra_reasons)
                )


# ---------------------------------------------------------------------------
# OpenAlex abstract reconstruction
# ---------------------------------------------------------------------------


class OpenAlexAbstractTests(NoNetworkTestCase):
    """abstract_inverted_index -> plain text reconstruction."""

    def test_openalex_abstract_rebuild(self) -> None:
        rebuild = CitationChecker._rebuild_openalex_abstract
        # Unordered index with a word occurring at multiple positions.
        self.assertEqual(
            rebuild({"the": [0, 2], "more": [1], "merrier": [3]}),
            "the more the merrier",
        )
        # Insertion order must not matter, only the recorded positions.
        self.assertEqual(
            rebuild({"need": [4], "Attention": [0], "all": [2], "is": [1], "you": [3]}),
            "Attention is all you need",
        )
        # OpenAlex sometimes serialises positions as strings; int() coercion.
        self.assertEqual(rebuild({"b": [1], "a": ["0"]}), "a b")
        # Degenerate inputs collapse to None, never to an empty string.
        self.assertIsNone(rebuild(None))
        self.assertIsNone(rebuild({}))
        self.assertIsNone(rebuild({"word": []}))


# ---------------------------------------------------------------------------
# PDF end-to-end smoke test (mock checker; skipped when pypdf is missing)
# ---------------------------------------------------------------------------


def build_minimal_pdf(lines: list[str]) -> bytes:
    """Build a minimal single-page text PDF from scratch (no dependencies).

    Emits raw PDF 1.4 syntax with one Helvetica text object per line and a
    correct xref table, so ``pypdf`` can extract the text back verbatim.
    """

    def escape(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    parts = ["BT /F1 12 Tf 72 720 Td"]
    for i, line in enumerate(lines):
        if i:
            parts.append("0 -16 Td")
        parts.append(f"({escape(line)}) Tj")
    parts.append("ET")
    stream = " ".join(parts).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n"
    xref_pos = len(out)
    out += f"xref\n0 {len(objects) + 1}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode("latin-1")
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    ).encode("latin-1")
    return bytes(out)


class PdfAuditSmokeTests(NoNetworkTestCase):
    """End-to-end: PDF -> extracted citations -> injected mock checker."""

    def test_pdf_audit_smoke_with_mock_checker(self) -> None:
        if pdf_citation_audit.pypdf is None:
            self.skipTest("pypdf is not installed")

        pdf_bytes = build_minimal_pdf(
            [
                "References",
                "[1] A. Vaswani, N. Shazeer. Attention Is All You Need. "
                "NeurIPS, 2017. doi:10.5555/3295222",
                "[2] J. Devlin. BERT: Pre-training of Deep Bidirectional "
                "Transformers. NAACL, 2019.",
            ]
        )
        canned_audit = ReportAudit(
            verifications=[
                Verification(
                    citation=Citation(key="ref1"),
                    exists=True,
                    confidence=Confidence.HIGH,
                    action=Action.ACCEPT,
                )
            ]
        )
        mock_checker = mock.Mock(spec=CitationChecker)
        mock_checker.verify_report.return_value = canned_audit

        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = os.path.join(tmp_dir, "tiny_report.pdf")
            with open(pdf_path, "wb") as handle:
                handle.write(pdf_bytes)
            audit = pdf_citation_audit.audit_pdf(pdf_path, checker=mock_checker)

        # The injected checker was used, and its audit is returned untouched.
        self.assertIs(audit, canned_audit)
        mock_checker.verify_report.assert_called_once()
        (citations,) = mock_checker.verify_report.call_args[0]
        # The PDF extraction really recovered both numbered references.
        self.assertEqual(len(citations), 2)
        self.assertEqual(citations[0].key, "ref1")
        self.assertEqual(citations[0].title, TITLE)
        self.assertEqual(citations[0].year, 2017)
        self.assertEqual(citations[0].doi, "10.5555/3295222")
        self.assertEqual(citations[1].key, "ref2")
        self.assertEqual(
            citations[1].title, "BERT: Pre-training of Deep Bidirectional Transformers"
        )
        self.assertEqual(citations[1].year, 2019)


if __name__ == "__main__":
    unittest.main(verbosity=2)
