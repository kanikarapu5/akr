import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("PARTNER", "Partner"),
        ("INSTITUTION", "Institution"),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Partner(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="partner")
    referral_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return self.user.username

class Institution(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name="institution")

    def __str__(self):
        return self.user.username

class Student(models.Model):
    CLASS_CHOICES = (
        ('Nursery', 'Nursery'),
        ('LKG', 'LKG'),
        ('UKG', 'UKG'),
        ('1', '1st'),
        ('2', '2nd'),
        ('3', '3rd'),
        ('4', '4th'),
        ('5', '5th'),
        ('6', '6th'),
        ('7', '7th'),
        ('8', '8th'),
        ('9', '9th'),
        ('10', '10th'),
        ('Other', 'Other'),
    )
    student_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=20, choices=CLASS_CHOICES)
    other_class = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=15)
    photo = models.ImageField(upload_to='student_photos/')
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE)
    partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, null=True, blank=True)
    unique_id = models.CharField(max_length=10, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            last_student = Student.objects.order_by('id').last()
            if last_student and last_student.unique_id:
                last_id = int(last_student.unique_id[1:])
                new_id = last_id + 1
                self.unique_id = f'S{new_id:04d}'
            else:
                self.unique_id = 'S0001'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.student_name
