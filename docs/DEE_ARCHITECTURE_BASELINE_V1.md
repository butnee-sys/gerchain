# DEE Architecture Baseline v1

## Canonical structure

```text
DIGITAL ECONOMY
      │
     DEE
      │
NEF + GERCHAIN
      │
CORE ADAPTER
      │
EXIM PORT
      │
CONNECTOR ADAPTER
      │
I2B MULTI-CONNECTOR GATEWAY
      │
 ┌────┼────┐
 ▼    ▼    ▼
ТӨР  КОМПАНИ  ХУВЬ ХҮН
```

SHUUD / SHIID is one replaceable business application prototype connected through the Company side. It is not an infrastructure layer.

Inbound: `Participant → Application → I2B → Connector Adapter → EXIM Port → Core Adapter → NEF–GerChain`

Outbound: `NEF–GerChain → Core Adapter → EXIM Port → Connector Adapter → I2B → Application → Participant`

The three participant classes are external roles, not repository layers.
