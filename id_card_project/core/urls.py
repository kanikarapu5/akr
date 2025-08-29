from django.urls import path
from .views import (
    PartnerSignUpView, InstitutionSignUpView, referral_student_add,
    institution_dashboard, partner_dashboard, admin_dashboard, export_data,
    StudentUpdateView, StudentDeleteView, student_add_by_institution,
    user_list, UserCreateView, UserUpdateView, UserDeleteView, admin_reset_password,
    home
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', home, name='home'),
    path('admin/users/', user_list, name='user_list'),
    path('admin/users/create/', UserCreateView.as_view(), name='user_create'),
    path('admin/users/<int:pk>/update/', UserUpdateView.as_view(), name='user_update'),
    path('admin/users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),
    path('admin/users/<int:pk>/reset-password/', admin_reset_password, name='admin_reset_password'),
    path('dashboard/admin/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/institution/', institution_dashboard, name='institution_dashboard'),
    path('dashboard/partner/', partner_dashboard, name='partner_dashboard'),
    path('export/', export_data, name='export_data'),
    path('student/add/', student_add_by_institution, name='student_add'),
    path('student/<int:pk>/update/', StudentUpdateView.as_view(), name='student_update'),
    path('student/<int:pk>/delete/', StudentDeleteView.as_view(), name='student_delete'),
    path('referral/<uuid:referral_code>/', referral_student_add, name='referral_student_add'),
    path('signup/partner/', PartnerSignUpView.as_view(), name='partner_signup'),
    path('signup/institution/', InstitutionSignUpView.as_view(), name='institution_signup'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
