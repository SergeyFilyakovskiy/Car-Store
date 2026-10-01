"""
Tests for Celery tasks.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from core.enums import StatusEnum
from dealers.models import DealershipSupplier, PurchasePlan, SupplierPriceLog
from dealers.tasks import (
    actualize_supplier_best_prices,
    calculate_sales_statistics,
    expire_offers,
    purchase_from_suppliers,
)
from deals.models import OfferLog, PurchaseHistory, SupplyHistory
from deals.tasks import process_offer
from django.utils import timezone
from analytics.models import SalesStatistics


# =============================================================================
# Task 1: calculate_sales_statistics
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestCalculateSalesStatistics:
    """Tests for the calculate_sales_statistics task."""

    def test_calculate_statistics_success(self, dealership, purchase_history):
        """The task calculates statistics for a dealership."""
        result = calculate_sales_statistics(dealership.id)

        assert result.get("new_statistics_for") == dealership.name

        stats = SalesStatistics.objects.get(dealership=dealership)
        assert stats.total_sales == 1
        assert stats.total_revenue == purchase_history.price_paid


# =============================================================================
# Task 2: expire_offers
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestExpireOffers:
    """Tests for the expire_offers task."""

    def test_expire_offers_success(self, offer):
        """The task marks expired offers as EXPIRED."""
        offer.expires_at = timezone.now() - timedelta(days=1)
        offer.save(update_fields=["expires_at"])

        result = expire_offers()

        assert result.get("expired_count") == 1
        offer.refresh_from_db()
        assert offer.status == StatusEnum.EXPIRED

    def test_expire_offers_no_expired(self, offer):
        """The task does not affect non-expired offers."""
        result = expire_offers()

        assert result.get("expired_count") == 0
        offer.refresh_from_db()
        assert offer.status == StatusEnum.PENDING


# =============================================================================
# Task 3: actualize_supplier_best_prices
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestActualizeSupplierBestPrices:
    """Tests for the actualize_supplier_best_prices task."""

    def test_actualize_updates_price_when_promo_active(
        self,
        dealership,
        car_model,
        supplier,
        supplier_car_factory,
        supplier_promo_factory,
        supplier_promo_model_factory,
    ):
        """The task updates best_price when an active promo exists."""
        # DealershipSupplier link
        link = DealershipSupplier.objects.create(
            dealer_id=dealership,
            supplier_id=supplier,
            car_model_id=car_model,
            best_price=Decimal("1000.00"),
            is_best=False,
        )

        # SupplierCar with base price (required by pricing service)
        supplier_car_factory(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("1000.00"),
            stock_quantity=10,
        )

        # Active promo: 10% off
        promo = supplier_promo_factory(
            supplier=supplier,
            discount_pct=Decimal("10.00"),
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=1),
        )
        supplier_promo_model_factory(promo=promo, car_model=car_model)

        result = actualize_supplier_best_prices()

        assert "stats" in result
        assert result["stats"]["updated_prices"] >= 1

        link.refresh_from_db()
        assert link.best_price == Decimal("900.00")
        assert SupplierPriceLog.objects.count() == 1

        log = SupplierPriceLog.objects.first()
        assert log is not None
        assert log.old_best_price == Decimal("1000.00")
        assert log.new_best_price == Decimal("900.00")

    def test_actualize_sets_is_best_flag(
        self, dealership, car_model, supplier_factory, supplier_car_factory
    ):
        """The task sets is_best=True for the supplier with the lowest price."""
        supplier_a = supplier_factory(name="Supplier A")
        supplier_b = supplier_factory(name="Supplier B")
        supplier_c = supplier_factory(name="Supplier C")

        # SupplierCar with different base prices
        supplier_car_factory(supplier=supplier_a, car_model=car_model, base_price=Decimal("1000.00"), stock_quantity=10)
        supplier_car_factory(supplier=supplier_b, car_model=car_model, base_price=Decimal("900.00"), stock_quantity=10)
        supplier_car_factory(supplier=supplier_c, car_model=car_model, base_price=Decimal("1100.00"), stock_quantity=10)

        # DealershipSupplier links
        link_a = DealershipSupplier.objects.create(
            dealer_id=dealership, supplier_id=supplier_a, car_model_id=car_model, best_price=Decimal("1000.00")
        )
        link_b = DealershipSupplier.objects.create(
            dealer_id=dealership, supplier_id=supplier_b, car_model_id=car_model, best_price=Decimal("900.00")
        )
        link_c = DealershipSupplier.objects.create(
            dealer_id=dealership, supplier_id=supplier_c, car_model_id=car_model, best_price=Decimal("1100.00")
        )

        actualize_supplier_best_prices()

        link_a.refresh_from_db()
        link_b.refresh_from_db()
        link_c.refresh_from_db()

        assert link_a.is_best is False
        assert link_b.is_best is True  # lowest price
        assert link_c.is_best is False

    def test_actualize_does_not_duplicate_logs(
        self, dealership, car_model, supplier, supplier_car_factory
    ):
        """The task does not create duplicate logs if the price hasn't changed."""
        DealershipSupplier.objects.create(
            dealer_id=dealership,
            supplier_id=supplier,
            car_model_id=car_model,
            best_price=Decimal("1000.00"),
        )
        supplier_car_factory(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("1000.00"),
            stock_quantity=10,
        )

        actualize_supplier_best_prices()
        first_count = SupplierPriceLog.objects.count()

        actualize_supplier_best_prices()
        second_count = SupplierPriceLog.objects.count()

        assert first_count == second_count


