from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.views.generic import CreateView, UpdateView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .forms import CustomUserCreationForm, UserProfileForm, CompanyProfileForm
from .models import CompanyProfile

class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('core:home')
    template_name = 'registration/register.html'
    
    def form_valid(self, form):
        # Save the user first
        response = super().form_valid(form)
        
        # Get the username and password
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        
        # Authenticate and login the user
        user = authenticate(
            username=username, 
            password=password
        )
        
        if user is not None:
            login(self.request, user)
            messages.success(
                self.request, 
                f'Welcome, {user.username}! Your account has been created successfully.'
            )
            
            # Send welcome email (you can implement this later)
            # send_welcome_email(user)
            
        return response
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create an Account'
        return context
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['use_required_attribute'] = False
        return kwargs


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'My Profile'
        context['active_tab'] = self.request.GET.get('tab', 'profile')
        
        try:
            # Try to get the company profile
            company_profile = CompanyProfile.objects.get(user=self.request.user)
        except CompanyProfile.DoesNotExist:
            # If it doesn't exist, create one
            company_profile = CompanyProfile.objects.create(user=self.request.user)
        
        # Initialize the form with the company profile
        if 'company_form' not in context:
            context['company_form'] = CompanyProfileForm(instance=company_profile)
        
        # Add password form if not already in context
        if 'password_form' not in context:
            context['password_form'] = PasswordChangeForm(user=self.request.user)
            
        # Debug information
        context['debug'] = {
            'user': self.request.user.username,
            'has_company_profile': hasattr(self.request.user, 'company_profile'),
            'company_form_fields': list(context.get('company_form', {}).fields.keys()) if 'company_form' in context else []
        }
        
        return context
        
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        print("\n=== DEBUG: Form Submission ===")
        print(f"POST data: {request.POST}")
        print(f"FILES data: {request.FILES}")
        
        # Check which form was submitted
        if 'update_company' in request.POST:
            print("Company form submitted")
            try:
                company_profile = CompanyProfile.objects.get(user=request.user)
                print(f"Found existing company profile: {company_profile}")
            except CompanyProfile.DoesNotExist:
                print("No company profile found, creating new one")
                company_profile = CompanyProfile(user=request.user)
                
            form = CompanyProfileForm(request.POST, request.FILES, instance=company_profile)
            print(f"Form is valid: {form.is_valid()}")
            if not form.is_valid():
                print(f"Form errors: {form.errors}")
            if form.is_valid():
                form.save()
                messages.success(request, 'Company information updated successfully.')
                return redirect('{}?tab=company'.format(reverse('accounts:profile')))
            else:
                # If form is invalid, we need to return the form with errors
                context = self.get_context_data()
                context['company_form'] = form
                context['active_tab'] = 'company'
                return self.render_to_response(context)
        else:
            # Default to UserProfileForm if not company form
            form = self.get_form()
            if form.is_valid():
                response = self.form_valid(form)
                messages.success(request, 'Profile updated successfully.')
                return response
            else:
                return self.form_invalid(form)
                
    def form_invalid(self, form):
        # Handle form validation errors
        context = self.get_context_data()
        if 'update_company' in self.request.POST:
            context['company_form'] = form
            context['active_tab'] = 'company'
        return self.render_to_response(context)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add form-control class to all fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class ChangePasswordView(LoginRequiredMixin, FormView):
    form_class = PasswordChangeForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Change Password'
        context['active_tab'] = 'password'
        # Add profile form to context
        context['form'] = UserProfileForm(instance=self.request.user)
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add form-control class to all fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)  # Important to keep the user logged in
        messages.success(self.request, 'Your password was successfully updated!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # If password change form is invalid, show the form with errors
        return self.render_to_response(self.get_context_data(password_form=form))
