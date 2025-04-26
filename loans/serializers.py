from rest_framework import serializers, generics
from .models import CustomUser, Loan, DebitCard, Sucursal, UserProfile, Transfer
import datetime

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['provincia', 'direccion']

class UserSerializer(serializers.ModelSerializer):
    sucursal = SucursalSerializer(read_only=True)
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'address', 'balance', 'sucursal', 'profile_image']
        extra_kwargs = {
            'address': {'required': False},
            'profile_image': {'required': False}
        }

class LoanSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['id', 'monto', 'motivo', 'comentario', 'status', 'fecha_solicitud']

    def get_status(self, obj):
        return 'Aprobado' if obj.aprobado else 'Rechazado'
                
class DebitCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = DebitCard
        fields = ['id', 'numero', 'tipo', 'fecha_emision', 'fecha_vencimiento', 'cvv']
        
class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = ['id', 'provincia', 'direccion']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    sucursal = serializers.CharField(source='user.sucursal.nombre', read_only=True)
    balance = serializers.DecimalField(source='user.balance', max_digits=12, decimal_places=2, read_only=True)
    alias = serializers.CharField(source='user.alias', read_only=True)
    cbu = serializers.CharField(source='user.cbu', read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name', 'dni', 
            'profile_image', 'sucursal', 'balance', 'alias', 'cbu'
        ]
        
# class ProfileImageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomUser
#         fields = ['profile_image']

class TransferSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    receiver_name = serializers.SerializerMethodField()

    class Meta:
        model = Transfer
        fields = ['id', 'sender_name', 'receiver_name', 'amount', 'timestamp', 'description', 'status']

    def get_sender_name(self, obj):
        return f"{obj.sender.userprofile.first_name} {obj.sender.userprofile.last_name}"

    def get_receiver_name(self, obj):
        return f"{obj.receiver.userprofile.first_name} {obj.receiver.userprofile.last_name}"
