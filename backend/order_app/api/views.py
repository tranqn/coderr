"""Views for orders and the count helpers."""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Order
from .permissions import (
    IsAdminForDelete,
    IsBusinessUserOfOrder,
    IsCustomerUser,
)
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusUpdateSerializer,
)

User = get_user_model()


class OrderListCreateView(APIView):
    """GET — orders involving the requester. POST — create as customer."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsCustomerUser()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = Order.objects.filter(
            Q(customer_user=request.user) | Q(business_user=request.user)
        )
        return Response(OrderSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = OrderCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(
            OrderSerializer(order).data, status=status.HTTP_201_CREATED
        )


class OrderDetailView(APIView):
    """PATCH (business-only) and DELETE for an order."""

    permission_classes = [IsAuthenticated]

    def _get_order(self, pk):
        try:
            return Order.objects.get(pk=pk)
        except Order.DoesNotExist as exc:
            raise Http404("Order not found.") from exc

    def patch(self, request, pk):
        order = self._get_order(pk)
        permission = IsBusinessUserOfOrder()
        if not permission.has_object_permission(request, self, order):
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = OrderStatusUpdateSerializer(
            order, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(order).data)

    def delete(self, request, pk):
        if not IsAdminForDelete().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        order = self._get_order(pk)
        order.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _ensure_business_user(business_user_id):
    """Return the user or raise 404 when missing or not a business profile."""
    try:
        user = User.objects.select_related("profile").get(pk=business_user_id)
    except User.DoesNotExist as exc:
        raise Http404("Business user not found.") from exc
    profile = getattr(user, "profile", None)
    if not profile or profile.type != "business":
        raise Http404("Business user not found.")
    return user


class OrderCountView(APIView):
    """GET /api/order-count/{business_user_id}/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        user = _ensure_business_user(business_user_id)
        count = Order.objects.filter(
            business_user=user, status="in_progress"
        ).count()
        return Response({"order_count": count})


class CompletedOrderCountView(APIView):
    """GET /api/completed-order-count/{business_user_id}/."""

    permission_classes = [IsAuthenticated]

    def get(self, request, business_user_id):
        user = _ensure_business_user(business_user_id)
        count = Order.objects.filter(
            business_user=user, status="completed"
        ).count()
        return Response({"completed_order_count": count})
