from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, LoanViewSet, RegisterView, LoginView
from .views import ValidateTokenView, SolicitarPrestamoView, ObtenerPrestamosView, ListDebitCardsView, SucursalListView, UpdateSucursalView, ReactivateSucursalChangeView, CheckSucursalPermissionView, UpdateUserProfileView, GetUserProfileView, GetUserBalanceView,ConsultarCuentaView, GetFullUserDetailsView, EliminarPrestamoView, TransferirAPIView, TransferenciasAPIView, AssignedSucursalView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'loans', LoanViewSet)
# router.register(r'cards', CardViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('api/validate-token/', ValidateTokenView.as_view(), name='validate-token'),
    path('solicitar-prestamo/', SolicitarPrestamoView.as_view(), name='solicitar-prestamo'),
    path('mis-prestamos/', ObtenerPrestamosView.as_view(), name='obtener-prestamos'),
    path('eliminar-prestamo/<int:pk>/', EliminarPrestamoView.as_view(), name='eliminar-prestamo'),
    path('tarjetas/', ListDebitCardsView.as_view(), name='list_debit_cards'),
    path('sucursales/', SucursalListView.as_view(), name='sucursales-list'),
    path('update-sucursal/', UpdateSucursalView.as_view(), name='update-sucursal'),
    path('update-sucursal/<int:id>/', UpdateSucursalView.as_view(), name='update_sucursal'),
    path('reactivate-sucursal-change/<int:user_id>/', ReactivateSucursalChangeView.as_view(), name='reactivate_sucursal_change'),
    path('check-sucursal-permission/', CheckSucursalPermissionView.as_view(), name='check_sucursal_permission'),
    path('update-profile/', UpdateUserProfileView.as_view(), name='update-profile'),
    path('profile/', GetUserProfileView.as_view(), name='get-profile'),
    # path('update-profile-image/', ProfileImageView.as_view(), name='update-profile-image'),
    path('user-balance/', GetUserBalanceView.as_view(), name='user-balance'),
    path('user-cuenta/', ConsultarCuentaView.as_view(), name='consultar-cuenta'),
    path('perfil-completo/', GetFullUserDetailsView.as_view(), name='get-full-user-details'),
    path('transferir/', TransferirAPIView.as_view(), name='transferencia'),
    path('transferencias/', TransferenciasAPIView.as_view(), name='transferencias'),
    # path('user-sucursal/', UserSucursalView.as_view(), name='user_sucursal'),
    path("mi-sucursal/", AssignedSucursalView.as_view(), name="mi-sucursal"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
