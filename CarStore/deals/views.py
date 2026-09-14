"""
Views for the deals application.

Provides endpoints for buyer offers, transactions, and purchase history.
"""

from accounts.permissions import IsBuyer, IsDealership
from django.db import models
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from deals.exceptions import (
    InsufficientBalanceError,
    OfferAlreadyProcessedError,
    OfferExpiredError,
    OutOfStockError,
)
from deals.models import Offer, PurchaseHistory, Transaction
from deals.serializers import (
    AcceptOfferSerializer,
    OfferSerializer,
    PurchaseHistorySerializer,
    TransactionSerializer,
)
from deals.services import accept_offer


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


class AcceptOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsDealership]

    def post(self, request: Request):
        serialazer = AcceptOfferSerializer(data=request.data)
        serialazer.is_valid(raise_exception=True)

        try:
            offer = Offer.objects.get(id=serialazer.validated_data["offer_id"])  # pyright: ignore[reportOptionalSubscript, reportIndexIssue]
            dealership = request.user.dealership_profile
        except Offer.DoesNotExist:
            return Response(
                {"error": "Offer not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except AttributeError:
            return Response(
                {"error": "User is not a dealership"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            result = accept_offer(offer=offer, dealership=dealership)
        except OfferAlreadyProcessedError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)
        except OfferExpiredError as e:
            return Response({"error": str(e)}, status=status.HTTP_410_GONE)
        except InsufficientBalanceError as e:
            return Response({"error": str(e)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        except OutOfStockError as e:
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            {
                "offer_id": result.offer.id,
                "final_price": str(result.final_price),
                "new_balance": str(result.updated_buyer_balance),
                "transaction_id": str(result.transaction.id),
            },
            status=status.HTTP_200_OK,
        )
