import os

# Test-only connector credential. Production and sandbox runtime configuration
# must provide SHUUD_EXIM_CREDENTIAL explicitly.
os.environ.setdefault("SHUUD_EXIM_CREDENTIAL", "TEST-EXIM-CREDENTIAL")
