import uuid
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext as _
import logging
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.conf import settings
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Q
from xhtml2pdf import pisa
from io import BytesIO

# Set up logging
logger = logging.getLogger(__name__)

from .models import Invoice, InvoiceItem
from .forms import InvoiceForm, InvoiceItemFormSet
from accounts.models import CompanyProfile
from .payments import generate_pay_by_square

class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'invoices/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Invoice.objects.select_related('client').order_by('-issue_date', '-created_at')
        
        # Filter by status if provided
        status = self.request.GET.get('status')
        if status in ['draft', 'sent', 'paid', 'overdue']:
            if status == 'overdue':
                from django.utils import timezone
                queryset = queryset.filter(due_date__lt=timezone.now().date(), status__in=['draft', 'sent'])
            else:
                queryset = queryset.filter(status=status)
                
        # Filter by client if provided
        client_id = self.request.GET.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(client__name__icontains=search_query) |
                Q(notes__icontains=search_query)
            )
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all invoices for stats
        all_invoices = Invoice.objects.all()
        
        # Calculate statistics
        context.update({
            'total_invoices': all_invoices.count(),
            'total_paid': sum(inv.total_amount for inv in all_invoices.filter(status='paid')),
            'total_overdue': sum(
                inv.total_amount for inv in all_invoices.filter(
                    due_date__lt=timezone.now().date(),
                    status__in=['draft', 'sent']
                )
            ),
            'status_filter': self.request.GET.get('status', ''),
            'search_query': self.request.GET.get('q', ''),
        })
        
        # Add clients for filter dropdown if needed
        if 'client' in self.request.GET:
            from clients.models import Client
            context['selected_client'] = self.request.GET['client']
            context['clients'] = Client.objects.all().order_by('name')
            
        return context

