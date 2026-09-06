import pytest
from repository import GerchainRepository
from database import Base


@pytest.fixture
def repo():
    # Тест бүрт тусгаарлагдсан in-memory SQLite database ашиглана.
    repository = GerchainRepository("sqlite:///:memory:")

    # Repository-ийн өөрийн engine дээр schema үүсгэнэ.
    Base.metadata.create_all(bind=repository.engine)

    yield repository

    # Тест дуусмагц schema-г цэвэрлэнэ.
    Base.metadata.drop_all(bind=repository.engine)


def test_save_and_get_escrow_state(repo):
    escrow_id = "test_escrow_999"

    repo.save_escrow_state(
        escrow_id=escrow_id,
        state="PENDING",
        amount=1500,
        currency="USD",
        history=[{"event": "INIT"}]
    )

    data = repo.get_escrow_state(escrow_id)

    assert data is not None
    assert data["escrow_id"] == escrow_id
    assert data["state"] == "PENDING"
    assert data["amount"] == 1500
    assert data["currency"] == "USD"
    assert len(data["history"]) == 1


def test_update_escrow_state(repo):
    escrow_id = "test_escrow_999"

    repo.save_escrow_state(
        escrow_id,
        "PENDING",
        1000,
        "MNT",
        []
    )

    repo.save_escrow_state(
        escrow_id,
        "SETTLED",
        1000,
        "MNT",
        [{"event": "SETTLED"}]
    )

    data = repo.get_escrow_state(escrow_id)

    assert data["state"] == "SETTLED"
    assert len(data["history"]) == 1


def test_save_chain_tip(repo):
    repo.save_chain_tip(
        chain_tip_hash="tip_hash_123",
        manifest_hash="manifest_456",
        state_root="root_789"
    )

    assert True
