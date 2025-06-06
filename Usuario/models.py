# Usuario/models.py

from django.db import models
from django.contrib.auth.models import User


# O Profile é o único modelo que pertence verdadeiramente ao app Usuario,
# pois ele estende diretamente o usuário.
class Profile(models.Model):
    usuario = models.OneToOneField(
        User, related_name="perfil", on_delete=models.CASCADE
    )
    vendedor = models.BooleanField(default=False)
    foto = models.ImageField(
        upload_to="uploads/fotos_perfil/",
        default="uploads/fotos_perfil/DefaultProfileImage.png",
    )
    bios = models.CharField(max_length=255, default="Olá, este é o meu Perfil!")

    mp_connected = models.BooleanField(default=False)
    mp_user_id = models.CharField(max_length=255, blank=True, null=True)
    mp_access_token = models.CharField(max_length=255, blank=True, null=True)
    mp_refresh_token = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.usuario.first_name
