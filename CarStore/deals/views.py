"""
Views for the deals application.

Provides endpoints for buyer offers, transactions, and purchase history.
"""

from accounts.exceptions import InsufficientBalanceError
from accounts.models import Transaction
from accounts.permissions import IsBuyer, IsDealership, IsSupplier
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from CarStore.dealers.models import Dealership
from CarStore.suppliers.models import Supplier
from deals.exceptions import (
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OfferRoleError,
    OutOfStockError,
)
from deals.models import Offer, PurchaseHistory
from deals.serializers import (
    OfferSerializer,
    PurchaseHistorySerializer,
    TransactionSerializer,
)
from deals.services import accept_purchase_offer, accept_supply_offer


class IsOfferOwner(permissions.BasePermission):
    """
    Custom permission to only allow buyers to access their own offers.
    """

    def has_object_permission(self, request, view, obj):
        return obj.buyer.user == request.user


class IsTransactionParticipant(permissions.BasePermission):
    """
    Custom permission to allow access only to participants of the transaction
    (buyer, dealership, or supplier).
    """

    def has_object_permission(self, request, view, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
        if obj.buyer and obj.buyer.user == request.user:
            return True
        if obj.dealership and obj.dealership.account_id == request.user:
            return True
        if obj.supplier and obj.supplier.account_id == request.user:
            return True
        return False


class IsPurchaseHistoryOwner(permissions.BasePermission):
    """
    Custom permission to allow access only to the buyer or dealership
    involved in the purchase.
    """

    def has_object_permission(self, request, view, obj):  # pyright: ignore[reportIncompatibleMethodOverride]
        if obj.buyer.user == request.user:
            return True
        if obj.dealership.account_id == request.user:
            return True
        return False


# ==============================================================================
# Offer Views
# ==============================================================================


class OfferListCreateAPIView(generics.ListCreateAPIView):
    """
    List buyer's offers or create a new offer.
    Only authenticated buyers can access this endpoint.
    """

    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Offer.objects.filter(buyer__user=self.request.user)

    def perform_create(self, serializer):
        from accounts.models import Buyer

        buyer_profile = Buyer.objects.get(user=self.request.user)
        serializer.save(buyer=buyer_profile)


class OfferDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update a specific offer.
    Only the offer owner (buyer) can access this endpoint.
    """

    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated, IsOfferOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        return Offer.objects.filter(buyer__user=self.request.user)


# ==============================================================================
# Transaction Views (Read-Only)
# ==============================================================================


class TransactionListAPIView(generics.ListAPIView):
    """
    List transactions where the user is a participant.
    Available to buyers, dealerships, and suppliers.
    """

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return Transaction.objects.filter(
            models.Q(buyer__user=user)
            | models.Q(dealership__account_id=user)
            | models.Q(supplier__account_id=user)
        )


class TransactionDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific transaction.
    Only participants can access this endpoint.
    """

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTransactionParticipant]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return Transaction.objects.filter(
            models.Q(buyer__user=user)
            | models.Q(dealership__account_id=user)
            | models.Q(supplier__account_id=user)
        )


# ==============================================================================
# Purchase History Views (Read-Only)
# ==============================================================================


class PurchaseHistoryListAPIView(generics.ListAPIView):
    """
    List purchase history for the user.
    Buyers see their purchases, dealerships see their sales.
    """

    serializer_class = PurchaseHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return PurchaseHistory.objects.filter(
            models.Q(buyer__user=user) | models.Q(dealership__account_id=user)
        )


class PurchaseHistoryDetailAPIView(generics.RetrieveAPIView):
    """
    Retrieve details of a specific purchase.
    Only the buyer or dealership involved can access this endpoint.
    """

    serializer_class = PurchaseHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsPurchaseHistoryOwner]

    def get_queryset(self):  # pyright: ignore[reportIncompatibleMethodOverride]
        user = self.request.user
        return PurchaseHistory.objects.filter(
            models.Q(buyer__user=user) | models.Q(dealership__account_id=user)
        )


# ==============================================================================
# Accept offer Views (Read-Only)
# ==============================================================================


class BaseAcceptOfferView(APIView):
    """
    Shared pipeline: fetch offer -> resolve partner -> run service -> map errors.
    Subclasses only define permissions, partner lookup and the service to call.
    """

    accept_fn = None  # set in subclasses

    def get_partner(self, request: Request):
        raise NotImplementedError

    def post(self, request: Request, offer_id: str) -> Response:
        offer = get_object_or_404(Offer, id=offer_id)

        partner = self.get_partner(request)
        if partner is None:
            return Response(
                {"error": "No profile found for your role"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = self.accept_fn(offer, partner)  # pyright: ignore[reportOptionalCall]
        except OfferAlreadyProcessedError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except OfferExpiredError as e:
            return Response({"error": str(e)}, status=status.HTTP_410_GONE)
        except OfferRoleError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except InsufficientBalanceError as e:
            return Response({"error": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except OutOfStockError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        # Own balance after the deal (never expose the counterparty's balance!)
        request.user.refresh_from_db()

        return Response(
            {
                "offer_id": str(result.offer.id),
                "transaction_id": str(result.transaction.id),
                "unit_price": str(result.unit_price),
                "total_price": str(result.total_price),
                "quantity": result.quantity,
                "new_balance": str(request.user.balance),
            },
            status=status.HTTP_200_OK,
        )


class AcceptPurchaseOfferView(BaseAcceptOfferView):
    """Dealership accepts a buyer's offer."""

    permission_classes = [permissions.IsAuthenticated, IsDealership]
    accept_fn = staticmethod(accept_purchase_offer)

    def get_partner(self, request: Request):
        return Dealership.objects.filter(account_id=request.user).first()


class AcceptSupplyOfferView(BaseAcceptOfferView):
    """Supplier accepts a dealership's purchase offer."""

    permission_classes = [permissions.IsAuthenticated, IsSupplier]
    accept_fn = staticmethod(accept_supply_offer)

    def get_partner(self, request: Request):
        return Supplier.objects.filter(account_id=request.user).first()
