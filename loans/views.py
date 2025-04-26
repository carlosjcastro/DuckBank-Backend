from rest_framework import viewsets, permissions, generics
from .models import CustomUser, Loan, DebitCard, Sucursal, UserProfile, Transfer
import random
from datetime import datetime
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from .serializers import UserSerializer, LoanSerializer, DebitCardSerializer, SucursalSerializer, UserProfileSerializer, TransferSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, UntypedToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.views.decorators.csrf import csrf_exempt
import jwt
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import CustomUser
from rest_framework.permissions import IsAuthenticated, IsAdminUser

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
# Esto permite iniciar sesión en el Frontend luego de registrar un usuario
class LoginView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "username": user.username,
                    "email": user.email,
                }
            }, status=status.HTTP_200_OK)
        return Response({"detail": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)

# Esto permite registrar un usuario en el Frontend y Backend
class RegisterView(APIView):
    def post(self, request):
        username = request.data.get("usuario")
        password = request.data.get("password")
        dni = request.data.get("dni")

        if CustomUser.objects.filter(username=username).exists():
            return Response({"detail": "El nombre de usuario ya está en uso."}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(username=username, password=password)
        user.dni = dni
        user.save()

        UserProfile.objects.get_or_create(user=user)

        return Response({"detail": "Usuario creado exitosamente."}, status=status.HTTP_201_CREATED)
    
    # Esto permite validar el token en el Frontend
class ValidateTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            token = request.headers.get('Authorization').split()[1]
            UntypedToken(token)
            print("Token válido recibido")
            return Response({"detail": "Token válido"}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error al validar token: {str(e)}")
            return Response({"detail": "Token inválido"}, status=status.HTTP_401_UNAUTHORIZED)
     
# Esto permite solicitar un préstamo en el Frontend   
class SolicitarPrestamoView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        monto = request.data.get("monto")
        motivo = request.data.get("motivo")
        comentario = request.data.get("comentario", "")

        if not monto or not motivo:
            return Response({"detail": "El monto y el motivo son obligatorios."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            monto = float(monto)
        except ValueError:
            return Response({"detail": "El monto debe ser un número válido."}, status=status.HTTP_400_BAD_REQUEST)

        if monto > 1000000:
            return Response({"detail": "El monto excede el límite permitido."}, status=status.HTTP_400_BAD_REQUEST)

        loan = Loan.objects.create(
            user=user,
            monto=monto,
            motivo=motivo,
            comentario=comentario,
            aprobado=True,
            fecha_aprobacion=timezone.now()
        )

        serializer = LoanSerializer(loan)

        return Response({
            "status": "aprobado" if loan.aprobado else "rechazado",
            "monto": loan.monto,
            "fecha": loan.fecha_solicitud,
            "motivo": loan.motivo,
            "comentario": loan.comentario,
        }, status=status.HTTP_201_CREATED)

# Esto permite mostrar préstamos solicitados por el usuario en el Frontend
class ObtenerPrestamosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        prestamos = Loan.objects.filter(user=user)
        serializer = LoanSerializer(prestamos, many=True)
        return Response(serializer.data, status=200)

# Esto permite mostrar préstamos solicitados por el usuario en el Frontend
@api_view(['GET'])
def mis_prestamos(request):
    loans = Loan.objects.filter(user=request.user)
    loan_data = []

    for loan in loans:
        loan_info = {
            'id': loan.id,
            'monto': loan.monto,
            'motivo': loan.motivo,
            'comentario': loan.comentario or "Ninguno",
            'status': 'Aprobado' if loan.aprobado else 'Rechazado',
            'fecha_solicitud': loan.fecha_solicitud,
        }
        loan_data.append(loan_info)

    return Response(loan_data)

# Esto permite al usuario eliminar un préstamo
class EliminarPrestamoView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            prestamo = Loan.objects.get(id=pk, user=request.user)
        except Loan.DoesNotExist:
            return Response({"detail": "Préstamo no encontrado o no autorizado."}, status=status.HTTP_404_NOT_FOUND)

        prestamo.delete()
        return Response({"detail": "Préstamo eliminado correctamente."}, status=status.HTTP_204_NO_CONTENT)

# Esto permite mostrar un listado de tarjetas de débito del usuario
class ListDebitCardsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tarjetas = DebitCard.objects.filter(user=request.user)
        serializer = DebitCardSerializer(tarjetas, many=True)
        return Response(serializer.data, status=200)
    
# Esto permite mostrar las sucursales
class SucursalListView(generics.ListAPIView):
    queryset = Sucursal.objects.all()
    serializer_class = SucursalSerializer

# Esto permite al usuario elegir una sucursal y asignarla a su cuenta
class UpdateSucursalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, *args, **kwargs):
        try:
            user = request.user
            if not user.can_change_sucursal:
                return Response({"error": "No tienes permiso para cambiar tu sucursal."}, status=status.HTTP_403_FORBIDDEN)

            sucursal = Sucursal.objects.get(id=id)

            user.sucursal = sucursal
            user.can_change_sucursal = False
            user.save()

            return Response({"message": "Sucursal actualizada correctamente!"}, status=status.HTTP_200_OK)

        except Sucursal.DoesNotExist:
            return Response({"error": "Sucursal no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error al actualizar la sucursal: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
     
class ReactivateSucursalChangeView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, user_id, *args, **kwargs):
        try:
            user = CustomUser.objects.get(id=user_id)
            user.can_change_sucursal = True
            user.save()
            return Response({"message": "Permiso para cambiar sucursal reactivado."}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
# Esto permite validar si el usuario seleccionó la sucursal. Si es así, se bloquea la posibilidad de cambiar la sucursal  
class CheckSucursalPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response({"can_change_sucursal": user.can_change_sucursal}, status=status.HTTP_200_OK)

# Esto permite mostrar al usuario la sucursal asignada
class AssignedSucursalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.sucursal:
            return Response(
                {"error": "No tienes una sucursal asignada."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "provincia": user.sucursal.provincia,
                "direccion": user.sucursal.direccion,
            },
            status=status.HTTP_200_OK
        )
# Esto permite al usuario actualizar su perfil y guardar los cambios
class UpdateUserProfileView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        user = request.user
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        dni = request.data.get('dni')
        profile_image = request.data.get('profile_image')

        user_profile, created = UserProfile.objects.get_or_create(user=user)

        if first_name:
            user_profile.first_name = first_name
        if last_name:
            user_profile.last_name = last_name
        if email:
            user_profile.email = email
        if dni:
            user_profile.dni = dni
        if profile_image:
            user_profile.profile_image = profile_image

        user_profile.save()

        return Response({
            'first_name': user_profile.first_name,
            'last_name': user_profile.last_name,
            'email': user_profile.email,
            'dni': user_profile.dni,
            'profile_image': user_profile.profile_image.url if user_profile.profile_image else None
        })

class GetUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            user_profile = UserProfile.objects.get(user=user)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Perfil no encontrado'}, status=404)
        
class GetUserBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            balance = user.balance
            return Response({"balance": balance}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

class GetUserBalanceAndCBUView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "balance": user.balance,
            "cbu": user.cbu
        })
        
class ConsultarCuentaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        tipo_consulta = request.query_params.get("tipo", "").lower()

        if tipo_consulta == "cbu":
            return Response({"cbu": user.cbu}, status=status.HTTP_200_OK)

        elif tipo_consulta == "alias":
            return Response({"alias": user.alias}, status=status.HTTP_200_OK)

        return Response({
            "alias": user.alias,
            "cbu": user.cbu
        }, status=status.HTTP_200_OK)

# Esto permite mostrar la información completa del usuario
class GetFullUserDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            user_profile = user.userprofile

            sucursal = user.sucursal

            sucursal_nombre = sucursal.nombre if sucursal else 'No asignada'

            user_data = {
                'username': user.username,
                'email': user_profile.email or 'No registrado',
                'first_name': user_profile.first_name or 'N/A',
                'last_name': user_profile.last_name or 'N/A',
                'dni': user_profile.dni or 'N/A',
                'address': user.address or 'Sin dirección',
                'balance': user.balance or 0,
                'sucursal': sucursal_nombre,
                'alias': user.alias or 'Sin alias',
                'cbu': user.cbu or 'Sin CBU',
                'profile_image': user_profile.profile_image.url if user_profile.profile_image else None,
            }

            return Response(user_data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'Perfil del usuario no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {'detail': f'Error inesperado: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Esto permite transferir dinero a otro usuario registrado y descontar el monto de la cuenta del usuario que realiza la transferencia
class TransferirAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):

        user = request.user

        receiver_alias = request.data.get('receiver_alias')
        receiver_cbu = request.data.get('receiver_cbu')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        try:
            amount = Decimal(amount)
        except (ValueError, InvalidOperation):
            return Response({'detail': 'Monto inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({'detail': 'El monto debe ser mayor a cero.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if receiver_alias:
                receiver = CustomUser.objects.get(alias=receiver_alias)
            elif receiver_cbu:
                receiver = CustomUser.objects.get(cbu=receiver_cbu)
            else:
                return Response({'detail': 'Debe proporcionar un alias o un CBU del receptor.'}, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'Receptor no encontrado.'}, status=status.HTTP_404_NOT_FOUND)


        if user.balance < amount:
            return Response({'detail': 'Saldo insuficiente para realizar la transferencia.'}, status=status.HTTP_400_BAD_REQUEST)


        user.balance -= amount
        receiver.balance += amount

        user.save()
        receiver.save()

        transfer = Transfer.objects.create(
            sender=user,
            receiver=receiver,
            amount=amount,
            description=description,
            status="Completada"
        )

        transfer_data = {
            'sender': f"{transfer.sender.first_name} {transfer.sender.last_name}",
            'receiver': f"{transfer.receiver.first_name} {transfer.receiver.last_name}",
            'amount': str(transfer.amount),
            'timestamp': transfer.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'description': transfer.description or 'Sin descripción',
            'status': transfer.status
        }

        return Response({
            'detail': 'Transferencia realizada con éxito.',
            'transfer': transfer_data
        }, status=status.HTTP_200_OK)

#  Esto permite mostrar las transferencias realizadas o recibidas por el usuario 
class TransferenciasAPIView(APIView):
    def get(self, request, *args, **kwargs):
        user = request.user

        transfers_sent = Transfer.objects.filter(sender=user)
        transfers_received = Transfer.objects.filter(receiver=user)

        transfers = transfers_sent | transfers_received

        transfers = transfers.order_by('-timestamp')

        serializer = TransferSerializer(transfers, many=True)

        return Response({
            'transferencias': serializer.data
        }, status=status.HTTP_200_OK)
        