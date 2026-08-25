"""Chain-of-Evidence citation verifier for the AI Research Agent.

This module implements interview question #4: verify that every citation in a
generated research report actually exists, and route each citation to an
ACCEPT / HUMAN_REVIEW / REJECT decision based on the verification confidence.

Chain of Evidence -- four non-negotiable principles
---------------------------------------------------
1. Provenance-only BibTeX. Every BibTeX record must come from a traceable
   lookup (CrossRef / OpenAlex, keyed by DOI or fuzzy title match). An LLM is
   NEVER allowed to zero-shot fabricate a BibTeX entry; this module only pulls
   official records from the CrossRef transform endpoint.
2. Claim-evidence support check. When the report body uses a citation to back
   a specific claim, the claim is checked against the cited work's abstract
   (via an injectable judge). A real paper that does not support the claim is
   NOT silently accepted.
3. Unresolvable citations are banned. A citation that cannot be resolved in
   either CrossRef or OpenAlex (by DOI or by title) must be rejected and
   removed from the report.
4. Non-empty bibliography is enforced. Auditing a report with zero citations
   raises EmptyBibliographyError so the pipeline (and its tests) can guarantee
   the final report always carries references.

Confidence routing
------------------
* HIGH / ACCEPT        strong provenance match: high title similarity PLUS at
                       least one positive corroboration (year, first author,
                       or the cited DOI resolving to the matched record), the
                       claim is supported (or no claim was attached), AND the
                       official BibTeX was pulled from the transform endpoint.
* MEDIUM / HUMAN_REVIEW resolvable but ambiguous: weak fuzzy match, metadata
                       conflict, title-only match with no corroborating
                       metadata, missing abstract, unsupported claim, missing
                       provenance BibTeX, or a lookup backend outage
                       (fail-safe: never auto-accept).
* LOW / REJECT         provenance failed (not found anywhere), or the matched
                       abstract contradicts the cited claim.

Only the Python standard library is used. Network calls are injectable so the
module is fully testable offline.
"""

from __future__ import annotations

import difflib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

CROSSREF_WORKS_API = "https://api.crossref.org/works"
OPENALEX_WORKS_API = "https://api.openalex.org/works"

_HTTP_TIMEOUT_SECONDS = 10
_HTTP_MAX_RETRIES = 2  # total attempts = 1 + retries, backoff 1s then 2s


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class LookupBackendError(Exception):
    """Raised when a lookup backend (CrossRef/OpenAlex) is unreachable.

    Raised only after the configured retries are exhausted. Verification
    treats this as "provenance temporarily unverifiable" and fail-safes the
    citation into MEDIUM / HUMAN_REVIEW -- it must never be auto-accepted.
    """


class NotFoundError(Exception):
    """Raised when a backend answers HTTP 404 for a specific record.

    Deliberately NOT a subclass of LookupBackendError: a 404 is a definite
    negative answer (e.g. an invalid DOI), not an infrastructure failure.
    Injected fetchers should follow the same contract.
    """


class EmptyBibliographyError(Exception):
    """Raised when a report audit is requested with zero citations.

    The pipeline must guarantee that a research report is never emitted with
    an empty bibliography; tests assert on this exception.
    """


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Confidence(Enum):
    """Verification confidence level for a single citation."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Action(Enum):
    """Routing decision derived from the verification confidence."""

    ACCEPT = "ACCEPT"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECT = "REJECT"


@dataclass
class Citation:
    """A citation extracted from a report or a .bib file.

    Attributes:
        key: BibTeX-style key or synthetic key (e.g. ``ref3``).
        title: Cited work title as written in the report (may be None when
            parsing failed; such citations can only be resolved via DOI).
        authors: Author names as written (free-form strings).
        year: Publication year claimed by the report, if any.
        doi: DOI claimed by the report, if any (bare form, no URL prefix).
        venue: Journal / conference name, if any.
        claim: The sentence in the report body that this citation is used to
            support, if the extractor could locate one.
        raw: The raw source text this citation was parsed from.
    """

    key: str
    title: Optional[str] = None
    authors: list[str] = field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    claim: Optional[str] = None
    raw: Optional[str] = None


@dataclass
class Verification:
    """The full Chain-of-Evidence verdict for one citation.

    ``backend_failed`` is an internal fail-safe flag: when any provenance
    lookup died with LookupBackendError the citation can never be ACCEPTed
    in this run, regardless of what partial evidence was gathered.
    """

    citation: Citation
    exists: bool = False
    matched_title: Optional[str] = None
    matched_doi: Optional[str] = None
    title_similarity: float = 0.0
    matched_source: Optional[str] = None  # 'crossref' | 'openalex'
    year_consistent: Optional[bool] = None
    author_consistent: Optional[bool] = None
    support_score: Optional[float] = None
    supports_claim: Optional[bool] = None
    claim_contradicted: Optional[bool] = None
    confidence: Confidence = Confidence.MEDIUM
    action: Action = Action.HUMAN_REVIEW
    reasons: list[str] = field(default_factory=list)
    bibtex: Optional[str] = None
    backend_failed: bool = False


@dataclass
class ReportAudit:
    """Aggregated audit result for a whole report's bibliography."""

    verifications: list[Verification] = field(default_factory=list)

    @property
    def n_accept(self) -> int:
        """Number of citations routed to ACCEPT."""
        return sum(1 for v in self.verifications if v.action is Action.ACCEPT)

    @property
    def n_review(self) -> int:
        """Number of citations routed to HUMAN_REVIEW."""
        return sum(1 for v in self.verifications if v.action is Action.HUMAN_REVIEW)

    @property
    def n_reject(self) -> int:
        """Number of citations routed to REJECT."""
        return sum(1 for v in self.verifications if v.action is Action.REJECT)

    @property
    def ok(self) -> bool:
        """True when the bibliography is non-empty and every citation was ACCEPTed."""
        return bool(self.verifications) and self.n_review == 0 and self.n_reject == 0


