"""
Tests for Celery tasks.
"""
from decimal import Decimal

import pytest
from django.utils import timezone
from datetime import timedelta
from dealers.tasks import calculate_sales_statistics, expire_offers
from core.enums import StatusEnum
from tests.dealers.conftest import dealership, other_dealership, dealership_user, other_dealership_user
from tests.deals.conftest import purchase_history
from tests.deals.conftest import offer, transaction, purchase_history
from tests.accounts.conftest import buyer_user, supplier_user
from tests.cars.conftest import car_model, car_brand
from tests.suppliers.conftest import supplier

@pytest.mark.django_db
@pytest.mark.fast
class TestCalculateSalesStatistics:
    def test_calculate_statistics_success(self, dealership, purchase_history):
        """Task should calculate statistics for a dealership."""
        result = calculate_sales_statistics(dealership.id)

        assert result.get("new_statistics_for") == dealership.name

        from analytics.models import SalesStatistics
        stats = SalesStatistics.objects.get(dealership=dealership)
        assert stats.total_sales == 1
        assert stats.total_revenue == purchase_history.price_paid



@pytest.mark.django_db
@pytest.mark.fast
class TestExpireOffers:
    def test_expire_offers_success(self, offer):
        """Task should mark expired offers as EXPIRED."""

        offer.expires_at = timezone.now() - timedelta(days=1)
        offer.save()

        result = expire_offers()

        assert result.get("expired_count") == 1
        offer.refresh_from_db()
        assert offer.status == StatusEnum.EXPIRED

    def test_expire_offers_no_expired(self, offer):
        """Task should not affect non-expired offers."""
        result = expire_offers()

        assert result.get("expired_count") == 0
        offer.refresh_from_db()
        assert offer.status == StatusEnum.PENDING

@pytest.mark.django_db
@pytest.mark.fast
class TestActualizeSupplierBestPrices:
    def test_actualize_supplier_prices_updates_price_when_promo_active(
        self, dealership_supplier_factory, supplier_promo_factory
    ):
        """Task should update best_price when active promo exists."""
        from dealers.models import DealershipSupplier, SupplierPriceLog
        from dealers.tasks import actualize_supplier_best_prices

        link = dealership_supplier_factory(
            base_price=Decimal("1000.00"),
            best_price=Decimal("1000.00"),
        )

        supplier_promo_factory(
            supplier=link.supplier_id,
            car_model=link.car_model_id,
            discount_pct=Decimal("10.00"),
            start_date=timezone.now().date() - timedelta(days=1),
            end_date=timezone.now().date() + timedelta(days=1),
        )

        result = actualize_supplier_best_prices()

        assert "stats" in result
        assert result["stats"]["updated_prices"] >= 1

        link.refresh_from_db()
        assert link.best_price == Decimal("900.00")
        assert SupplierPriceLog.objects.count() == 1

        log = SupplierPriceLog.objects.first()
        assert log.old_best_price == Decimal("1000.00") #type: ignore
        assert log.new_best_price == Decimal("900.00") #type: ignore

    def test_actualize_supplier_prices_sets_is_best_flag(
        self, dealership, car_model, supplier_factory
    ):
        """Task should set is_best=True for supplier with lowest price."""
        from dealers.models import DealershipSupplier
        from dealers.tasks import actualize_supplier_best_prices

        supplier_a = supplier_factory(name="Supplier A")
        supplier_b = supplier_factory(name="Supplier B")
        supplier_c = supplier_factory(name="Supplier C")

        link_a = DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier_a,
            car_model=car_model,
            best_price=Decimal("1000.00"),
            is_best=False,
        )
        link_b = DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier_b,
            car_model=car_model,
            best_price=Decimal("900.00"),
            is_best=False,
        )
        link_c = DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier_c,
            car_model=car_model,
            best_price=Decimal("1100.00"),
            is_best=False,
        )

        actualize_supplier_best_prices()

        link_a.refresh_from_db()
        link_b.refresh_from_db()
        link_c.refresh_from_db()

        assert link_a.is_best is False
        assert link_b.is_best is True
        assert link_c.is_best is False

    def test_actualize_supplier_prices_does_not_duplicate_logs(
        self, dealership_supplier_factory
    ):
        """Task should not create duplicate logs if price hasn't changed."""
        from dealers.models import SupplierPriceLog
        from dealers.tasks import actualize_supplier_best_prices

        link = dealership_supplier_factory(
            base_price=Decimal("1000.00"),
            best_price=Decimal("1000.00"),
        )

        actualize_supplier_best_prices()
        first_count = SupplierPriceLog.objects.count()

        actualize_supplier_best_prices()
        second_count = SupplierPriceLog.objects.count()

        assert first_count == second_count

