from django.test import TestCase
from django.urls import reverse
from .models import User, Partner, Institution, Student

class UserModelTest(TestCase):
    def test_create_admin_user(self):
        user = User.objects.create_user(username='admin_user', password='password', role='ADMIN')
        self.assertEqual(user.role, 'ADMIN')
        self.assertTrue(user.check_password('password'))

    def test_create_partner_user(self):
        user = User.objects.create_user(username='partner_user', password='password', role='PARTNER')
        Partner.objects.create(user=user)
        self.assertEqual(user.role, 'PARTNER')
        self.assertIsNotNone(user.partner)
        self.assertTrue(user.check_password('password'))

    def test_create_institution_user(self):
        user = User.objects.create_user(username='institution_user', password='password', role='INSTITUTION')
        Institution.objects.create(user=user)
        self.assertEqual(user.role, 'INSTITUTION')
        self.assertIsNotNone(user.institution)
        self.assertTrue(user.check_password('password'))

class SignUpViewTests(TestCase):
    def test_partner_signup(self):
        data = {
            'first_name': 'Test',
            'last_name': 'Partner',
            'email': 'partner@test.com',
            'password': 'testpassword',
            'password2': 'testpassword',
        }
        response = self.client.post(reverse('partner_signup'), data=data)
        self.assertEqual(response.status_code, 302) # Redirects on success
        self.assertTrue(User.objects.filter(email='partner@test.com').exists())
        user = User.objects.get(email='partner@test.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertEqual(user.role, 'PARTNER')

    def test_institution_signup(self):
        data = {
            'username': 'testinstitution',
            'first_name': 'Test',
            'last_name': 'Institution',
            'email': 'institution@test.com',
            'password': 'testpassword',
            'password2': 'testpassword',
        }
        response = self.client.post(reverse('institution_signup'), data=data)
        self.assertEqual(response.status_code, 302) # Redirects on success
        self.assertTrue(User.objects.filter(email='institution@test.com').exists())
        user = User.objects.get(email='institution@test.com')
        self.assertTrue(user.check_password('testpassword'))
        self.assertEqual(user.role, 'INSTITUTION')

class DashboardViewTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser('admin', 'admin@test.com', 'password')

        self.partner_user = User.objects.create_user(username='partner', password='password', role='PARTNER')
        self.partner = Partner.objects.create(user=self.partner_user)

        self.institution_user = User.objects.create_user(username='institution', password='password', role='INSTITUTION')
        self.institution = Institution.objects.create(user=self.institution_user)

    def test_admin_dashboard_view(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_partner_dashboard_view(self):
        self.client.login(username='partner', password='password')
        response = self.client.get(reverse('partner_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_institution_dashboard_view(self):
        self.client.login(username='institution', password='password')
        response = self.client.get(reverse('institution_dashboard'))
        self.assertEqual(response.status_code, 200)

class ReferralSystemTest(TestCase):
    def setUp(self):
        self.partner_user = User.objects.create_user(username='partner_for_referral', password='password', role='PARTNER')
        self.partner = Partner.objects.create(user=self.partner_user)
        self.institution_user = User.objects.create_user(username='institution_for_referral', password='password', role='INSTITUTION')
        self.institution = Institution.objects.create(user=self.institution_user)

    def test_referral_link_works(self):
        response = self.client.get(reverse('referral_student_add', kwargs={'referral_code': self.partner.referral_code}))
        self.assertEqual(response.status_code, 200)

    def test_student_creation_via_referral(self):
        student_data = {
            'student_name': 'Test Student',
            'father_name': 'Test Father',
            'class_name': '1',
            'village': 'Test Village',
            'mobile_number': '1234567890',
            'institution': self.institution.pk,
        }
        self.client.post(reverse('referral_student_add', kwargs={'referral_code': self.partner.referral_code}), data=student_data)

        student = Student.objects.last()
        self.assertIsNotNone(student)
        self.assertEqual(student.student_name, 'Test Student')
        self.assertEqual(student.partner, self.partner)
