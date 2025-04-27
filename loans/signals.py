from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from datetime import timedelta
import datetime
from django.utils.crypto import get_random_string
import random
import os
from django.conf import settings
from .models import DebitCard, CustomUser, UserProfile
from django.core.files import File

# Crear tarjeta de débito al registrar usuario
@receiver(post_save, sender=CustomUser)
def crear_tarjeta_debito(sender, instance, created, **kwargs):
    if created:
        fecha_vencimiento = now().date() + datetime.timedelta(days=365 * 5)
        numero_tarjeta = get_random_string(16, allowed_chars="0123456789")
        
        DebitCard.objects.create(
            user=instance,
            numero=numero_tarjeta,
            tipo="Débito",
            fecha_emision=now(),
            fecha_vencimiento=fecha_vencimiento,
        )

# Asignar saldo aleatorio al registrar usuario
@receiver(post_save, sender=CustomUser)
def assign_random_balance(sender, instance, created, **kwargs):
    if created:
        random_balance = random.uniform(40000, 500000)
        instance.balance = round(random_balance, 2)
        instance.save()

# Crear perfil de usuario al registrar usuario
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = UserProfile.objects.create(
            user=instance,
            dni=instance.dni,
            first_name=instance.first_name,
            last_name=instance.last_name,
            email=instance.email,
            profile_image=instance.profile_image,
        )
        # Poner imagen de perfil por defecto si no subió imagen
        if not instance.profile_image:
            default_image_path = os.path.join(settings.BASE_DIR, 'media', 'profile_images', 'duck_profile.jpeg')
            if os.path.exists(default_image_path):
                with open(default_image_path, 'rb') as img_file:
                    user_profile.profile_image.save('duck_profile.jpeg', File(img_file))
                user_profile.save()

# Guardar perfil automáticamente si se actualiza usuario
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