# ---------------------------------------------------------------------------
# Pure routing function (kept standalone so it is trivially unit-testable)
# ---------------------------------------------------------------------------


def is_strong_match(verification: Verification, title_strong: float = 0.95) -> bool:
    """Pure predicate: does this verification constitute a STRONG match?

    A strong provenance match requires all of:

    1. title similarity >= ``title_strong``;
    2. no metadata contradiction (year or first author explicitly mismatched);
    3. at least one POSITIVE corroboration beyond the title: the year agrees,
       the first author agrees, or the DOI cited in the report resolves to
       the matched record.

    Rule 3 exists because "not contradicted" is not the same as "confirmed":
    a citation carrying only a title could otherwise be auto-accepted against
    any similarly-titled but different work (identity confusion).
    """
    v = verification
    if v.title_similarity < title_strong:
        return False
    if v.year_consistent is False or v.author_consistent is False:
        return False
    doi_corroborated = bool(
        v.citation.doi
        and v.matched_doi
        and v.citation.doi.strip().lower() == v.matched_doi.strip().lower()
    )
    return v.year_consistent is True or v.author_consistent is True or doi_corroborated


def route_verification(
    verification: Verification, title_strong: float = 0.95
) -> tuple[Confidence, Action, list[str]]:
    """Pure confidence-routing function (no side effects, no I/O).

    Rules (in priority order):
    1. Backend outage -> MEDIUM / HUMAN_REVIEW (fail-safe: never auto-accept
       and never auto-reject on infrastructure failure).
    2. Not found in CrossRef nor OpenAlex -> LOW / REJECT.
    3. Strong match (see :func:`is_strong_match`: similarity >=
       ``title_strong``, no year/author contradiction, AND at least one
       positive corroboration among year / first author / cited DOI):
       * abstract CONTRADICTS the claim -> LOW / REJECT (evidence that
         conflicts with the conclusion must never back it);
       * no claim attached, or claim supported -> HIGH / ACCEPT, but ONLY if
         the official provenance BibTeX was retrieved (``bibtex`` non-empty);
         a missing BibTeX downgrades to MEDIUM / HUMAN_REVIEW so downstream
         can never be tempted to let an LLM fabricate the entry;
       * claim attached but NOT supported -> MEDIUM / HUMAN_REVIEW (the paper
         is real but does not back the sentence citing it);
       * claim attached but abstract unavailable -> MEDIUM / HUMAN_REVIEW.
    4. Everything else (weak fuzzy match, metadata conflict, title-only match
       with no corroborating metadata) -> MEDIUM / HUMAN_REVIEW.

    Args:
        verification: A Verification populated by ``verify_one`` (confidence
            and action fields are ignored as input).
        title_strong: Similarity threshold for a strong title match.

    Returns:
        (confidence, action, extra_reasons) -- the caller applies these to the
        Verification and fires the HITL callback when action is HUMAN_REVIEW.
    """
    v = verification
    if v.backend_failed:
        return (
            Confidence.MEDIUM,
            Action.HUMAN_REVIEW,
            ["backend unavailable, needs retry/human"],
        )
    if not v.exists:
        return (
            Confidence.LOW,
            Action.REJECT,
            ["provenance failed: not found in CrossRef or OpenAlex"],
        )
    if is_strong_match(v, title_strong):
        if v.claim_contradicted is True:
            return (
                Confidence.LOW,
                Action.REJECT,
                ["abstract contradicts the cited claim (evidence conflict)"],
            )
        if not v.citation.claim or v.supports_claim is True:
            if v.bibtex:
                return (Confidence.HIGH, Action.ACCEPT, [])
            return (
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                [
                    "provenance BibTeX unavailable; never LLM-generate it -- "
                    "retry the transform endpoint or attach it manually"
                ],
            )
        if v.supports_claim is False:
            return (
                Confidence.MEDIUM,
                Action.HUMAN_REVIEW,
                ["citation exists but does not support the cited claim"],
            )
        return (
            Confidence.MEDIUM,
            Action.HUMAN_REVIEW,
            ["claim support unknown (abstract unavailable)"],
        )
    return (
        Confidence.MEDIUM,
        Action.HUMAN_REVIEW,
        [
            "ambiguous provenance (weak title match, metadata conflict, or "
            "no corroborating year/author/DOI)"
        ],
    )