class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'invoices/invoice_detail.html'
    context_object_name = 'invoice'
    
    def get_context_data(self, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        context = super().get_context_data(**kwargs)
        invoice = self.get_object()
        
        # Debug logging
        logger.info(f"Current user: {self.request.user}")
        logger.info(f"User has company_profile: {hasattr(self.request.user, 'company_profile')}")
        
        # Add company profile (issuer) information
        if hasattr(self.request.user, 'company_profile'):
            company = self.request.user.company_profile
            logger.info(f"Company profile data: {company.__dict__}")
            
            issuer_data = {
                'issuer_name': company.company_name,
                'issuer_address': f"{company.address_line1}\n{company.address_line2}" if company.address_line2 else company.address_line1,
                'issuer_city': company.city,
                'issuer_zip_code': company.postal_code,
                'issuer_country': company.country,
                'issuer_vat_id': company.tax_id,
            }
            logger.info(f"Issuer data being added to context: {issuer_data}")
            context.update(issuer_data)
            
        # Add debug information to the template
        context['debug_info'] = {
            'user': str(self.request.user),
            'has_company_profile': hasattr(self.request.user, 'company_profile'),
            'context_keys': list(context.keys())
        }
        
        # Generate Pay by Square data
        if invoice.status != 'paid':
            pay_by_square = generate_pay_by_square(invoice)
            context.update({
                'pay_by_square': pay_by_square,
                'show_payment': True
            })
        return context

class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    
    def generate_invoice_number(self):
        """Generate a unique invoice number using the current year and a sequence number."""
        from django.utils import timezone
        
        # Get the current year
        current_year = timezone.now().year
        
        # Get the last invoice number for this year
        last_invoice = Invoice.objects.filter(
            invoice_number__startswith=str(current_year)
        ).order_by('-invoice_number').first()
        
        if last_invoice:
            # Extract sequence number from last invoice
            sequence = int(last_invoice.invoice_number.split('-')[1]) + 1
        else:
            sequence = 1
        
        # Format the invoice number as YYYY-NNNN
        return f"{current_year}-{sequence:04d}"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the formset using our helper method
        if not hasattr(self, 'formset'):
            self.formset = self.get_formset()
        
        # Don't add extra forms by default
        self.formset.extra = 0
        
        # Add formset to the context
        context['formset'] = self.formset
        return context
    
    def get_form_kwargs(self):
        """Add the request user and formset to the form kwargs"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        
        # Always get the formset, not just for POST requests
        # This ensures the formset is available during validation
        if not hasattr(self, 'formset'):
            self.formset = self.get_formset()
            
        kwargs['items_formset'] = self.formset
        return kwargs
        
    def get_formset(self):
        """Helper method to get the formset with proper instance and data"""
        # For create view, instance will be None
        instance = self.object if hasattr(self, 'object') else None
        
        # Determine if this is a POST request
        if self.request.method == 'POST':
            formset = InvoiceItemFormSet(
                self.request.POST,
                instance=instance,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
        else:
            # For GET requests, initialize with one empty form
            formset = InvoiceItemFormSet(
                instance=instance,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
            
            # Don't add extra forms by default (the formset already includes one form)
            formset.extra = 0
        
        return formset
        
    def form_valid(self, form):
        # Check if the form was actually submitted
        if 'form_submitted' not in self.request.POST:
            return self.form_invalid(form)
        
        # Get the formset
        items_formset = self.get_formset()
        
        # Debug: Log form data
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Form data: {form.data}")
        logger.info(f"Form cleaned_data: {form.cleaned_data}")
        
        # Ensure client is set from form data
        client = None
        try:
            # First try to get client from cleaned_data
            if 'client' in form.cleaned_data and form.cleaned_data['client']:
                client = form.cleaned_data['client']
                form.instance.client = client
            # If not in cleaned_data, try to get from form data
            elif 'client' in form.data and form.data['client']:
                from clients.models import Client
                try:
                    client = Client.objects.get(pk=form.data['client'])
                    form.instance.client = client
                    # Also update cleaned_data to ensure it's available for future use
                    form.cleaned_data['client'] = client
                except (Client.DoesNotExist, ValueError, TypeError) as e:
                    logger.error(f"Client lookup error: {e}")
                    form.add_error('client', 'Please select a valid client.')
                    return self.form_invalid(form)
            
            # If we still don't have a client, try to get it from the instance
            if not hasattr(form.instance, 'client') or not form.instance.client:
                if hasattr(self, 'object') and self.object and hasattr(self.object, 'client'):
                    form.instance.client = self.object.client
            
            # Validate the formset
            if items_formset is None:
                form.add_error(None, 'No invoice items provided.')
                return self.form_invalid(form)
                
            # Set the instance for the formset
            items_formset.instance = form.instance
            
            # Check if formset is valid
            if not items_formset.is_valid():
                logger.error("Formset validation errors: %s", items_formset.errors)
                # Add formset errors to the form
                for error in items_formset.non_form_errors():
                    form.add_error(None, error)
                # Add field errors
                for i, form_in_formset in enumerate(items_formset):
                    for field, errors in form_in_formset.errors.items():
                        if field != 'DELETE':  # Skip DELETE field errors
                            for error in errors:
                                form.add_error(None, f"Item {i+1}, {field}: {error}")
                return self.form_invalid(form)
            
            # If we get here, both form and formset are valid
            # Save the form instance which will also save the formset
            self.object = form.save(commit=False)
            
            # Set the user if this is a new invoice
            if not hasattr(self.object, 'created_by') or not self.object.created_by:
                self.object.created_by = self.request.user
            
            # Set the invoice number if this is a new invoice
            if not self.object.invoice_number:
                self.object.invoice_number = self.generate_invoice_number()
            
            # Save the invoice (this will also save the formset via the form's save method)
            self.object.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            # Update totals
            self.object.update_totals(save=True)
            
            # Log success
            logger.info(f"Successfully saved invoice {self.object.id}")
            
            messages.success(self.request, 'Invoice saved successfully.')
            return super().form_valid(form)
            
        except Exception as e:
            logger.error(f"Error saving invoice: {str(e)}", exc_info=True)
            form.add_error(None, f'An error occurred while saving the invoice: {str(e)}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submission with better error handling."""
        # Log form errors for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Form errors: {form.errors}")
        
        # Get the formset from the form or create a new one
        items_formset = getattr(form, 'items_formset', None)
        if items_formset is None:
            items_formset = self.get_formset()
            for field_name, value in form.cleaned_data.items():
                # Safely handle client field
                if field_name == 'client' and value is not None:
                    try:
                        logger.error(f"  client: {value.id} ({value.__class__.__name__})")
                    except Exception as e:
                        logger.error(f"  client: Error getting client info: {str(e)}")
                else:
                    logger.error(f"  {field_name}: {value} ({type(value)})")
        
        # Log formset errors if they exist
        if hasattr(form, 'items_formset') and hasattr(form.items_formset, 'forms'):
            logger.error("=== Formset Errors ===")
            for i, form_in_formset in enumerate(form.items_formset.forms):
                if hasattr(form_in_formset, 'errors') and form_in_formset.errors:
                    logger.error(f"Form {i} errors: {form_in_formset.errors}")
            
            if hasattr(form.items_formset, 'non_form_errors'):
                logger.error(f"Formset non-form errors: {form.items_formset.non_form_errors()}")
            
            # Log formset data for debugging
            logger.error("Formset data:")
            for i, form_in_formset in enumerate(form.items_formset.forms):
                if hasattr(form_in_formset, 'data'):
                    logger.error(f"  Form {i} data: {form_in_formset.data}")
                elif hasattr(form_in_formset, 'cleaned_data'):
                    logger.error(f"  Form {i} cleaned_data: {form_in_formset.cleaned_data}")
                else:
                    logger.error(f"  Form {i}: No data or cleaned_data available")
                logger.error(f"  Form {i} cleaned_data: {getattr(form_in_formset, 'cleaned_data', {})}")
        
        # Ensure all form errors are properly passed to the template
        if not form.errors and not form.non_field_errors():
            if hasattr(form, 'items_formset') and form.items_formset.non_form_errors():
                for error in form.items_formset.non_form_errors():
                    form.add_error(None, error)
            else:
                form.add_error(None, 'An unknown error occurred. Please check the form and try again.')
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('invoices:detail', kwargs={'pk': self.object.pk})

class InvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoices/invoice_form.html'
    
    def get_formset(self):
        """Helper method to get the formset with proper instance and data"""
        instance = self.get_object()
        
        if self.request.method == 'POST':
            formset = InvoiceItemFormSet(
                self.request.POST,
                instance=instance,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
        else:
            formset = InvoiceItemFormSet(
                instance=instance,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
            
        return formset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get or create the formset
        if not hasattr(self, 'formset'):
            self.formset = self.get_formset()
        
        # For new invoices, ensure at least one empty form is shown
        if not self.object or not self.object.pk:
            self.formset.extra = 1
        else:
            self.formset.extra = 0
        
        # Add formset to the context
        context['formset'] = self.formset
        return context
    
    def _process_form_with_formset(self, form, formset):
        """
        Process the form and formset after initial validation.
        This method is called from form_valid after basic validation passes.
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Set the client on the form's instance
            if 'client' in form.cleaned_data and form.cleaned_data['client']:
                form.instance.client = form.cleaned_data['client']
            
            # Save the form to get an instance (but don't commit to DB yet)
            self.object = form.save(commit=False)
            
            # Process the form data to remove empty forms
            post_data = self.request.POST.copy()
            total_forms = int(post_data.get('items-TOTAL_FORMS', 0))
            
            # Find which forms have data
            valid_forms = []
            for i in range(total_forms):
                has_data = any(
                    post_data.get(f'items-{i}-{field}') 
                    for field in ['description', 'quantity', 'unit_price', 'vat_rate']
                )
                if has_data:
                    valid_forms.append(i)
            
            # Update the form count
            post_data['items-TOTAL_FORMS'] = str(len(valid_forms))
            
            # Create a new formset with the cleaned data
            formset = type(formset)(
                post_data,
                instance=self.object,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
            
            # Check if formset is valid
            if not formset.is_valid():
                logger.error("Formset validation errors: %s", formset.errors)
                for error in formset.errors:
                    if error:
                        form.add_error(None, f'Error in item: {error}')
                return self.form_invalid(form)
            
            # Check if there's at least one non-deleted form with data
            has_valid_forms = False
            for form_in_formset in formset:
                # Skip deleted forms
                if form_in_formset.cleaned_data.get('DELETE'):
                    continue
                    
                # Check if form has any data
                form_data = {k: v for k, v in form_in_formset.cleaned_data.items() 
                           if k not in ('id', 'DELETE') and v not in (None, '', 0, '0')}
                
                if form_data:  # If form has any data
                    has_valid_forms = True
                    break
            
            if not has_valid_forms:
                form.add_error(None, 'At least one invoice item is required.')
                return self.form_invalid(form)
            
            # If we got this far, save everything in a transaction
            with transaction.atomic():
                # Save the main form first
                self.object.save()
                
                # Now save the formset
                formset.instance = self.object
                formset.save()
                
                messages.success(self.request, 'Invoice updated successfully!')
                return super().form_valid(form)
                
        except Exception as e:
            logger.exception("Error processing form with formset")
            form.add_error(None, f'An error occurred while saving the invoice: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # Log form errors for debugging
        import logging
        logger = logging.getLogger(__name__)
        
        # Log form errors if they exist
        if hasattr(form, 'errors'):
            logger.error("Form errors: %s", form.errors)
        else:
            logger.error("Form is invalid but no errors attribute found")
        
        # Log formset errors if available
        if hasattr(form, 'items_formset') and form.items_formset is not None:
            try:
                if hasattr(form.items_formset, 'errors'):
                    logger.error("Formset errors: %s", form.items_formset.errors)
                else:
                    logger.error("Formset has no errors attribute")
            except Exception as e:
                logger.error("Error accessing formset errors: %s", str(e))
        else:
            logger.warning("No formset available in form_invalid")
        
        # Get the formset from the context if not already on the form
        if not hasattr(form, 'items_formset') or form.items_formset is None:
            try:
                context = self.get_context_data()
                if 'formset' in context:
                    form.items_formset = context['formset']
                    logger.info("Added formset from context to form")
            except Exception as e:
                logger.error("Error getting formset from context: %s", str(e))
        
        return super().form_invalid(form)
    
    def form_valid(self, form):
        """
        Handle valid form submission.
        """
        # Check if the form was actually submitted
        if 'form_submitted' not in self.request.POST:
            return self.form_invalid(form)
            
        try:
            # Get the formset from context data
            context = self.get_context_data()
            formset = context.get('formset')
            
            if formset is None:
                raise ValueError("Formset not found in context")
            
            # Store the formset on the form for use in form_invalid if needed
            form.items_formset = formset
            
            # Get the current version from the form for optimistic locking
            current_version = form.cleaned_data.get('version') if form.cleaned_data else None
            if current_version is not None and hasattr(self, 'object') and self.object is not None:
                if str(self.object.version) != str(current_version):
                    form.add_error(None, 'This invoice has been modified by another user. Please refresh and try again.')
                    return self.form_invalid(form)
            
            # Process the form data to remove empty forms
            post_data = self.request.POST.copy()
            total_forms = int(post_data.get('items-TOTAL_FORMS', 0))
            
            # Find which forms have data
            valid_forms = []
            for i in range(total_forms):
                has_data = any(
                    post_data.get(f'items-{i}-{field}') 
                    for field in ['description', 'quantity', 'unit_price', 'vat_rate']
                )
                if has_data:
                    valid_forms.append(i)
            
            # Update the form count
            post_data['items-TOTAL_FORMS'] = str(len(valid_forms))
            
            # Create a new formset with the cleaned data
            formset = type(formset)(
                post_data,
                instance=form.instance,
                prefix='items',
                form_kwargs={'user': self.request.user}
            )
            
            # Validate the formset
            if not formset.is_valid():
                logger.error("Formset validation errors: %s", formset.errors)
                for error in formset.errors:
                    if error:
                        form.add_error(None, f'Error in item: {error}')
                return self.form_invalid(form)
            
            # Check if there's at least one non-deleted form with data
            has_valid_forms = False
            for form_in_formset in formset:
                # Skip deleted forms
                if form_in_formset.cleaned_data.get('DELETE'):
                    continue
                    
                # Check if form has any data
                form_data = {k: v for k, v in form_in_formset.cleaned_data.items() 
                            if k not in ('id', 'DELETE') and v not in (None, '', 0, '0')}
                
                if form_data:  # If form has any data
                    has_valid_forms = True
                    break
            
            if not has_valid_forms:
                form.add_error(None, 'At least one invoice item is required.')
                return self.form_invalid(form)
            
            # If we got this far, save everything in a transaction
            with transaction.atomic():
                # Save the main form first
                self.object = form.save(commit=False)
                self.object.save()
                
                # Now save the formset
                formset.instance = self.object
                formset.save()
                
                # Update the invoice totals
                self.object.update_totals()
                
                messages.success(self.request, 'Invoice updated successfully!')
                return super().form_valid(form)
                
        except Exception as e:
            # Log the error and add a user-friendly message
            logger = logging.getLogger(__name__)
            logger.error("Error in form_valid: %s", str(e), exc_info=True)
            form.add_error(None, f'An error occurred while processing the form: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('invoices:detail', kwargs={'pk': self.object.pk})

class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoices/invoice_confirm_delete.html'
    success_url = reverse_lazy('invoices:list')

def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    template_path = 'invoices/invoice_pdf.html'
    
    # Debug information
    print("\n=== DEBUG: Invoice PDF Generation ===")
    print(f"User: {request.user.username}")
    
    # Get the company profile for the logged-in user
    company_profile = None
    try:
        company_profile = request.user.company_profile
        print(f"Found company profile: {company_profile}")
        print(f"Company name: {getattr(company_profile, 'company_name', 'Not set')}")
    except CompanyProfile.DoesNotExist:
        print("No company profile found for user")
    except Exception as e:
        print(f"Error getting company profile: {str(e)}")
    
    # For debugging, let's try to get any company profile
    if not company_profile:
        try:
            company_profile = CompanyProfile.objects.first()
            print(f"Using first available company profile: {company_profile}")
        except Exception as e:
            print(f"Error getting any company profile: {str(e)}")
    
    # Generate payment information
    payment_info = {
        'account_number': getattr(company_profile, 'bank_account', 'SK1234567890') if company_profile else 'SK1234567890',
        'amount': float(invoice.total_amount or 0),
        'currency': 'EUR',
        'vs': invoice.invoice_number,
        'message': f'Platba za faktúru {invoice.invoice_number}',
        'has_bank_info': bool(company_profile and hasattr(company_profile, 'bank_account') and getattr(company_profile, 'bank_account', None))
    }
    
    # Generate Pay by Square data if invoice is not paid
    pay_by_square = None
    if invoice.status != 'paid':
        pay_by_square = generate_pay_by_square(invoice)
    
    context = {
        'invoice': invoice,
        'company': company_profile,
        'payment': payment_info,
        'pay_by_square': pay_by_square,
        'show_payment': invoice.status != 'paid',
        'debug': {
            'has_company_profile': hasattr(request.user, 'company_profile'),
            'company_profile_exists': company_profile is not None,
            'user': request.user.username,
        }
    }
    
    print(f"Context company: {context.get('company')}")
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="invoice_{invoice.invoice_number}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context, request)
    
    # Print the first 500 chars of the rendered HTML for debugging
    print("\n=== Rendered HTML (first 500 chars) ===")
    print(html[:500])
    
    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        print(f"Error generating PDF: {pisa_status.err}")
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response
