from django.contrib.auth.models import AbstractUser, Group, Permission
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.timezone import now
import random

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100, blank=True, null=True)
    provincia = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.provincia} - {self.direccion}"

class CustomUser(AbstractUser):
    address = models.CharField(max_length=255, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sucursal = models.ForeignKey('Sucursal', null=True, blank=True, on_delete=models.SET_NULL)
    can_change_sucursal = models.BooleanField(default=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    alias = models.CharField(max_length=20, unique=True, blank=True, null=True)
    cbu = models.CharField(max_length=22, unique=True, blank=True, null=True)

    groups = models.ManyToManyField(Group, related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_set", blank=True)

    def generate_alias(self):
        """Genera un alias aleatorio para el usuario"""
        return f"USER{random.randint(100000, 999999)}"

    def generate_cbu(self):
        """Genera un CBU aleatorio de 22 dígitos"""
        return f"{random.randint(1000000000000000000000, 9999999999999999999999)}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not hasattr(self, 'userprofile'):
            UserProfile.objects.create(user=self)
        if not self.alias:
            self.alias = self.generate_alias()
        if not self.cbu:
            self.cbu = self.generate_cbu()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Loan(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=255, default="Sin motivo")
    comentario = models.TextField(blank=True, null=True)
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    aprobado = models.BooleanField(default=False)
    fecha_aprobacion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.monto} - {'Aprobado' if self.aprobado else 'Rechazado'}"

class DebitCard(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="debit_cards")
    numero = models.CharField(max_length=16, unique=True)
    tipo = models.CharField(max_length=50, default="Débito")
    fecha_emision = models.DateTimeField(auto_now_add=True)
    fecha_vencimiento = models.DateField()
    cvv = models.CharField(max_length=3, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = get_random_string(16, allowed_chars='0123456789')
        if not self.cvv:
            self.cvv = str(random.randint(100, 999))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo} - {self.numero}"

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, default="")
    email = models.EmailField()
    dni = models.CharField(max_length=20)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        return self.user.username

class Transfer(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sent_transfers")
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="received_transfers")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="Pendiente")
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        sender_profile = self.sender.userprofile
        receiver_profile = self.receiver.userprofile
        return f"Transferencia de {sender_profile.first_name} {sender_profile.last_name} a {receiver_profile.first_name} {receiver_profile.last_name} por {self.amount} USD"

    def to_dict(self):
        sender_profile = self.sender.userprofile
        receiver_profile = self.receiver.userprofile
        return {
            'sender': f"{sender_profile.first_name} {sender_profile.last_name}",
            'receiver': f"{receiver_profile.first_name} {receiver_profile.last_name}",
            'amount': str(self.amount),
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'description': self.description or 'Sin descripción',
        }