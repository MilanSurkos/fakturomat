from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def test_company_profile(request):
    company_profile = None
    if hasattr(request.user, 'company_profile'):
        company_profile = request.user.company_profile
    
    context = {
        'company': company_profile,
        'user': request.user,
        'has_company_profile': hasattr(request.user, 'company_profile'),
    }
    return render(request, 'invoices/test_company.html', context)