# ---------------------------------------------------------------------------
# Default claim-support judge (heuristic fallback)
# ---------------------------------------------------------------------------

_STOPWORDS = frozenset(
    """a an the and or but of in on at to for from by with as is are was were be
    been being this that these those it its we our they their he she you your i
    which who whom whose what when where how than then also can could may might
    will would should shall do does did done have has had into over under about
    between among through during more most such only own same so very et al""".split()
)

_NEGATION_TOKENS = frozenset(
    "not no never none nothing neither nor cannot cant dont doesnt didnt "
    "wont without fail fails failed unable lack lacks".split()
)


_CONTRADICTION_OVERLAP = 0.6  # raw overlap above which a negation flip means conflict


def default_support_judge(claim: str, abstract: str) -> tuple[float, bool]:
    """Heuristic lexical claim-support judge.

    Computes a length-weighted Jaccard containment of the normalized claim
    token set against the abstract token set (stopwords removed; each token
    weighted by its character length so contentful terms dominate).

    Contradiction detection: when the two texts talk about the same thing
    (raw overlap >= ``_CONTRADICTION_OVERLAP``) but exactly one side carries
    negation tokens, the abstract is treated as CONTRADICTING the claim
    (e.g. claim "X improves Y" vs abstract "X does not improve Y") -- such a
    citation must be routed to REJECT, never merely "weak support". On any
    negation flip the score is also halved.

    NOTE: this is intentionally a dependency-free, deterministic FALLBACK so
    the module stays testable offline. A production deployment should inject
    an LLM-based judge via ``CitationChecker(support_judge=...)`` -- an LLM
    reads entailment, not just word overlap. An injected judge may return
    either a bare float (contradiction assumed False) or the same
    ``(score, contradicted)`` tuple.

    Args:
        claim: The report sentence the citation is meant to support.
        abstract: The abstract of the matched work.

    Returns:
        ``(score, contradicted)``: score in [0, 1] (higher = the abstract
        lexically covers the claim) and a boolean contradiction verdict.
    """

    def tokens(text: str) -> set[str]:
        norm = CitationChecker._normalize(text)
        return {t for t in norm.split() if t not in _STOPWORDS}

    claim_tokens = tokens(claim)
    abstract_tokens = tokens(abstract)
    if not claim_tokens or not abstract_tokens:
        return (0.0, False)
    weight = lambda toks: sum(len(t) for t in toks)  # noqa: E731
    score = weight(claim_tokens & abstract_tokens) / max(1, weight(claim_tokens))
    claim_negated = bool(claim_tokens & _NEGATION_TOKENS)
    abstract_negated = bool(abstract_tokens & _NEGATION_TOKENS)
    contradicted = False
    if claim_negated != abstract_negated:
        contradicted = score >= _CONTRADICTION_OVERLAP
        score *= 0.5
    return (min(1.0, score), contradicted)


