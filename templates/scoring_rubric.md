# Scoring Rubric for Identity Verification Vendors

Use this rubric for public-stack review only. Scores reflect what is publicly disclosed, not internal implementation details.

Scoring scale: 1 = weak, 3 = moderate, 5 = strong

## 1. Liveness strength
- 1: Passive-only or unclear liveness model; little public anti-spoofing detail
- 2: Some liveness detection, but limited challenge design or weak public anti-spoofing claims
- 3: Clear liveness model with some anti-spoofing controls; moderate public evidence
- 4: Active or hybrid liveness with meaningful anti-spoofing and public standards/certifications
- 5: Strong public evidence for active liveness, 3D depth or equivalent, and clear anti-spoofing posture

## 2. Document authenticity strength
- 1: OCR or template checks only; few public forensic controls
- 2: Basic document verification with limited anti-tamper detail
- 3: Reasonable document checks with some forensics and matching
- 4: Strong public document verification with template, tampering, and security-feature checks
- 5: Very strong document authenticity via multiple layers, forensics, and chip/NFC or equivalent verification

## 3. Device / session integrity
- 1: Little or no public device/session integrity controls
- 2: Some browser/device metadata checks, but limited session validation
- 3: Clear device and session controls with moderate integration depth
- 4: Strong device/session signals with meaningful validation and risk routing
- 5: Advanced device and session validation with strong public evidence and layered integrity enforcement

## 4. Synthetic media resistance
- 1: Little to no public synthetic-media or deepfake controls
- 2: Some mention of anti-spoofing or synthetic fraud, but weak public detail
- 3: Clear synthetic-risk controls from public claims and some behavioral checks
- 4: Strong public synthetic-media posture with facial motion, behavioral, or other layered signals
- 5: Very strong synthetic-media posture with multiple layered protection signals and public emphasis on deepfake detection

## 5. Human review / escalation
- 1: No public escalation or manual review
- 2: Minimal manual review or ambiguous outcomes
- 3: Some manual review and escalation path
- 4: Clear escalation paths and review for ambiguous or suspicious submissions
- 5: Strong human review and escalation model with explicit attention to edge cases and high-risk outcomes

## 6. Overall public resilience
- 1: Weak public posture; limited public evidence of layered controls
- 2: Moderate public posture but significant public gaps
- 3: Solid public posture with meaningful coverage across liveness, docs, and fraud controls
- 4: Strong public posture with layered controls and clear public evidence
- 5: Very strong public posture across multiple dimensions with clear public evidence of layered defense

## 7. Confidence in assessment
- Low: limited public evidence or vendor does not disclose enough detail
- Medium: some public evidence but gaps remain
- High: strong public evidence and multiple public sources support the assessment
