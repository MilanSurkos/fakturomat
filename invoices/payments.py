import segno
from datetime import datetime, timedelta
from decimal import Decimal

def generate_pay_by_square(invoice):
    """
    Generate Pay by Square data for an invoice.

    Args:
        invoice: Invoice instance

    Returns:
        dict: Contains 'qr_code' (SVG string) and 'payment_data' (string)
    """
    # Get payment amount in cents (minimum 1 EUR)
    amount = max(int(invoice.total_amount * 100), 100)  # At least 1 EUR

    # Format due date (default to 30 days from now if not set)
    due_date = invoice.due_date or (datetime.now().date() + timedelta(days=30))
    due_date_str = due_date.strftime('%Y%m%d')

    # Create payment data string according to Pay by Square specification
    payment_data = [
        '1',                    # Version
        '1',                    # Payment request
        '1',                    # Payment options (1 = priority, 2 = standard)
        str(amount),            # Amount in cents
        '978',                  # Currency code (EUR)
        '0',                    # Variable symbol
        '0',                    # Specific symbol
        '0',                    # Constant symbol
        due_date_str,           # Due date (YYYYMMDD)
        '0',                    # Payment note
        '1',                    # Country code (SK)
        '0',                    # IBAN
        '0',                    # SWIFT
        '0',                    # Bank account name
        '0',                    # Bank account address line 1
        '0',                    # Bank account address line 2
        invoice.invoice_number,  # Payment reference
        '0',                    # Payment note for recipient
        '0',                    # Payment type (0 = standard)
        '1.2.203.2.4.5.1'      # Pay by Square protocol version
    ]

    # Join with pipe and remove trailing zeros
    payment_string = '|'.join(payment_data).rstrip('|0') + '|'

    # Generate QR code as PNG and convert to base64
    import io
    import base64
    
    qr = segno.make(payment_string, micro=False)
    buffer = io.BytesIO()
    qr.save(buffer, kind='png', scale=4, border=1)
    
    # Convert to base64 for embedding in HTML
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('ascii')
    
    return {
        'qr_code': qr_base64,
        'payment_data': payment_string
    }