def _default_on_human_review(verification: Verification) -> None:
    """Default HITL hook: print a review notice to stderr.

    Production should inject a real notifier (Slack/e-mail/ticket) via
    ``CitationChecker(on_human_review=...)``.
    """
    print(
        f"[HITL] citation '{verification.citation.key}' needs human review: "
        + ("; ".join(verification.reasons) or "unspecified"),
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# The checker
# ---------------------------------------------------------------------------


class CitationChecker:
    """Verify citations against CrossRef / OpenAlex with confidence routing.

    All external effects are injectable for offline testing:

    * ``fetch_json(url) -> dict``: HTTP GET returning parsed JSON. Must raise
      ``NotFoundError`` on HTTP 404 and ``LookupBackendError`` on any other
      persistent failure (the default implementation does).
    * ``fetch_text(url) -> str``: HTTP GET returning raw text (used for the
      CrossRef BibTeX transform endpoint). Same exception contract.
    * ``support_judge(claim, abstract)``: claim-support scorer returning
      either a float in [0, 1] or a ``(score, contradicted)`` tuple. Defaults
      to :func:`default_support_judge`; inject an LLM judge in production.
    * ``on_human_review(verification) -> None``: HITL notification hook fired
      whenever a citation is routed to HUMAN_REVIEW.
    """

    def __init__(
        self,
        fetch_json: Optional[Callable[[str], dict]] = None,
        fetch_text: Optional[Callable[[str], str]] = None,
        support_judge: Optional[Callable[[str, str], float]] = None,
        on_human_review: Optional[Callable[[Verification], None]] = None,
        mailto: str = "research-agent@example.com",
        title_strong: float = 0.95,
        title_weak: float = 0.80,
        support_threshold: float = 0.45,
    ) -> None:
        """Configure backends, thresholds and hooks.

        Args:
            fetch_json: Injectable JSON GET (see class docstring contract).
            fetch_text: Injectable text GET (see class docstring contract).
            support_judge: Claim-support scorer; defaults to the heuristic
                :func:`default_support_judge`.
            on_human_review: HITL hook; defaults to a stderr notice.
            mailto: Contact address advertised in the User-Agent so CrossRef
                serves us from its polite pool. Keep it a role address; never
                put personal data here in a public deployment.
            title_strong: Similarity threshold for a strong title match.
            title_weak: Similarity threshold below which a match is treated
                as "not found" for that backend.
            support_threshold: Minimum support score for supports_claim=True.
        """
        if not (0.0 <= title_weak <= title_strong <= 1.0):
            raise ValueError("expected 0 <= title_weak <= title_strong <= 1")
        self._fetch_json_impl = fetch_json
        self._fetch_text_impl = fetch_text
        self.support_judge = support_judge or default_support_judge
        self.on_human_review = on_human_review or _default_on_human_review
        self.mailto = mailto
        self.title_strong = title_strong
        self.title_weak = title_weak
        self.support_threshold = support_threshold

    # -- HTTP layer ---------------------------------------------------------

    def _http_get(self, url: str, accept: str) -> str:
        """Default HTTP GET: timeout=10s, up to 2 retries with 1s/2s backoff.

        Raises:
            NotFoundError: on HTTP 404 (a definite negative, not retried).
            LookupBackendError: on any other failure after retries.
        """
        headers = {
            "User-Agent": (
                "ai-research-agent-citation-checker/1.0 "
                f"(https://github.com/jihaoxin; mailto:{self.mailto})"
            ),
            "Accept": accept,
        }
        last_error: Optional[Exception] = None
        for attempt in range(1 + _HTTP_MAX_RETRIES):
            try:
                request = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as resp:
                    return resp.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as err:
                if err.code == 404:
                    raise NotFoundError(f"HTTP 404 for {url}") from err
                last_error = err
            except (urllib.error.URLError, TimeoutError, OSError, ValueError) as err:
                last_error = err
            if attempt < _HTTP_MAX_RETRIES:
                time.sleep(2**attempt)  # 1s, then 2s
        raise LookupBackendError(
            f"GET {url} failed after {1 + _HTTP_MAX_RETRIES} attempts: {last_error!r}"
        )

    def _get_json(self, url: str) -> dict:
        """GET a JSON document via the injected or default fetcher."""
        if self._fetch_json_impl is not None:
            return self._fetch_json_impl(url)
        try:
            return json.loads(self._http_get(url, accept="application/json"))
        except json.JSONDecodeError as err:
            raise LookupBackendError(f"non-JSON response from {url}: {err}") from err

    def _get_text(self, url: str) -> str:
        """GET a plain-text document via the injected or default fetcher."""
        if self._fetch_text_impl is not None:
            return self._fetch_text_impl(url)
        return self._http_get(url, accept="text/plain, application/x-bibtex")

    # -- text utilities -----------------------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for fuzzy matching.

        NFKD-decompose and drop diacritics, lowercase, replace punctuation
        with spaces, and collapse whitespace.
        """
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def _similarity(cls, a: Optional[str], b: Optional[str]) -> float:
        """Fuzzy similarity ratio between two normalized strings in [0, 1]."""
        if not a or not b:
            return 0.0
        return difflib.SequenceMatcher(None, cls._normalize(a), cls._normalize(b)).ratio()

    @staticmethod
    def _strip_jats(markup: str) -> str:
        """Strip JATS/XML tags from a CrossRef abstract and collapse spaces."""
        text = re.sub(r"<[^>]+>", " ", markup)
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _rebuild_openalex_abstract(inverted_index: Optional[dict]) -> Optional[str]:
        """Rebuild plain abstract text from an OpenAlex abstract_inverted_index.

        OpenAlex stores abstracts as ``{word: [position, ...]}``; this places
        each word back at its positions and joins the result.
        """
        if not inverted_index:
            return None
        slots: dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                slots[int(pos)] = word
        if not slots:
            return None
        return " ".join(slots[i] for i in sorted(slots))

    @staticmethod
    def _first_author_family(authors: list[str]) -> Optional[str]:
        """Extract the family name of the first author from free-form names."""
        if not authors:
            return None
        name = authors[0].strip()
        if not name:
            return None
        if "," in name:  # "Family, Given"
            return name.split(",", 1)[0].strip() or None
        parts = name.split()
        return parts[-1] if parts else None

    # -- candidate builders -------------------------------------------------

    def _candidate_from_crossref(self, message: dict) -> dict:
        """Normalize one CrossRef work record into a candidate dict."""
        titles = message.get("title") or []
        title = titles[0] if titles else None
        year = None
        for key in ("issued", "published-print", "published-online", "created"):
            date_parts = (message.get(key) or {}).get("date-parts")
            if date_parts and date_parts[0] and date_parts[0][0]:
                year = int(date_parts[0][0])
                break
        author_list = message.get("author") or []
        family = author_list[0].get("family") if author_list else None
        raw_abstract = message.get("abstract")
        return {
            "source": "crossref",
            "title": title,
            "year": year,
            "first_family": family,
            "doi": message.get("DOI"),
            "abstract": self._strip_jats(raw_abstract) if raw_abstract else None,
        }

    def _candidate_from_openalex(self, record: dict) -> dict:
        """Normalize one OpenAlex work record into a candidate dict."""
        title = record.get("title") or record.get("display_name")
        authorships = record.get("authorships") or []
        display_name = None
        if authorships:
            display_name = (authorships[0].get("author") or {}).get("display_name")
        family = display_name.split()[-1] if display_name else None
        doi = record.get("doi")
        if doi:
            doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
        return {
            "source": "openalex",
            "title": title,
            "year": record.get("publication_year"),
            "first_family": family,
            "doi": doi,
            "abstract": self._rebuild_openalex_abstract(
                record.get("abstract_inverted_index")
            ),
        }

    # -- core verification --------------------------------------------------

    def verify_one(self, citation: Citation) -> Verification:
        """Run the full Chain-of-Evidence check for one citation.

        Pipeline: (a) DOI resolution on CrossRef, (b) fuzzy title search on
        CrossRef with OpenAlex fallback, (c) existence + metadata consistency
        verdict, (d) claim-support judgement against the matched abstract,
        (e) provenance-only BibTeX retrieval, (f) confidence routing (with
        fail-safe handling of backend outages).

        Returns:
            A fully populated, already-routed Verification.
        """
        v = Verification(citation=citation)
        candidates: list[dict] = []

        def note(reason: str) -> None:
            if reason not in v.reasons:
                v.reasons.append(reason)

        def add_candidate(candidate: dict) -> None:
            if citation.title:
                candidate["similarity"] = self._similarity(citation.title, candidate["title"])
            else:
                # No title to compare: a direct DOI hit is identity by DOI.
                candidate["similarity"] = 1.0 if candidate["source"] == "crossref" else 0.0
            candidates.append(candidate)

        def best_candidate() -> Optional[dict]:
            return max(candidates, key=lambda c: c["similarity"]) if candidates else None

        if not citation.doi and not citation.title:
            note("citation has neither DOI nor title; provenance impossible")

        # (a) DOI resolution -------------------------------------------------
        if citation.doi:
            doi_path = urllib.parse.quote(citation.doi, safe="/")
            try:
                data = self._get_json(f"{CROSSREF_WORKS_API}/{doi_path}")
                add_candidate(self._candidate_from_crossref(data.get("message") or {}))
            except NotFoundError:
                note(
                    f"DOI '{citation.doi}' not found on CrossRef (invalid DOI; "
                    "falling back to title search)"
                )
            except LookupBackendError:
                v.backend_failed = True
                note("backend unavailable, needs retry/human")

        best = best_candidate()
        have_strong_doi_hit = best is not None and best["similarity"] >= self.title_strong
        if citation.doi and best is not None and not have_strong_doi_hit:
            note(
                "DOI resolved but its metadata does not match the cited title "
                f"(similarity {best['similarity']:.2f})"
            )

        # (b) title search: CrossRef, then OpenAlex fallback ------------------
        if not have_strong_doi_hit and citation.title:
            need_openalex = False
            query = urllib.parse.quote(citation.title)
            try:
                data = self._get_json(
                    f"{CROSSREF_WORKS_API}?query.bibliographic={query}&rows=5"
                )
                items = (data.get("message") or {}).get("items") or []
                crossref_best = 0.0
                for item in items:
                    candidate = self._candidate_from_crossref(item)
                    add_candidate(candidate)
                    crossref_best = max(crossref_best, candidate["similarity"])
                if not items or crossref_best < self.title_weak:
                    need_openalex = True
            except NotFoundError:
                need_openalex = True
            except LookupBackendError:
                v.backend_failed = True
                need_openalex = True
                note("backend unavailable, needs retry/human")

            if need_openalex:
                try:
                    data = self._get_json(
                        f"{OPENALEX_WORKS_API}?search={query}&per-page=5"
                    )
                    for record in data.get("results") or []:
                        add_candidate(self._candidate_from_openalex(record))
                except NotFoundError:
                    note("OpenAlex search returned 404")
                except LookupBackendError:
                    v.backend_failed = True
                    note("backend unavailable, needs retry/human")

        # (c) existence + metadata consistency --------------------------------
        best = best_candidate()
        strong = False
        if best is not None:
            v.matched_title = best["title"]
            v.matched_doi = best["doi"]
            v.matched_source = best["source"]
            v.title_similarity = best["similarity"]
            if citation.year is not None and best["year"] is not None:
                v.year_consistent = abs(citation.year - int(best["year"])) <= 1
                if not v.year_consistent:
                    note(f"year mismatch: cited {citation.year}, found {best['year']}")
            cited_family = self._first_author_family(citation.authors)
            if cited_family and best["first_family"]:
                v.author_consistent = self._normalize(cited_family) == self._normalize(
                    best["first_family"]
                )
                if not v.author_consistent:
                    note(
                        "first-author mismatch: cited "
                        f"'{cited_family}', found '{best['first_family']}'"
                    )

        if best is not None and v.title_similarity >= self.title_weak:
            v.exists = True
            strong = is_strong_match(v, self.title_strong)
            if not strong and v.title_similarity < self.title_strong:
                note(
                    f"fuzzy title match only ({v.title_similarity:.2f} in "
                    f"[{self.title_weak}, {self.title_strong}))"
                )
            elif not strong:
                note(
                    "title matches but no corroborating metadata "
                    "(year/author/DOI) confirms the identity"
                )
        else:
            v.exists = False
            if best is not None:
                note(
                    f"best candidate similarity {v.title_similarity:.2f} is below "
                    f"the weak threshold {self.title_weak}"
                )
            elif not v.backend_failed and (citation.doi or citation.title):
                note("no candidates found in CrossRef or OpenAlex")

        # (d) claim-support judgement -----------------------------------------
        if v.exists and citation.claim:
            abstract = best.get("abstract") if best else None
            if abstract:
                judgement = self.support_judge(citation.claim, abstract)
                if isinstance(judgement, tuple):
                    score, contradicted = judgement
                else:  # judges may return a bare float (no contradiction info)
                    score, contradicted = judgement, False
                v.support_score = float(score)
                v.claim_contradicted = bool(contradicted)
                v.supports_claim = (
                    not v.claim_contradicted
                    and v.support_score >= self.support_threshold
                )
                if v.claim_contradicted:
                    note("abstract contradicts the cited claim (evidence conflict)")
                elif not v.supports_claim:
                    note(
                        f"support score {v.support_score:.2f} below threshold "
                        f"{self.support_threshold}"
                    )
            else:
                note("abstract unavailable; claim support unknown")

        # (e) provenance-only BibTeX ------------------------------------------
        # The BibTeX is ONLY ever pulled from the official CrossRef transform
        # endpoint -- this module never composes a BibTeX string itself. A
        # contradicted claim is already destined for REJECT, so no pull.
        if (
            strong
            and v.matched_doi
            and not v.backend_failed
            and v.claim_contradicted is not True
        ):
            doi_path = urllib.parse.quote(v.matched_doi, safe="/")
            try:
                v.bibtex = self._get_text(
                    f"{CROSSREF_WORKS_API}/{doi_path}/transform/application/x-bibtex"
                )
            except (NotFoundError, LookupBackendError):
                note("bibtex retrieval failed (non-fatal); regenerate before final build")

        # (f) confidence routing ------------------------------------------------
        return self.route(v)

    def route(self, verification: Verification) -> Verification:
        """Apply :func:`route_verification` and fire the HITL hook if needed.

        Returns the same Verification with ``confidence``/``action`` set and
        routing reasons appended.
        """
        confidence, action, extra_reasons = route_verification(
            verification, self.title_strong
        )
        verification.confidence = confidence
        verification.action = action
        for reason in extra_reasons:
            if reason not in verification.reasons:
                verification.reasons.append(reason)
        if action is Action.HUMAN_REVIEW and self.on_human_review is not None:
            self.on_human_review(verification)
        return verification

    def verify_report(self, citations: list[Citation]) -> ReportAudit:
        """Verify every citation of a report and aggregate the audit.

        Raises:
            EmptyBibliographyError: when ``citations`` is empty -- the
                pipeline guarantees a report never ships without references.
        """
        if not citations:
            raise EmptyBibliographyError(
                "bibliography is empty: a research report must cite at least one source"
            )
        return ReportAudit(verifications=[self.verify_one(c) for c in citations])


# ---------------------------------------------------------------------------
# Parsers (BibTeX / Markdown / single reference entries)
# ---------------------------------------------------------------------------


def parse_bibtex(text: str) -> list[Citation]:
    """Parse a BibTeX string into Citations (lightweight, regex-based).

    Supports ``field = {value}`` (one level of nested braces), ``field =
    "value"`` and bare values; extracts title / author (split on ``and``) /
    year / doi / journal-or-booktitle. ``@comment``/``@string``/``@preamble``
    blocks are skipped. This is a best-effort parser for auditing, not a full
    BibTeX grammar.
    """
    citations: list[Citation] = []
    for match in re.finditer(r"@(\w+)\s*\{", text):
        entry_type = match.group(1).lower()
        if entry_type in ("comment", "string", "preamble"):
            continue
        # Scan to the matching closing brace of the entry body.
        depth = 0
        end = None
        for i in range(match.end() - 1, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            continue  # unbalanced entry; skip
        body = text[match.end() : end]
        key_match = re.match(r"\s*([^,\s{}]+)\s*,", body)
        if not key_match:
            continue
        fields: dict[str, str] = {}
        for fm in re.finditer(
            r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*"|[^,{}\s]+)', body
        ):
            value = fm.group(2).strip()
            if value[:1] in ('{', '"'):
                value = value[1:-1]
            value = re.sub(r"[{}]", "", value)
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", value).strip()
        year: Optional[int] = None
        year_match = re.search(r"\d{4}", fields.get("year", ""))
        if year_match:
            year = int(year_match.group(0))
        authors = [
            a.strip()
            for a in re.split(r"\s+and\s+", fields.get("author", ""))
            if a.strip()
        ]
        citations.append(
            Citation(
                key=key_match.group(1),
                title=fields.get("title") or None,
                authors=authors,
                year=year,
                doi=fields.get("doi") or None,
                venue=fields.get("journal") or fields.get("booktitle") or None,
                raw=text[match.start() : end + 1],
            )
        )
    return citations


_DOI_IN_TEXT_RE = re.compile(
    r"(?:doi:\s*|https?://(?:dx\.)?doi\.org/)(10\.\S+)", re.I
)


def parse_reference_entry(number: int, text: str, claim: Optional[str] = None) -> Citation:
    """Parse one numbered reference entry line into a Citation.

    Expected shape (best effort): ``Authors. Title. Venue, Year. doi:10.x/...``.
    Segments are split on a period followed by whitespace when the period is
    preceded by a lowercase letter or a digit/paren -- this keeps author
    initials like ``A.`` intact. The heuristic is intentionally simple; the
    downstream fuzzy lookup tolerates imperfect splits.
    """
    raw = text
    text = re.sub(r"\s+", " ", text).strip()

    doi = None
    doi_match = _DOI_IN_TEXT_RE.search(text)
    if doi_match:
        doi = doi_match.group(1).rstrip(".,;)")

    year = None
    years = re.findall(r"\b(?:19|20)\d{2}\b", text)
    if years:
        year = int(years[-1])

    core = _DOI_IN_TEXT_RE.sub("", text)
    core = re.sub(r"https?://\S+", "", core).strip()
    parts = [p.strip() for p in re.split(r"(?<=[a-z0-9)])\.\s+", core) if p.strip()]

    authors_text = parts[0] if len(parts) >= 2 else ""
    title = parts[1] if len(parts) >= 2 else (parts[0] if parts else None)
    if title:
        title = title.rstrip(".")
    venue = None
    if len(parts) >= 3:
        venue = re.sub(r",?\s*(?:19|20)\d{2}.*$", "", parts[2]).strip(" .,") or None
    authors = [
        a.strip(" .")
        for a in re.split(r",\s*|\s+and\s+|\s*&\s*", authors_text)
        if a.strip(" .") and a.strip(" .").lower() not in ("et al", "al")
    ]
    return Citation(
        key=f"ref{number}",
        title=title or None,
        authors=authors,
        year=year,
        doi=doi,
        venue=venue,
        claim=claim,
        raw=raw,
    )


def extract_from_markdown(md: str) -> list[Citation]:
    """Extract numbered citations and their supported claims from Markdown.

    Looks for the last ``## References`` / ``## 参考文献`` heading (any level
    1-6), parses subsequent ``[n] Authors. Title. Venue, Year. doi:...`` lines
    (wrapped continuation lines are merged), and attaches as ``claim`` the
    first body sentence that cites ``[n]`` (citation markers stripped).
    """
    heading_re = re.compile(r"^#{1,6}\s*(?:references|参考文献)\s*$", re.I | re.M)
    heading = None
    for m in heading_re.finditer(md):
        heading = m
    if heading is None:
        return []
    body, refs = md[: heading.start()], md[heading.end() :]

    # Collect [n] entries, merging wrapped lines until a blank line/heading.
    entries: dict[int, str] = {}
    current: Optional[int] = None
    for line in refs.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            break  # next section
        entry_match = re.match(r"^\[(\d+)\]\s*(.*)$", stripped)
        if entry_match:
            current = int(entry_match.group(1))
            entries[current] = entry_match.group(2)
        elif stripped and current is not None:
            entries[current] += " " + stripped
        elif not stripped:
            current = None

    # Map citation number -> the first body sentence that cites it.
    # Paragraph breaks also terminate a sentence so headings do not glue
    # onto the following sentence.
    claims: dict[int, str] = {}
    for sentence in re.split(r"(?<=[.!?。!?])\s+|\n{2,}", body):
        for num_text in re.findall(r"\[(\d+)\]", sentence):
            num = int(num_text)
            if num in claims:
                continue
            clean = re.sub(r"\s*\[\d+\]", "", sentence)
            clean = re.sub(r"\s+", " ", clean).strip().lstrip("#*- ").strip()
            if clean:
                claims[num] = clean

    return [
        parse_reference_entry(num, entry, claim=claims.get(num))
        for num, entry in sorted(entries.items())
    ]


# ---------------------------------------------------------------------------
# Reporting / CLI
# ---------------------------------------------------------------------------


def format_audit_table(audit: ReportAudit, max_reason_width: int = 80) -> str:
    """Render an aligned plain-text audit table plus a summary line."""
    headers = ["key", "exists", "sim", "support", "confidence", "action", "reasons"]
    rows: list[list[str]] = []
    for v in audit.verifications:
        if v.supports_claim is None:
            support = "-"
        else:
            support = "yes" if v.supports_claim else "no"
        reasons = "; ".join(v.reasons) or "-"
        if len(reasons) > max_reason_width:
            reasons = reasons[: max_reason_width - 3] + "..."
        rows.append(
            [
                v.citation.key,
                "yes" if v.exists else "no",
                f"{v.title_similarity:.2f}",
                support,
                v.confidence.value,
                v.action.value,
                reasons,
            ]
        )
    widths = [
        max(len(headers[i]), *(len(row[i]) for row in rows)) if rows else len(headers[i])
        for i in range(len(headers))
    ]
    lines = [
        "  ".join(headers[i].ljust(widths[i]) for i in range(len(headers))),
        "  ".join("-" * widths[i] for i in range(len(headers))),
    ]
    for row in rows:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(headers))))
    lines.append("")
    lines.append(
        f"total={len(audit.verifications)} accept={audit.n_accept} "
        f"review={audit.n_review} reject={audit.n_reject} ok={audit.ok}"
    )
    return "\n".join(lines)


def audit_exit_code(audit: ReportAudit) -> int:
    """Map an audit to a process exit code: REJECT->2, HUMAN_REVIEW->1, else 0."""
    if audit.n_reject > 0:
        return 2
    if audit.n_review > 0:
        return 1
    return 0


def main(argv: list[str]) -> int:
    """CLI entry point: ``python citation_checker.py <report.md|refs.bib>``."""
    if len(argv) != 2:
        print("usage: python citation_checker.py <report.md|refs.bib>", file=sys.stderr)
        return 2
    path = argv[1]
    try:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as err:
        print(f"error: cannot read {path}: {err}", file=sys.stderr)
        return 2
    if path.lower().endswith(".bib"):
        citations = parse_bibtex(text)
    else:
        citations = extract_from_markdown(text)
    checker = CitationChecker()
    try:
        audit = checker.verify_report(citations)
    except EmptyBibliographyError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    print(format_audit_table(audit))
    return audit_exit_code(audit)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
