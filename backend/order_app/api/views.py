"""Views for orders."""
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Order
from .permissions import IsCustomerUser
from .serializers import OrderCreateSerializer, OrderSerializer


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
