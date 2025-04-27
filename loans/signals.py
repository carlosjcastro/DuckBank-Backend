from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.utils.crypto import get_random_string
from datetime import timedelta
import random
from .models import DebitCard, CustomUser, UserProfile

# Esto permite que cada vez que se cree un usuario, se cree una tarjeta de débito
@receiver(post_save, sender=CustomUser)
def crear_tarjeta_debito(sender, instance, created, **kwargs):
    if created:
        fecha_vencimiento = now().date() + timedelta(days=365 * 5)
        numero_tarjeta = get_random_string(16, allowed_chars="0123456789")
        
        DebitCard.objects.create(
            user=instance,
            numero=numero_tarjeta,
            tipo="Débito",
            fecha_emision=now(),
            fecha_vencimiento=fecha_vencimiento,
        )

# Esto permite que cada vez que se cree un usuario, se cree un perfil de usuario
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Solo crear el perfil si no existe
        if not UserProfile.objects.filter(user=instance).exists():
            user_profile = UserProfile.objects.create(user=instance)
            # Asignar alias y CBU si no existen
            if not user_profile.alias:
                user_profile.alias = user_profile.generate_alias()  # Método para generar el alias
            if not user_profile.cbu:
                user_profile.cbu = user_profile.generate_cbu()  # Método para generar el CBU
            user_profile.save()

# Esto permite que cada vez que se cree un usuario, se le asigne un saldo aleatorio entre 40,000 y 500,000
@receiver(post_save, sender=CustomUser)
def assign_random_balance(sender, instance, created, **kwargs):
    if created:
        random_balance = random.uniform(40000, 500000)
        instance.balance = round(random_balance, 2)
        instance.save()
