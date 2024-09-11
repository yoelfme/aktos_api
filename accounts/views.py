import csv

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import Account, Client, Consumer


@require_GET
def ingest_accounts(request):
    csv_url = request.GET.get('url')
    if not csv_url:
        return JsonResponse({'error': 'URL parameter is required'}, status=400)

    try:
        response = requests.get(csv_url)
        response.raise_for_status()
        csv_content = response.content.decode('utf-8')
        csv_reader = csv.DictReader(csv_content.splitlines())

        for row in csv_reader:
            client, _ = Client.objects.get_or_create(client_reference_no=row['client reference no'])
            
            consumer, _ = Consumer.objects.get_or_create(
                ssn=row['ssn'],
                defaults={
                    'name': row['consumer name'],
                    'address': row['consumer address']
                }
            )

            Account.objects.create(
                balance=float(row['balance']),
                status=row['status'],
                client=client,
                consumer=consumer
            )

        return JsonResponse({'message': 'Data ingested successfully'})
    except requests.RequestException as e:
        return JsonResponse({'error': f'Failed to download CSV: {str(e)}'}, status=500)
    except Exception as e:
        return JsonResponse({'error': f'Error processing data: {str(e)}'}, status=500)


@require_GET
def get_accounts(request):
    # Start with all accounts
    queryset = Account.objects.all()

    # Filter by min_balance
    min_balance = request.GET.get('min_balance')
    if min_balance:
        queryset = queryset.filter(balance__gte=float(min_balance))

    # Filter by max_balance
    max_balance = request.GET.get('max_balance')
    if max_balance:
        queryset = queryset.filter(balance__lte=float(max_balance))

    # Filter by status
    status = request.GET.get('status')
    if status:
        queryset = queryset.filter(status__iexact=status)

    # Filter by consumer_name
    consumer_name = request.GET.get('consumer_name')
    if consumer_name:
        queryset = queryset.filter(consumer__name__icontains=consumer_name)

    # Prepare the response data
    accounts_data = []
    for account in queryset:
        account_data = {
            'account_id': account.account_id,
            'balance': float(account.balance),
            'status': account.status,
            'client_reference_no': account.client.client_reference_no,
            'consumer': {
                'name': account.consumer.name,
                'ssn': account.consumer.ssn,
                'address': account.consumer.address
            }
        }
        accounts_data.append(account_data)

    return JsonResponse({'accounts': accounts_data})