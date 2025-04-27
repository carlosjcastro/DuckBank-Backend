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

# Esto permite que cada vez que se cree un usuario, se cree una tarjeta de débito
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
# Esto permite que cada vez que se cree un usuario, se cree un perfil de usuario
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        
@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
    
# Esto permite que cada vez que se cree un usuario, se le asigne un saldo aleatorio entre 40,000 y 500,000
@receiver(post_save, sender=CustomUser)
def assign_random_balance(sender, instance, created, **kwargs):
    if created:
        random_balance = random.uniform(40000, 500000)
        instance.balance = round(random_balance, 2)
        instance.save()
        
@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# @receiver(post_save, sender=CustomUser)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         user_profile = UserProfile.objects.create(user=instance)
#         default_image_path = os.path.join(settings.BASE_DIR, 'media', 'profile_images', 'duck_profile.jpeg')
#         if os.path.exists(default_image_path):
#             with open(default_image_path, 'rb') as img_file:
#                 user_profile.profile_image.save('duck_profile.jpeg', File(img_file))
#             user_profile.save()