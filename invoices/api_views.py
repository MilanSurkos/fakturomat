import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from .models import Invoice, InvoiceItem

# Set up logging
logger = logging.getLogger("invoices")

logger = logging.getLogger("invoices")

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal
from django.db import transaction
from .models import Invoice, InvoiceItem

@csrf_exempt
@require_http_methods(["POST"])
def calculate_invoice_totals(request):
    """
    Calculate invoice totals including subtotal, tax, and grand total.
    
    Expected JSON payload:
    {
        "tax_rate": "20.00",
        "currency": "EUR",
        "items": [
            {
                "quantity": "2",
                "unit_price": "10.00",
                "description": "Product A"
            },
            ...
        ]
    }
    """
    try:
        # Parse and validate request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {'success': False, 'error': 'Invalid JSON payload'}, 
                status=400
            )
        
        # Validate required fields
        if 'items' not in data:
            return JsonResponse(
                {'success': False, 'error': 'Missing required field: items'}, 
                status=400
            )
        
        # Get and validate tax rate
        try:
            tax_rate = Decimal(str(data.get('tax_rate', 0)))
            if tax_rate < 0 or tax_rate > 100:
                return JsonResponse(
                    {'success': False, 'error': 'Tax rate must be between 0 and 100'}, 
                    status=400
                )
        except (TypeError, ValueError, decimal.InvalidOperation):
            return JsonResponse(
                {'success': False, 'error': 'Invalid tax rate format'}, 
                status=400
            )
        
        # Initialize totals
        subtotal = Decimal('0')
        items = data.get('items', [])
        
        # Validate and process items
        for i, item in enumerate(items, 1):
            # Skip deleted items
            if item.get('DELETE') == 'on':
                continue
                
            # Validate item data
            try:
                quantity = Decimal(str(item.get('quantity', 0)))
                unit_price = Decimal(str(item.get('unit_price', 0)))
                
                if quantity < 0:
                    return JsonResponse(
                        {'success': False, 'error': f'Item {i}: Quantity cannot be negative'}, 
                        status=400
                    )
                    
                if unit_price < 0:
                    return JsonResponse(
                        {'success': False, 'error': f'Item {i}: Unit price cannot be negative'}, 
                        status=400
                    )
                
                # Calculate item total with proper rounding
                item_total = (quantity * unit_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                subtotal += item_total
                
            except (TypeError, ValueError, decimal.InvalidOperation) as e:
                return JsonResponse(
                    {'success': False, 'error': f'Item {i}: Invalid quantity or price format'}, 
                    status=400
                )
        
        # Calculate tax and total with proper rounding
        tax_amount = (subtotal * tax_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total = (subtotal + tax_amount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Ensure subtotal is properly quantized
        subtotal = subtotal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return JsonResponse({
            'success': True,
            'subtotal': str(subtotal),
            'tax_amount': str(tax_amount),
            'total': str(total),
            'currency': data.get('currency', 'EUR'),
            'tax_rate': str(tax_rate)
        })
        
    except Exception as e:
        # Log the full error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error calculating invoice totals")
        
        # Return a generic error message to the client
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while calculating totals. Please try again.'
        }, status=500)
