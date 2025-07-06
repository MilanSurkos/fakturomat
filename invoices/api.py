from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal

@csrf_exempt
@require_http_methods(["POST"])
def calculate_totals(request):
    try:
        data = json.loads(request.body)
        items = data.get('items', [])
        tax_rate = Decimal(str(data.get('tax_rate', 0)))

        subtotal = Decimal('0')
        tax_amount = Decimal('0')
        total = Decimal('0')

        calculated_items = []

        for item in items:
            quantity = Decimal(str(item.get('quantity', 0)))
            unit_price = Decimal(str(item.get('unit_price', 0)))
            vat_rate = Decimal(str(item.get('vat_rate', 0)))

            line_total = quantity * unit_price
            line_vat = line_total * (vat_rate / Decimal('100'))
            line_total_with_vat = line_total + line_vat

            calculated_items.append({
                'line_total': str(line_total.quantize(Decimal('0.01'))),
                'line_vat': str(line_vat.quantize(Decimal('0.01'))),
                'line_total_with_vat': str(line_total_with_vat.quantize(Decimal('0.01')))
            })

            subtotal += line_total
            tax_amount += line_vat
            total += line_total_with_vat

        # Apply global tax rate to the subtotal if needed
        if tax_rate > 0:
            tax_amount = subtotal * (tax_rate / Decimal('100'))
            total = subtotal + tax_amount

        return JsonResponse({
            'success': True,
            'subtotal': str(subtotal.quantize(Decimal('0.01'))),
            'tax_amount': str(tax_amount.quantize(Decimal('0.01'))),
            'total': str(total.quantize(Decimal('0.01'))),
            'items': calculated_items
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
