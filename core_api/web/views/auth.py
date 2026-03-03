from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from ..forms import OrgRegisterForm, LoginForm
from users.models import CustomUser
from api.models import OrgRegistrationToken


def login_view(request):
    """Public login page."""
    if request.user.is_authenticated:
        return redirect('web:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Try username first
            user = authenticate(request, username=username_or_email, password=password)
            if not user:
                # Try email
                try:
                    user_obj = CustomUser.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except CustomUser.DoesNotExist:
                    pass

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect('web:home')
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'web/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('web:home')


def register_view(request):
    """Org registration using a token."""
    if request.user.is_authenticated:
        return redirect('web:home')

    if request.method == 'POST':
        form = OrgRegisterForm(request.POST)
        if form.is_valid():
            token_val = form.cleaned_data['token']
            org_name = form.cleaned_data['org_name']
            admin_name = form.cleaned_data['admin_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            # Token validation already happened in form.clean_token
            try:
                from django.db import transaction
                token_val = form.cleaned_data['token']
                token_obj = OrgRegistrationToken.objects.get(token=token_val)

                if not token_obj.is_valid:
                    messages.error(request, "This token has expired or is already used.")
                    return render(request, 'web/auth/register.html', {'form': form})

                with transaction.atomic():
                    # 1. Create User first (organisation=None is already allowed)
                    from api.models import Organisation
                    user = CustomUser.objects.create_user(
                        username=admin_name,
                        email=email,
                        password=password,
                        role='admin',
                        organisation=None
                    )

                    # 2. Create Organisation with the user as admin (admin is NOT nullable)
                    organisation = Organisation.objects.create(
                        name=org_name,
                        admin=user
                    )

                    # 3. Link user to the created organisation
                    user.organisation = organisation
                    user.save()

                    # 4. Mark token as used
                    token_obj.used = True
                    token_obj.save()

                login(request, user)
                messages.success(request, f"Organisation '{org_name}' registered successfully.")
                return redirect('web:org_panel')

            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
    else:
        # Check if URL has ?token=...
        initial = {}
        token_param = request.GET.get('token')
        if token_param:
            try:
                token_obj = OrgRegistrationToken.objects.get(token=token_param, used=False)
                initial['token'] = token_obj.token
                if token_obj.organisation_name:
                    initial['org_name'] = token_obj.organisation_name
            except OrgRegistrationToken.DoesNotExist:
                messages.error(request, "Invalid or expired token link.")
        form = OrgRegisterForm(initial=initial)

    return render(request, 'web/auth/register.html', {'form': form})
