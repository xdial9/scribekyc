# Internal Decision Memo: Identity Verification Vendor Public Stack Assessment

Date: 2026-10-03

## Purpose
This memo summarizes the public evidence for major identity verification vendors and ranks them by public resilience across liveness, document authenticity, device/session integrity, and synthetic-media resistance.

## Scope
This review is based only on public product documentation, developer portals, public whitepapers, and public compliance/security references. It does not include proprietary implementation details, internal architecture, or active testing.

## Executive summary
The public evidence suggests that the strongest vendor stacks are those combining:
- active challenge-based liveness or hybrid detection
- document forensic checks beyond OCR
- device/session integrity validation
- behavioral and synthetic-media risk signals
- escalation for low-quality or suspicious submissions

The most exposed public posture is a passive-only liveness flow with weaker document authenticity and a lack of strong quality escalation.

## Publicly strongest stacks
### AU10TIX
- Strongest public document verification posture
- Public emphasis on forensic tests, chip/NFC validation, and synthetic identity detection
- Strong fraud monitoring and serial fraud detection
- Likely more resilient to high-quality mask + printed-card + degraded-media patterns when active liveness is enforced

### Onfido
- Strong public emphasis on active challenge-response and 3D face mapping
- Strong anti-spoofing and document forensic posture
- Public stack appears well-layered against static-media and presentation attacks

### Jumio
- Strong liveness and identity verification posture
- Active liveness and document checks provide meaningful resilience
- Lower risk than passive-only systems when challenge-response is enabled

## Moderate public stacks
### Socure
- Strong synthetic-media and deepfake focus
- Behavioral analysis helps resist static and synthetic attacks
- Public posture is solid when behavioral signals are consistently enforced

### IDology
- Multi-layer data matching, device fingerprinting, and ecosystem fraud intelligence
- Good resilience but less explicit public detail on deepfake detection than top vendors

## Highest public concern area
### Veriff
- Publicly strongest concern is passive-only liveness
- Device and session integrity are a plus, but passive liveness remains the leading public weak point if compressed or degraded media is accepted
- The combined attack pattern is most plausible when passive liveness, weak document checks, and low-quality uploads are combined

## Recommended defense pattern
To defend against the most common combined presentation attack patterns, the strongest public design pattern is:
- active liveness
- 3D depth or equivalent anti-spoofing
- strict quality thresholds on uploads
- stronger-than-OCR document authenticity checks
- device/session integrity validation
- behavioral and synthetic-media risk signals
- escalation for suspicious or borderline cases

## Concluding view
Public evidence indicates a clear hierarchy of resilience in broad stack design:
1. AU10TIX
2. Onfido
3. Jumio
4. Socure
5. IDology
6. Veriff

This ranking reflects public disclosures and architecture strength only. It does not claim proprietary implementation data or real-world attack outcomes.