@pytest.mark.django_db
@pytest.mark.fast
class TestPurchaseFromSuppliers:
    def test_purchase_task_creates_purchase_when_stock_covers_only_one_day(
        self, dealership_factory, car_model_factory, supplier_factory, inventory_factory
    ):
        """Task should create purchase when stock covers only 1 day of demand."""
        from dealers.models import DealershipSupplier, PurchasePlan
        from dealers.tasks import purchase_from_suppliers
        from deals.models import SupplyHistory

        dealership = dealership_factory()
        car_model = car_model_factory()
        supplier = supplier_factory()

        inventory = inventory_factory(
            dealership=dealership,
            car_model=car_model,
            quantity=2,
            purchase_price=Decimal("1000.00"),
            sale_price=Decimal("1200.00"),
        )

        DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            best_price=Decimal("1000.00"),
            is_best=True,
        )

        SupplyHistory.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            quantity=30,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("30000.00"),
        )

        dealership.account_id.balance = Decimal("100000.00")
        dealership.account_id.save()

        result = purchase_from_suppliers()

        assert result["total_purchases"] >= 1
        assert PurchasePlan.objects.count() >= 1

        plan = PurchasePlan.objects.first()
        assert plan is not None
        assert plan.dealership == dealership
        assert plan.car_model == car_model
        assert plan.supplier == supplier
        assert plan.status == PurchasePlan.Status.COMPLETED

    def test_purchase_task_does_not_create_purchase_when_stock_covers_14_days(
        self, dealership_factory, car_model_factory, supplier_factory, inventory_factory
    ):
        """Task should not create purchase when stock covers 14+ days."""
        from dealers.models import DealershipSupplier, PurchasePlan
        from dealers.tasks import purchase_from_suppliers
        from deals.models import SupplyHistory

        dealership = dealership_factory()
        car_model = car_model_factory()
        supplier = supplier_factory()

        inventory = inventory_factory(
            dealership=dealership,
            car_model=car_model,
            quantity=14,
            purchase_price=Decimal("1000.00"),
            sale_price=Decimal("1200.00"),
        )

        DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            best_price=Decimal("1000.00"),
            is_best=True,
        )

        SupplyHistory.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            quantity=30,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("30000.00"),
        )

        dealership.account_id.balance = Decimal("100000.00")
        dealership.account_id.save()

        result = purchase_from_suppliers()

        assert result["total_purchases"] == 0
        assert result["total_rejections"] >= 1

    def test_purchase_task_is_idempotent(
        self, dealership_factory, car_model_factory, supplier_factory, inventory_factory
    ):
        """Task should not create duplicate purchases on repeated runs."""
        from dealers.models import DealershipSupplier, PurchasePlan
        from dealers.tasks import purchase_from_suppliers
        from deals.models import SupplyHistory

        dealership = dealership_factory()
        car_model = car_model_factory()
        supplier = supplier_factory()

        inventory = inventory_factory(
            dealership=dealership,
            car_model=car_model,
            quantity=2,
            purchase_price=Decimal("1000.00"),
            sale_price=Decimal("1200.00"),
        )

        DealershipSupplier.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            best_price=Decimal("1000.00"),
            is_best=True,
        )

        SupplyHistory.objects.create(
            dealership=dealership,
            supplier=supplier,
            car_model=car_model,
            quantity=30,
            unit_price=Decimal("1000.00"),
            total_price=Decimal("30000.00"),
        )

        dealership.account_id.balance = Decimal("100000.00")
        dealership.account_id.save()

        purchase_from_suppliers()
        first_count = PurchasePlan.objects.count()

        purchase_from_suppliers()
        second_count = PurchasePlan.objects.count()

        assert first_count == second_count

