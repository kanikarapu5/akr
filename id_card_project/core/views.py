import base64
import uuid
import zipfile
import io
import csv
import os
from django.http import HttpResponse
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from .forms import PartnerSignUpForm, InstitutionSignUpForm, StudentForm
from .models import User, Partner, Institution, Student

class PartnerSignUpView(CreateView):
    model = User
    form_class = PartnerSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'partner'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.role = 'PARTNER'
        user.save()
        Partner.objects.create(user=user)
        return redirect('login')

class InstitutionSignUpView(CreateView):
    model = User
    form_class = InstitutionSignUpForm
    template_name = 'registration/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'institution'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.role = 'INSTITUTION'
        user.save()
        Institution.objects.create(user=user)
        return redirect('login')

class StudentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'student_form.html'
    success_url = reverse_lazy('institution_dashboard')

    def test_func(self):
        student = self.get_object()
        return self.request.user.role == 'INSTITUTION' and student.institution == self.request.user.institution

class StudentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Student
    template_name = 'student_confirm_delete.html'
    success_url = reverse_lazy('institution_dashboard')

    def test_func(self):
        student = self.get_object()
        return self.request.user.role == 'INSTITUTION' and student.institution == self.request.user.institution

def referral_student_add(request, referral_code):
    partner = get_object_or_404(Partner, referral_code=referral_code)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.partner = partner

            photo_data = request.POST.get('photo_data')
            if photo_data:
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')
                student.photo = data

            student.save()
            return redirect('login') # Or a success page
    else:
        form = StudentForm()
    return render(request, 'student_form.html', {'form': form, 'partner': partner})

@login_required
def student_add_by_institution(request):
    if request.user.role != 'INSTITUTION':
        return redirect('login')

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            student.institution = request.user.institution

            photo_data = request.POST.get('photo_data')
            if photo_data:
                format, imgstr = photo_data.split(';base64,')
                ext = format.split('/')[-1]
                data = ContentFile(base64.b64decode(imgstr), name=f'{uuid.uuid4()}.{ext}')
                student.photo = data

            student.save()
            return redirect('institution_dashboard')
    else:
        form = StudentForm()
    return render(request, 'student_form.html', {'form': form})


@login_required
def institution_dashboard(request):
    if request.user.role != 'INSTITUTION':
        return redirect('login') # Or a custom access denied page

    students = Student.objects.filter(institution=request.user.institution)
    return render(request, 'institution_dashboard.html', {'students': students})

@login_required
def partner_dashboard(request):
    if request.user.role != 'PARTNER':
        return redirect('login')

    students = Student.objects.filter(partner=request.user.partner)

    referral_path = reverse('referral_student_add', kwargs={'referral_code': request.user.partner.referral_code})
    referral_link = request.build_absolute_uri(referral_path)

    context = {
        'students': students,
        'referral_link': referral_link,
    }
    return render(request, 'partner_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('login')
    return render(request, 'admin_dashboard.html')

@login_required
def export_data(request):
    export_format = request.GET.get('format', 'csv') # default to csv

    students = []
    if request.user.role == 'ADMIN':
        students = Student.objects.all()
    elif request.user.role == 'PARTNER':
        students = Student.objects.filter(partner=request.user.partner)
    else:
        return HttpResponse("Unauthorized", status=401)

    # Group students by class
    students_by_class = {}
    for student in students:
        class_name = student.class_name
        if class_name == 'Other':
            class_name = student.other_class if student.other_class else 'Other'

        if class_name not in students_by_class:
            students_by_class[class_name] = []
        students_by_class[class_name].append(student)

    # Create a zip file in memory
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zip_file:
        for class_name, students_in_class in students_by_class.items():

            if export_format == 'xlsx':
                # Create XLSX file in memory
                workbook = Workbook()
                worksheet = workbook.active
                worksheet.title = "Students"
                header = ['Unique ID', 'Student Name', "Father's Name", 'Class', 'Village', 'Mobile Number']
                worksheet.append(header)

                for student in students_in_class:
                    s_class = student.class_name
                    if s_class == 'Other':
                        s_class = student.other_class
                    worksheet.append([student.unique_id, student.student_name, student.father_name, s_class, student.village, student.mobile_number])

                    # Add photo to zip
                    if student.photo:
                        photo_path = student.photo.path
                        _, extension = os.path.splitext(student.photo.name)
                        photo_filename = f"{student.unique_id}{extension}"
                        zip_file.write(photo_path, f'{class_name}/Photos/{photo_filename}')

                # Save workbook to a buffer and add to zip
                excel_buffer = io.BytesIO()
                workbook.save(excel_buffer)
                excel_buffer.seek(0)
                zip_file.writestr(f'{class_name}/student_data.xlsx', excel_buffer.getvalue())

            else: # Default to CSV
                # Create CSV file in memory
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer)
                csv_writer.writerow(['Unique ID', 'Student Name', "Father's Name", 'Class', 'Village', 'Mobile Number'])

                for student in students_in_class:
                    s_class = student.class_name
                    if s_class == 'Other':
                        s_class = student.other_class
                    csv_writer.writerow([student.unique_id, student.student_name, student.father_name, s_class, student.village, student.mobile_number])

                    # Add photo to zip
                    if student.photo:
                        photo_path = student.photo.path
                        _, extension = os.path.splitext(student.photo.name)
                        photo_filename = f"{student.unique_id}{extension}"
                        zip_file.write(photo_path, f'{class_name}/Photos/{photo_filename}')

                # Add CSV to zip
                zip_file.writestr(f'{class_name}/student_data.csv', csv_buffer.getvalue())


    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="student_data.zip"'
    return response


from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .forms import PasswordResetForm
from django.shortcuts import render

def home(request):
    if request.user.is_authenticated:
        if request.user.role == 'ADMIN':
            return redirect('admin_dashboard')
        elif request.user.role == 'PARTNER':
            return redirect('partner_dashboard')
        elif request.user.role == 'INSTITUTION':
            return redirect('institution_dashboard')
    return render(request, 'home.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_reset_password(request, pk):
    user_to_reset = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            user_to_reset.set_password(form.cleaned_data['new_password'])
            user_to_reset.save()
            messages.success(request, f"Password for {user_to_reset.username} has been reset successfully.")
            return redirect('user_list')
    else:
        form = PasswordResetForm()
    return render(request, 'admin/password_reset_form.html', {'form': form, 'user_to_reset': user_to_reset})

def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@login_required
@admin_required
def user_list(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'admin/user_list.html', {'users': users})

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = PartnerSignUpForm # Using a generic form for creation
    template_name = 'admin/user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data.get('password'))
        user.save()
        if user.role == 'PARTNER':
            Partner.objects.create(user=user)
        elif user.role == 'INSTITUTION':
            Institution.objects.create(user=user)
        return redirect(self.success_url)

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ['username', 'first_name', 'last_name', 'email', 'role']
    template_name = 'admin/user_form.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'admin/user_confirm_delete.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser
