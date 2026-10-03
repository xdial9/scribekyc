# Competitor Research: Public-Source Analysis

This folder contains research based entirely on public sources. No confidential, internal, or non-public data is included.

## Purpose

To build a comprehensive understanding of public technology stacks, known vulnerabilities, and risk patterns in the fintech, lending, identity verification, and onboarding space using only publicly available information.

## Scope and rules

- Public sources only
- Traceable URLs and public notes
- Anonymized entities and generalized component summaries
- No confidential or non-public vendor or customer data
- Human interpretation stays outside the repo and is not treated as factual evidence

## Structure

- `entities/` — anonymized fintech entities and their observable public characteristics
- `stacks/` — observed technology stack components from public sources
- `risk_profiles/` — vulnerability and exploit patterns for each technology component
- `sources/` — tracking of all public sources used for evidence
- `mitigations/` — hardening and control guidance

## Methodology

All data is collected from:
- Public job postings
- Public GitHub repositories
- Company blog posts and case studies
- Investor materials and public filings
- Public API documentation
- Public security advisories and CVE databases
- Public vendor security pages
- Conference talks and public presentations
- News articles and press releases

## Important constraints

- No confidential information
- No unauthorized data access
- No scraping of non-public data
- No internal or proprietary insights
- Everything is publicly sourced and traceable

## How to use this research

The entity anonymization keeps the research safe and professional. The real-world interpretation (knowing which entity is which) remains in your head, not in the repo.

When you query the knowledge base:
- Search for technology patterns
- Find vulnerability themes
- Review mitigation guidance
- Make your own inferences about risk

But the dataset itself stays generalized and public-source based.

## Source tracking

Every claim in this research should be traceable to a public source. See `sources/` for the evidence log.

## Dominant themes in the current corpus

1. Synthetic media and liveness bypass
   - Public evidence repeatedly highlights deepfake and synthetic media as a risk to weak biometric and liveness checks.

2. Document fraud and manipulated identity files
   - Public guidance and research discuss manipulated ID documents, synthetic identity material, and low-confidence onboarding events.

3. Workflow integrity and session abuse
   - Predictable challenge flows, weak session validation, and repeated attempts are common abuse vectors in public guidance.

4. Layered verification and escalation
   - The strongest public pattern is to combine document checks, liveness, session validation, and manual or secondary review.

## Recommended operating model

Keep the repo as the evidence base and keep private interpretation separate from the public corpus.

- Repo = public evidence and structured notes
- Private reasoning = internal synthesis and application

This preserves a clean, defensible research practice and keeps the dataset aligned with public-source-only boundaries.