# =============================================================================
# Task 4: purchase_from_suppliers
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseFromSuppliers:
    """Tests for the purchase_from_suppliers task."""

    def _setup_purchase_scenario(
        self,
        dealership_factory,
        car_model_factory,
        supplier_factory,
        inventory_factory,
        supplier_car_factory,
        stock_quantity,
    ):
        """Helper: set up a dealership with inventory, supplier, and history."""
        dealership = dealership_factory()
        car_model = car_model_factory()
        supplier = supplier_factory()

        inventory_factory(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=stock_quantity,
            purchase_price=Decimal("1000.00"),
            sale_price=Decimal("1200.00"),
        )

        DealershipSupplier.objects.create(
            dealer_id=dealership,
            supplier_id=supplier,
            car_model_id=car_model,
            best_price=Decimal("1000.00"),
            is_best=True,
        )

        # Supplier stock (required by accept_supply_offer)
        supplier_car_factory(
            supplier=supplier,
            car_model=car_model,
            base_price=Decimal("1000.00"),
            stock_quantity=100,
        )

        # Sales history: 30 units in 30 days -> demand 1/day
        SupplyHistory.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            quantity=30,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("30000.00"),
        )

        dealership.account_id.balance = Decimal("100000.00")
        dealership.account_id.save(update_fields=["balance"])

        return dealership, car_model, supplier

    def test_purchase_creates_purchase_when_stock_covers_one_day(
        self,
        dealership_factory,
        car_model_factory,
        supplier_factory,
        inventory_factory,
        supplier_car_factory,
    ):
        """The task creates a purchase when stock covers only ~2 days of demand."""
        dealership, car_model, supplier = self._setup_purchase_scenario(
            dealership_factory,
            car_model_factory,
            supplier_factory,
            inventory_factory,
            supplier_car_factory,
            stock_quantity=2,
        )

        result = purchase_from_suppliers()

        assert result["total_purchases"] >= 1
        assert PurchasePlan.objects.count() >= 1

        plan = PurchasePlan.objects.first()
        assert plan is not None
        assert plan.dealership == dealership
        assert plan.car_model == car_model
        assert plan.supplier == supplier
        assert plan.status == PurchasePlan.Status.COMPLETED

    def test_purchase_skips_when_stock_covers_14_days(
        self,
        dealership_factory,
        car_model_factory,
        supplier_factory,
        inventory_factory,
        supplier_car_factory,
    ):
        """The task does not create a purchase when stock covers 14+ days."""
        self._setup_purchase_scenario(
            dealership_factory,
            car_model_factory,
            supplier_factory,
            inventory_factory,
            supplier_car_factory,
            stock_quantity=14,
        )

        result = purchase_from_suppliers()

        assert result["total_purchases"] == 0
        assert result["total_rejections"] >= 1

    def test_purchase_is_idempotent(
        self,
        dealership_factory,
        car_model_factory,
        supplier_factory,
        inventory_factory,
        supplier_car_factory,
    ):
        """The task does not create duplicate purchases on repeated runs."""
        self._setup_purchase_scenario(
            dealership_factory,
            car_model_factory,
            supplier_factory,
            inventory_factory,
            supplier_car_factory,
            stock_quantity=2,
        )

        purchase_from_suppliers()
        first_count = PurchasePlan.objects.count()

        purchase_from_suppliers()
        second_count = PurchasePlan.objects.count()

        assert first_count == second_count


