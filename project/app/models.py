from django.db import models

# Create your models here.
class User(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    def __repr__(self):
        return f"User object: {self.first_name} {self.last_name} {self.email} {self.password}"
    def __str__(self):
        return f"User object: {self.first_name} {self.last_name} {self.email} {self.password}"