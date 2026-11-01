from shuud.app import app


def test_shuud_app_is_separate_fastapi_product():
    assert app.title == "SHUUD"
    assert app.description == "2 минутын дотор замаа чөлөөл"