@pytest.mark.django_db
@pytest.mark.fast
class TestProcessOffer:
    def test_process_offer_rejects_when_buyer_balance_is_zero(
        self, buyer_user, offer, car_model
    ):
        """Task should reject offer when buyer balance is zero."""
        from deals.models import OfferLog
        from deals.tasks import process_offer
        from core.enums import StatusEnum

        buyer_user.balance = Decimal("0")
        buyer_user.save()

        offer.creator = buyer_user
        offer.car_model = car_model
        offer.status = StatusEnum.PENDING
        offer.save()

        result = process_offer(str(offer.id))

        assert result["status"] == "rejected"
        assert result["reason"] == "buyer_balance_empty"

        offer.refresh_from_db()
        assert offer.status == StatusEnum.CANCELLED

    def test_process_offer_rejects_when_email_not_verified(
        self, buyer_user, offer, car_model
    ):
        """Task should reject offer when buyer email is not verified."""
        from deals.tasks import process_offer
        from core.enums import StatusEnum

        buyer_user.balance = Decimal("10000.00")
        buyer_user.is_verifyed = False
        buyer_user.save()

        offer.creator = buyer_user
        offer.car_model = car_model
        offer.status = StatusEnum.PENDING
        offer.save()

        result = process_offer(str(offer.id))

        assert result["status"] == "rejected"
        assert result["reason"] == "email_not_confirmed"

    def test_process_offer_completes_when_dealership_found(
        self, buyer_user, dealership, inventory, offer, car_model
    ):
        """Task should complete offer when suitable dealership is found."""
        from deals.tasks import process_offer
        from deals.models import PurchaseHistory
        from core.enums import StatusEnum

        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save()

        offer.creator = buyer_user
        offer.car_model = car_model
        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.status = StatusEnum.PENDING
        offer.save()

        inventory.car_model_id = car_model
        inventory.dealer_id = dealership
        inventory.quantity = 5
        inventory.sale_price = Decimal("40000.00")
        inventory.save()

        result = process_offer(str(offer.id))

        assert result["status"] == "completed"
        assert "transaction_id" in result

        offer.refresh_from_db()
        assert offer.status == StatusEnum.COMPLETED

        history = PurchaseHistory.objects.filter(offer=offer).first()
        assert history is not None
        assert history.dealership == dealership

    def test_process_offer_is_idempotent(
        self, buyer_user, dealership, inventory, offer, car_model
    ):
        """Task should not process the same offer twice."""
        from deals.tasks import process_offer
        from core.enums import StatusEnum

        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save()

        offer.creator = buyer_user
        offer.car_model = car_model
        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.status = StatusEnum.PENDING
        offer.save()

        inventory.car_model_id = car_model
        inventory.dealer_id = dealership
        inventory.quantity = 5
        inventory.sale_price = Decimal("40000.00")
        inventory.save()

        result1 = process_offer(str(offer.id))
        assert result1["status"] == "completed"

        result2 = process_offer(str(offer.id))
        assert result2["status"] == "already_processed"

    def test_process_offer_selects_cheapest_dealership(
        self, buyer_user, dealership, other_dealership, car_model, offer, inventory_factory
    ):
        """Task should select dealership with lowest price."""
        from deals.tasks import process_offer
        from core.enums import StatusEnum

        buyer_user.balance = Decimal("100000.00")
        buyer_user.is_verifyed = True
        buyer_user.save()

        offer.creator = buyer_user
        offer.car_model = car_model
        offer.quantity = 1
        offer.max_price = Decimal("50000.00")
        offer.status = StatusEnum.PENDING
        offer.save()

        inventory_factory(
            dealership=dealership,
            car_model=car_model,
            quantity=5,
            sale_price=Decimal("45000.00"),
            purchase_price=Decimal("40000.00"),
        )
        inventory_factory(
            dealership=other_dealership,
            car_model=car_model,
            quantity=5,
            sale_price=Decimal("40000.00"),
            purchase_price=Decimal("35000.00"),
        )

        result = process_offer(str(offer.id))

        assert result["status"] == "completed"
        assert result["dealership_id"] == str(other_dealership.id)
