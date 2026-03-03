from django.shortcuts import render, redirect
from django.contrib import messages
from ..forms import AddEmployeeForm, CameraStreamForm
from ..decorators import org_admin_required
from api.models import CameraStream


@org_admin_required
def org_panel_view(request):
    """View employees and org stats."""
    org = request.user.organisation
    employees = org.employees.all()
    context = {
        'organisation': org,
        'employees': employees
    }
    return render(request, 'web/org/org_panel.html', context)


@org_admin_required
def add_employee_view(request):
    if request.method == 'POST':
        form = AddEmployeeForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.organisation = request.user.organisation
            user.save()
            messages.success(request, f"Employee {user.username} added.")
            return redirect('web:org_panel')
    else:
        form = AddEmployeeForm()
    return render(request, 'web/org/add_employee.html', {'form': form})


@org_admin_required
def camera_manage_view(request):
    org = request.user.organisation
    cameras = org.camera_streams.all()
    if request.method == 'POST':
        form = CameraStreamForm(request.POST)
        if form.is_valid():
            camera = form.save(commit=False)
            camera.organisation = org
            camera.save()
            messages.success(request, f"Camera '{camera.name}' added successfully.")
            return redirect('web:camera_manage')
    else:
        form = CameraStreamForm()

    return render(request, 'web/cameras/manage.html', {
        'form': form,
        'cameras': cameras
    })


@org_admin_required
def camera_delete_view(request, pk):
    org = request.user.organisation
    try:
        camera = org.camera_streams.get(pk=pk)
        camera.delete()
        messages.success(request, "Camera deleted.")
    except CameraStream.DoesNotExist:
        messages.error(request, "Camera not found.")
    return redirect('web:camera_manage')
