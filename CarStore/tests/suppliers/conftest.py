import pytest
from tests.suppliers.factories import SupplierFactory


@pytest.fixture
def supplier(db, supplier_user):
    """Creates a supplier owned by supplier_user."""

    return SupplierFactory(account_id=supplier_user, name="Test Supplier")