# =============================================================================
# Task 5: process_offer
# =============================================================================


@pytest.mark.django_db
@pytest.mark.fast
class TestProcessOffer:
    """Tests for the process_offer task."""

    def test_process_offer_rejects_when_buyer_balance_is_zero(
        self, buyer_user, offer
    ):
        """The task rejects the offer when the buyer balance is zero."""
        buyer_user.balance = Decimal("0")
        buyer_user.save(update_fields=["balance"])

        result = process_offer(str(offer.id))

        assert result["status"] == "rejected"
        assert result["reason"] == "buyer_balance_empty"

        offer.refresh_from_db()
        assert offer.status == StatusEnum.CANCELLED

    def test_process_offer_rejects_when_email_not_verified(
        self, buyer_user, offer
    ):
        """The task rejects the offer when the buyer email is not verified."""
        buyer_user.balance = Decimal("10000.00")
        buyer_user.is_verifyed = False
        buyer_user.save(update_fields=["balance", "is_verifyed"])

        result = process_offer(str(offer.id))

        assert result["status"] == "rejected"
        assert result["reason"] == "email_not_confirmed"

    def test_process_offer_completes_when_dealership_found(
        self, buyer_user, dealership, inventory, offer
    ):
        """The task completes the offer when a suitable dealership is found."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save(update_fields=["balance", "is_verifyed"])

        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.save(update_fields=["quantity", "max_price"])

        inventory.quantity = 5
        inventory.sale_price = Decimal("40000.00")
        inventory.save(update_fields=["quantity", "sale_price"])

        result = process_offer(str(offer.id))

        assert result["status"] == "completed"
        assert "transaction_id" in result

        offer.refresh_from_db()
        assert offer.status == StatusEnum.COMPLETED

        history = PurchaseHistory.objects.filter(offer=offer).first()
        assert history is not None
        assert history.dealership == dealership

    def test_process_offer_is_idempotent(
        self, buyer_user, dealership, inventory, offer
    ):
        """The task does not process the same offer twice."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save(update_fields=["balance", "is_verifyed"])

        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.save(update_fields=["quantity", "max_price"])

        inventory.quantity = 5
        inventory.sale_price = Decimal("40000.00")
        inventory.save(update_fields=["quantity", "sale_price"])

        result1 = process_offer(str(offer.id))
        assert result1["status"] == "completed"

        result2 = process_offer(str(offer.id))
        assert result2["status"] == "already_processed"

    def test_process_offer_selects_cheapest_dealership(
        self,
        buyer_user,
        dealership,
        other_dealership,
        car_model,
        offer,
        inventory_factory,
    ):
        """The task selects the dealership with the lowest price."""
        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save(update_fields=["balance", "is_verifyed"])

        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.save(update_fields=["quantity", "max_price"])

        inventory_factory(
            dealer_id=dealership,
            car_model_id=car_model,
            quantity=5,
            sale_price=Decimal("45000.00"),
            purchase_price=Decimal("40000.00"),
        )
        inventory_factory(
            dealer_id=other_dealership,
            car_model_id=car_model,
            quantity=5,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("35000.00"),
        )

        result = process_offer(str(offer.id))

        assert result["status"] == "completed"
        assert result["dealership_id"] == str(other_dealership.id)

    def test_process_offer_unauthenticated_offer_not_found(self):
        """The task handles a non-existent offer gracefully."""
        result = process_offer("00000000-0000-0000-0000-000000000000")

        assert result["status"] == "not_found"
