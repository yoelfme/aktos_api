from decimal import Decimal
from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from .models import Account
from .models import Client as ClientModel
from .models import Consumer


class AccountViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.client_model = ClientModel.objects.create(client_reference_no='TEST001')
        self.consumer = Consumer.objects.create(ssn='123-45-6789', name='John Doe', address='123 Test St')
        self.account = Account.objects.create(
            balance=Decimal('1000.00'),
            status='ACTIVE',
            client=self.client_model,
            consumer=self.consumer
        )

    @patch('accounts.views.requests.get')
    def test_ingest_accounts_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'client reference no,balance,status,consumer name,consumer address,ssn\nTEST002,2000.00,INACTIVE,Jane Doe,456 Test Ave,987-65-4321'
        
        response = self.client.get(reverse('ingest_accounts'), {'url': 'http://example.com/test.csv'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'Data ingested successfully'})
        
        # Check if the new account was created
        self.assertTrue(Account.objects.filter(client__client_reference_no='TEST002').exists())

    def test_ingest_accounts_no_url(self):
        response = self.client.get(reverse('ingest_accounts'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'URL parameter is required'})

    def test_get_accounts_no_filters(self):
        response = self.client.get(reverse('get_accounts'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['accounts']), 1)

    def test_get_accounts_with_filters(self):
        Account.objects.create(
            balance=Decimal('500.00'),
            status='INACTIVE',
            client=self.client_model,
            consumer=self.consumer
        )
        
        response = self.client.get(reverse('get_accounts'), {'min_balance': '750', 'status': 'ACTIVE'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['accounts']), 1)
        self.assertEqual(response.json()['accounts'][0]['status'], 'ACTIVE')

    def test_get_accounts_consumer_name_filter(self):
        response = self.client.get(reverse('get_accounts'), {'consumer_name': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['accounts']), 1)
        self.assertEqual(response.json()['accounts'][0]['consumer']['name'], 'John Doe')

    def test_get_accounts_no_results(self):
        response = self.client.get(reverse('get_accounts'), {'min_balance': '5000'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['accounts']), 0)
