from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from decimal import Decimal
from .models import Occasion, Event, Expenditure, ExpenditureSplit, Payment

class SplitItAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@example.com',
            password='testpass123'
        )
        
        # Get JWT token for user1
        refresh = RefreshToken.for_user(self.user1)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

class OccasionAPITest(SplitItAPITestCase):
    def test_create_occasion(self):
        """Test creating a new occasion"""
        data = {
            'name': 'Test Occasion',
            'description': 'A test occasion for splitting expenses'
        }
        response = self.client.post('/api/occasions/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Occasion.objects.count(), 1)
        self.assertEqual(Occasion.objects.get().name, 'Test Occasion')

    def test_list_occasions(self):
        """Test listing occasions"""
        Occasion.objects.create(
            name='Test Occasion',
            created_by=self.user1
        )
        response = self.client.get('/api/occasions/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_occasion_detail(self):
        """Test retrieving occasion detail"""
        occasion = Occasion.objects.create(
            name='Test Occasion',
            created_by=self.user1
        )
        response = self.client.get(f'/api/occasions/{occasion.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Occasion')

class EventAPITest(SplitItAPITestCase):
    def setUp(self):
        super().setUp()
        self.occasion = Occasion.objects.create(
            name='Test Occasion',
            created_by=self.user1
        )

    def test_create_event_with_occasion(self):
        """Test creating an event with an occasion"""
        data = {
            'name': 'Test Event',
            'description': 'A test event',
            'occasion': self.occasion.id
        }
        response = self.client.post('/api/events/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Event.objects.get().occasion, self.occasion)

    def test_create_event_without_occasion(self):
        """Test creating an event without an occasion"""
        data = {
            'name': 'Test Event',
            'description': 'A test event'
        }
        response = self.client.post('/api/events/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Event.objects.count(), 1)
        self.assertIsNone(Event.objects.get().occasion)

class ExpenditureAPITest(SplitItAPITestCase):
    def setUp(self):
        super().setUp()
        self.event = Event.objects.create(
            name='Test Event',
            created_by=self.user1
        )

    def test_create_expenditure_equal_split(self):
        """Test creating an expenditure with equal split"""
        data = {
            'event': self.event.id,
            'amount': '100.00',
            'description': 'Test expense',
            'split_type': 'equal',
            'split_user_ids': [self.user2.id, self.user3.id]
        }
        response = self.client.post('/api/expenditures/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expenditure.objects.count(), 1)
        self.assertEqual(ExpenditureSplit.objects.count(), 2)
        
        # Check that amounts are split equally
        splits = ExpenditureSplit.objects.filter(expenditure__id=response.data['id'])
        for split in splits:
            self.assertEqual(split.amount, Decimal('50.00'))

    def test_create_expenditure_custom_split(self):
        """Test creating an expenditure with custom split"""
        data = {
            'event': self.event.id,
            'amount': '100.00',
            'description': 'Test expense',
            'split_type': 'custom',
            'split_user_ids': [self.user2.id, self.user3.id],
            'custom_amounts': ['60.00', '40.00']
        }
        response = self.client.post('/api/expenditures/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Expenditure.objects.count(), 1)
        self.assertEqual(ExpenditureSplit.objects.count(), 2)
        
        # Check custom amounts
        splits = ExpenditureSplit.objects.filter(expenditure__id=response.data['id'])
        amounts = [split.amount for split in splits]
        self.assertIn(Decimal('60.00'), amounts)
        self.assertIn(Decimal('40.00'), amounts)

    def test_create_expenditure_invalid_custom_split(self):
        """Test creating an expenditure with invalid custom split amounts"""
        data = {
            'event': self.event.id,
            'amount': '100.00',
            'description': 'Test expense',
            'split_type': 'custom',
            'split_user_ids': [self.user2.id, self.user3.id],
            'custom_amounts': ['60.00', '50.00']  # Sum doesn't equal total
        }
        response = self.client.post('/api/expenditures/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class PaymentAPITest(SplitItAPITestCase):
    def test_create_payment(self):
        """Test creating a payment"""
        data = {
            'to_user_id': self.user2.id,
            'amount': '50.00',
            'description': 'Test payment'
        }
        response = self.client.post('/api/payments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(Payment.objects.get().amount, Decimal('50.00'))

    def test_settle_expenditure_split(self):
        """Test settling an expenditure split via new endpoint"""
        # user1 (auth) owes user2
        event = Event.objects.create(name='Test Event', created_by=self.user2)
        expenditure = Expenditure.objects.create(
            event=event,
            amount=Decimal('50.00'),
            description='Dinner',
            paid_by=self.user2
        )
        split = ExpenditureSplit.objects.create(
            expenditure=expenditure,
            user=self.user1,
            amount=Decimal('50.00')
        )
        response = self.client.post(f'/api/expenditure-splits/{split.id}/settle/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        split.refresh_from_db()
        self.assertTrue(split.is_paid)
        payment = Payment.objects.get(expenditure_split=split)
        self.assertEqual(payment.status, 'completed')

class UserBalanceAPITest(SplitItAPITestCase):
    def test_user_balance(self):
        """Test getting user balance"""
        # Create an expenditure where user1 pays and user2 owes
        event = Event.objects.create(name='Test Event', created_by=self.user1)
        expenditure = Expenditure.objects.create(
            event=event,
            amount=Decimal('100.00'),
            description='Test expense',
            paid_by=self.user1
        )
        ExpenditureSplit.objects.create(
            expenditure=expenditure,
            user=self.user2,
            amount=Decimal('50.00')
        )
        
        response = self.client.get('/api/user/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_owes'], Decimal('50.00'))
        self.assertEqual(response.data['total_owed'], Decimal('0.00'))
        self.assertEqual(response.data['balance'], Decimal('50.00'))

class OccasionSummaryAPITest(SplitItAPITestCase):
    def test_occasion_summary(self):
        """Test getting occasion summary"""
        occasion = Occasion.objects.create(
            name='Test Occasion',
            created_by=self.user1
        )
        event = Event.objects.create(
            name='Test Event',
            occasion=occasion,
            created_by=self.user1
        )
        expenditure = Expenditure.objects.create(
            event=event,
            amount=Decimal('100.00'),
            description='Test expense',
            paid_by=self.user1
        )
        ExpenditureSplit.objects.create(
            expenditure=expenditure,
            user=self.user2,
            amount=Decimal('50.00')
        )
        
        response = self.client.get(f'/api/occasions/{occasion.id}/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_expenditures'], Decimal('100.00'))
        self.assertEqual(response.data['total_events'], 1)

class AuthenticationTest(APITestCase):
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access protected endpoints"""
        response = self.client.get('/api/occasions/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_authentication(self):
        """Test JWT token authentication"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get('/api/user/balance/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)