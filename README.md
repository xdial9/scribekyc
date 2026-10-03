# Scribe

A local note-based knowledge assistant for searching security and risk knowledge.

## What this repo includes

- `scribe.py` — the local search assistant
- `dataset/` — starter public dataset for KYC / IDV / fraud / risk knowledge
- `notes/` — working folder for your personal knowledge base

## Project goal

This project is designed for safe, ethical, public-domain security research and internal risk analysis support. The dataset focuses on:

- KYC / IDV vendor risk categories
- Common exploit patterns
- Common public CVE themes
- Security framework concepts
- Mitigation guidance

It does not include confidential or internal competitor data.

## Quick start

```bash
python3 scribe.py --interactive
```

Or a single query:

```bash
python3 scribe.py --query "What are common KYC fraud patterns?"
```

## Dataset organization

```text
dataset/
  providers/
    socure.txt
    onfido.txt
    jumio.txt
  cve_themes/
    liveness_bypass.txt
    document_manipulation.txt
    facial_recognition_exploits.txt
    session_hijacking.txt
  mitigations/
    idv_hardening.txt
    kyc_best_practices.txt
  exploit_patterns/
    deepfake_identity_bypass.txt
    synthetic_media_attacks.txt
    document_fraud_vectors.txt
```

## Example queries

```bash
python3 scribe.py --query "What are common liveness bypass patterns?"
python3 scribe.py --query "How do deepfakes affect KYC?"
python3 scribe.py --query "What are mitigations for document fraud?"
python3 scribe.py --query "What is IDV hardening?"
```

## Important boundary

This project is intended to be a general public risk intelligence and research assistant. It should not be used to access internal or confidential competitor data, nor to analyze non-public systems or data sources.

## Safe use cases

- Risk research
- Public CVE and exploit pattern review
- Security note summarization
- Internal policy / best practice search
- Public KYC / IDV knowledge base

## License

This project is for research and internal tooling use only. Please ensure compliance with local and organizational policy.
