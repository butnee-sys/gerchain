import pytest

try:
    import database
except ModuleNotFoundError:
    database = None

Base = getattr(database, "Base", None)

engine = None
for name in dir(database):
    obj = getattr(database, name)
    if hasattr(obj, "connect") and hasattr(obj, "execute"):
        engine = obj
        break
    if hasattr(obj, "kw") and isinstance(obj.kw, dict) and "bind" in obj.kw:
        engine = obj.kw["bind"]
        break

@pytest.fixture(autouse=True)
def setup_database():
    if Base and engine:
        Base.metadata.create_all(bind=engine)
        yield
        Base.metadata.drop_all(bind=engine)
    else:
        yield
