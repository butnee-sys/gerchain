# OpenSSF OSPS Baseline — IP / License Decision Gate

**Repository:** butnee-sys/gerchain  
**Scope:** GerChain CORE  
**Assessment branch:** `security/openssf-scorecard`  
**OSPS Baseline:** v2026.08.28  
**Target:** Level 1  
**Status:** OPEN — management/IP decision required

## 1. Purpose

This document records the licensing decision gate created during the international technical-security assurance work.

It prevents the repository from adding an open-source license merely to obtain an external badge when the strategic IP policy requires the GerChain CORE source and know-how to remain controlled.

## 2. Verified external requirement

The current OSPS Baseline v2026.08.28 includes Level-1 legal controls requiring the source-code license to satisfy the OSI Open Source Definition or the FSF Free Software Definition, and requiring the license to be maintained in a recognized repository location such as `LICENSE`, `COPYING`, `LICENSES/`, or `LICENSE/`.

Therefore a proprietary/no-license repository cannot honestly be marked fully compliant with the Level-1 OSPS Baseline legal licensing controls.

## 3. GerChain IP protection principle

The current strategic IP principle is:

> Цөмийг худалдахгүй. Цөмд нэвтрэх эрхийг худалдаална.

Accordingly, no MIT, Apache-2.0, BSD, GPL, LGPL, or other open-source license shall be added to GerChain CORE without an explicit IP-owner decision.

## 4. Decision options

### Option A — Controlled/proprietary CORE

Keep GerChain CORE proprietary and protected. Do not add an open-source license solely for assurance purposes.

Consequences:
- OSPS Level-1 legal licensing controls remain GAP/OPEN.
- OpenSSF Best Practices Badge eligibility is not pursued on the basis of a false or incomplete open-source licensing position.
- Technical assurance work can continue through Scorecard, CodeQL, CI evidence, protected-branch governance, security policy, and independent assessment.
- International licensing can be offered as controlled access rather than source-code ownership transfer.

### Option B — Open-source a defined non-core component

If strategically useful, a separately scoped non-core component may later be released under an approved open-source license after legal/IP review.

This does not automatically open GerChain CORE, NEF, G-3 methodology, proprietary algorithms, keys, credentials, or protected know-how.

### Option C — Open-source GerChain CORE

This would require a formal IP-owner decision, ownership-chain review, third-party license review, patent/trade-secret impact review, and a deliberate commercial strategy before adding an open-source license.

This option is NOT authorized by this document.

## 5. Current decision

**Decision:** OPEN.

Until the IP owner formally selects an option, the repository MUST NOT receive an open-source license merely to improve an assurance score.

## 6. Assurance wording

Until the decision is made, the project may state:

> “GerChain CORE-ийн олон улсын техникийн аюулгүй байдлын үнэлгээг OpenSSF OSPS Baseline болон Scorecard-ийн хүрээнд үе шаттайгаар хийж байна. Лицензийн нийцэл нь IP эзэмшлийн бодлогын шийдвэрээс хамаарах тусдаа нээлттэй асуудал хэвээр байна.”

The project MUST NOT state that it has achieved OSPS Level-1 compliance or an OpenSSF Best Practices Badge while the applicable legal licensing controls remain unresolved.

## 7. Security/IP boundary

This decision gate does not authorize disclosure of:
- private keys;
- API tokens;
- passwords;
- production credentials;
- proprietary source outside approved review channels;
- confidential NEF/G-3 know-how;
- unreleased commercial or valuation information.

## 8. Next action

1. Keep CORE runtime frozen.
2. Obtain independent approval for PR #70 CODEOWNERS repair.
3. Obtain independent approval for PR #71 assurance workflow.
4. Merge only through protected-branch governance.
5. Obtain the first published main-branch Scorecard result.
6. Separately decide the IP/license strategy.
7. Only after that decision, determine whether OSPS Level-1 full closure or an OpenSSF Best Practices Badge is strategically appropriate.
