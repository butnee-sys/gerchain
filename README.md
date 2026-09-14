# GerChain

Core infrastructure for governed digital economic value flow.

The frozen architecture uses explicit boundaries:

```text
DE -> DEE -> G-3 -> NEF + GerChain -> EXIM -> I2B
     ^      ^                ^          ^      ^
   Adapter Adapter         Core       Adapter Adapter
```

The governing rule is:

> **Layer -> Adapter -> Layer**

Operational engines remain inside their owning layers. External economic services enter through the approved boundaries and do not bypass the adapter layer.
