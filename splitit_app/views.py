from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from decimal import Decimal
from .models import Occasion, Event, Expenditure, ExpenditureSplit, Payment
from .serializers import (
    OccasionSerializer, EventSerializer, ExpenditureSerializer,
    PaymentSerializer, UserBalanceSerializer, OccasionSummarySerializer, RegistrationSerializer
)


class OccasionListCreateView(generics.ListCreateAPIView):
    """List and create occasions"""
    serializer_class = OccasionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Occasion.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OccasionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an occasion"""
    serializer_class = OccasionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Occasion.objects.filter(created_by=self.request.user)


class EventListCreateView(generics.ListCreateAPIView):
    """List and create events"""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an event"""
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(created_by=self.request.user)


class RegisterUserView(generics.CreateAPIView):
    """Public endpoint to register a new user (non-admin)."""
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]


class ExpenditureListCreateView(generics.ListCreateAPIView):
    """List and create expenditures"""
    serializer_class = ExpenditureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expenditure.objects.filter(paid_by=self.request.user)

    def perform_create(self, serializer):
        serializer.save(paid_by=self.request.user)


class ExpenditureDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete an expenditure"""
    serializer_class = ExpenditureSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Expenditure.objects.filter(paid_by=self.request.user)


class PaymentListCreateView(generics.ListCreateAPIView):
    """List and create payments"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        )

    def perform_create(self, serializer):
        serializer.save(from_user=self.request.user)


class PaymentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a payment"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(
            Q(from_user=self.request.user) | Q(to_user=self.request.user)
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_balance(request):
    """Get user's balance summary"""
    user = request.user

    # Calculate total amount user owes (exclude splits where user is the payer)
    total_owed = ExpenditureSplit.objects.filter(
        user=user, is_paid=False
    ).exclude(expenditure__paid_by=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Calculate total amount user is owed
    total_owes = ExpenditureSplit.objects.filter(
        expenditure__paid_by=user, is_paid=False
    ).exclude(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    balance = total_owes - total_owed

    serializer = UserBalanceSerializer({
        'user': user,
        'balance': balance,
        'total_owed': total_owed,
        'total_owes': total_owes
    })

    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def occasion_summary(request, occasion_id):
    """Get occasion expenditure summary"""
    try:
        occasion = Occasion.objects.get(id=occasion_id, created_by=request.user)
    except Occasion.DoesNotExist:
        return Response({'error': 'Occasion not found'}, status=status.HTTP_404_NOT_FOUND)

    # Get all events for this occasion
    events = occasion.events.all()

    # Calculate total expenditures
    total_expenditures = Expenditure.objects.filter(
        event__in=events
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    # Get all users involved in this occasion
    user_ids = set()
    for event in events:
        for expenditure in event.expenditures.all():
            user_ids.add(expenditure.paid_by.id)
            for split in expenditure.splits.all():
                user_ids.add(split.user.id)

    users = User.objects.filter(id__in=user_ids)
    user_balances = []

    for user in users:
        # Calculate user's balance for this occasion (exclude splits where user is the payer)
        total_owed = ExpenditureSplit.objects.filter(
            user=user, expenditure__event__in=events, is_paid=False
        ).exclude(expenditure__paid_by=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        total_owes = ExpenditureSplit.objects.filter(
            expenditure__paid_by=user, expenditure__event__in=events, is_paid=False
        ).exclude(user=user).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        balance = total_owes - total_owed

        user_balances.append({
            'user': user,
            'balance': balance,
            'total_owed': total_owed,
            'total_owes': total_owes
        })

    serializer = OccasionSummarySerializer({
        'occasion': occasion,
        'total_expenditures': total_expenditures,
        'total_events': events.count(),
        'user_balances': user_balances
    })

    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def settle_expenditure_split(request, split_id):
    """Settle a specific expenditure split by ID.

    Requirements:
    - Authenticated user must match the split's user.
    - Marks the split as paid and creates a completed payment linked to this split using the split amount.
    """
    try:
        split = ExpenditureSplit.objects.select_related('expenditure', 'expenditure__paid_by', 'user').get(
            id=split_id,
            is_paid=False
        )
    except ExpenditureSplit.DoesNotExist:
        return Response({'error': 'Expenditure split not found or already settled'}, status=status.HTTP_404_NOT_FOUND)

    if split.user_id != request.user.id:
        return Response({'error': 'You can only settle your own split'}, status=status.HTTP_403_FORBIDDEN)

    # Create a completed payment linked to this split
    payment = Payment.objects.create(
        from_user=request.user,
        to_user=split.expenditure.paid_by,
        amount=split.amount,
        description=f"Settlement for expenditure split {split.id}",
        status='completed',
        expenditure_split=split
    )

    # Mark the split as paid
    split.is_paid = True
    split.save(update_fields=['is_paid', 'updated_at'])

    serializer = PaymentSerializer(payment)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def event_expenditures(request, event_id):
    """Get all expenditures for a specific event"""
    try:
        event = Event.objects.get(id=event_id, created_by=request.user)
    except Event.DoesNotExist:
        return Response({'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

    expenditures = event.expenditures.all()
    serializer = ExpenditureSerializer(expenditures, many=True)
    return Response(serializer.data)
