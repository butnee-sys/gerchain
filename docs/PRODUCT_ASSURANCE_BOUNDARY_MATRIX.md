# Product Assurance Boundary Matrix

| Layer | Role | Assurance track | Affected by SHUUD result? |
|---|---|---|---|
| NEF | Asset Truth | NEF asset/data assurance | No, unless formally changed |
| G-3 Escrow | Condition Truth | G-3 research/model assurance | No, unless formally changed |
| GerChain CORE | Value-Flow Truth infrastructure | CORE technical assurance | No |
| SHUUD | Application/product | SHUUD product assurance | Yes, within SHUUD only |
| Other applications | Application/product | Separate product assurance | No |

## Rule

A product-layer defect is a product-layer finding unless evidence demonstrates a defect in a CORE control or interface contract. Such evidence must trigger a formal scope/change review before changing the CORE assurance status.

## Evidence separation

CORE evidence and SHUUD evidence must retain separate identifiers, version references, test environments and conclusions.

## Certification separation

No product-level test result is an ISO/IEC 27001 certification claim. No CORE technical test is a SHUUD product certification claim.
