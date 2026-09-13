from pathlib import Path


CORE_IMPORTS = (
    "from escrow",
    "import escrow",
    "from witness",
    "import witness",
    "from verifier",
    "import verifier",
    "from network",
    "import network",
)
PORT_IMPORTS = ("from nef_gerchain_port", "import nef_gerchain_port")


def _python_files(root: Path):
    return root.rglob("*.py")


def test_exim_port_is_the_only_connector_to_port_boundary():
    root = Path(__file__).resolve().parents[1]
    connector_dir = root / "connectors"
    offenders = []
    for path in _python_files(connector_dir):
        text = path.read_text(encoding="utf-8")
        if path.name != "exim_adapter.py" and any(token in text for token in PORT_IMPORTS):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"Only EXIM connector adapter may import the Port: {offenders}"


def test_i2b_gateway_cannot_bypass_connector_and_port_boundaries():
    root = Path(__file__).resolve().parents[1]
    gateway_dir = root / "gateway"
    offenders = []
    for path in _python_files(gateway_dir):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in CORE_IMPORTS + PORT_IMPORTS):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"Gateway must not import core or EXIM Port internals: {offenders}"


def test_application_adapters_cannot_bypass_i2b_and_connector_boundaries():
    root = Path(__file__).resolve().parents[1]
    adapter_dir = root / "application_adapters"
    forbidden = CORE_IMPORTS + PORT_IMPORTS
    offenders = []
    for path in _python_files(adapter_dir):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"Application adapters must not bypass I2B/connector boundaries: {offenders}"


def test_shuud_cannot_bypass_exim_to_reach_core():
    root = Path(__file__).resolve().parents[1]
    shuud_dir = root / "shuud"
    forbidden = CORE_IMPORTS + PORT_IMPORTS
    offenders = []
    for path in _python_files(shuud_dir):
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"SHUUD must not bypass the protected architecture: {offenders}"


def test_exim_port_core_imports_are_isolated_to_core_adapters():
    root = Path(__file__).resolve().parents[1]
    port_dir = root / "nef_gerchain_port"
    allowed = {"gerchain_adapter.py", "nef_adapter.py"}
    offenders = []
    for path in _python_files(port_dir):
        if path.name in allowed:
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in CORE_IMPORTS):
            offenders.append(path.relative_to(root).as_posix())
    assert offenders == [], f"EXIM Port core access must remain isolated to Core Adapters: {offenders}"


def test_protected_directional_topology_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / "nef_gerchain_port").is_dir()
    assert (root / "nef_gerchain_port" / "gerchain_adapter.py").is_file()
    assert (root / "nef_gerchain_port" / "nef_adapter.py").is_file()
    assert (root / "connectors" / "exim_adapter.py").is_file()
    assert (root / "gateway" / "open_multi_connector.py").is_file()
    assert (root / "application_adapters" / "shuud.py").is_file()
