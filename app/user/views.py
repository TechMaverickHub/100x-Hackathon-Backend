import logging

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.db import transaction
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken

from app.core.views import CustomPageNumberPagination
from app.global_constants import SuccessMessage, ErrorMessage, GlobalValues
from app.user.serializers import UserDisplaySerializer, UserCreateSerializer, UserListFilterDisplaySerializer, \
    UserUpdateSerializer
from app.utils import get_response_schema
from permissions import IsSuperAdmin

logger = logging.getLogger('django')

class UserCreateThrottle(AnonRateThrottle):
    """Custom throttle for login endpoint"""
    rate = '10/hour'


class SuperAdminSetupView(GenericAPIView):
    """ View: Admin setup """
    throttle_classes = [UserCreateThrottle]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        )
    )
    def post(self, request):
        with transaction.atomic():
            request.data['role'] = GlobalValues.SUPER_ADMIN.value

            serializer = UserCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()

                user = get_user_model().objects.get(pk=serializer.data['pk'])
                response_serializer = UserDisplaySerializer(user)

                return get_response_schema(response_serializer.data, SuccessMessage.RECORD_CREATED.value,
                                           status.HTTP_201_CREATED, )

            return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)


class UserSetupView(GenericAPIView):
    """ View: Admin setup """
    throttle_classes = [UserCreateThrottle]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        )
    )
    def post(self, request):
        with transaction.atomic():
            request.data['role'] = GlobalValues.USER.value

            serializer = UserCreateSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()

                user = get_user_model().objects.get(pk=serializer.data['pk'])
                response_serializer = UserDisplaySerializer(user)

                return get_response_schema(response_serializer.data, SuccessMessage.RECORD_CREATED.value,
                                           status.HTTP_201_CREATED, )

            return get_response_schema(serializer.errors, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

class UserLoginThrottle(AnonRateThrottle):
    """Custom throttle for login endpoint"""
    rate = '100/hour'


class UserLogin(GenericAPIView):
    """ View: User login """

    throttle_classes = [UserLoginThrottle]
    serializer_class = UserDisplaySerializer

    @swagger_auto_schema(
        request_body=
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
        )
    )
    def post(self, request):
        try:
            email = request.data.get('email')
            password = request.data.get('password')

            if not email or not password:
                return get_response_schema(
                    {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.MISSING_FIELDS.value]},
                    ErrorMessage.BAD_REQUEST.value,
                    status.HTTP_400_BAD_REQUEST
                )

            user = get_user_model().objects.filter(email=email, is_active=True).first()

            if user is None:
                logger.warning(f"Login attempt for non-existent email: {email}")
                return get_response_schema(
                    {},
                    ErrorMessage.NOT_FOUND.value,
                    status.HTTP_404_NOT_FOUND
                )

            if not user.check_password(password):
                logger.warning(f"Failed login attempt for user: {email}")
                return get_response_schema(
                    {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.PASSWORD_MISMATCH.value]},
                    ErrorMessage.BAD_REQUEST.value,
                    status.HTTP_400_BAD_REQUEST
                )

            # Successful authentication
            login(request, user)

            #upadte last login
            user.last_login = timezone.now()
            user.save()

            refresh = RefreshToken.for_user(user)
            user_data = self.get_serializer(user).data

            # Log successful login (without sensitive data)
            logger.info(f"User {user.id} logged in successfully")

            return_data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            }

            return get_response_schema(
                return_data,
                SuccessMessage.CREDENTIALS_MATCHED.value,
                status.HTTP_200_OK
            )

        except Exception as e:
            logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
            return get_response_schema(
                {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [ErrorMessage.SOMETHING_WENT_WRONG.value]},
                ErrorMessage.SOMETHING_WENT_WRONG.value,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserLogout(GenericAPIView):
    """ View: User logout """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=
        openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='refresh token'),
            },
        )
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()

            return get_response_schema({}, SuccessMessage.CREDENTIALS_REMOVED.value, status.HTTP_204_NO_CONTENT)
        except:
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

class UserDetailAPI(GenericAPIView):

    permission_classes = [IsSuperAdmin]

    def get_object(self, pk):

        user_queryset = get_user_model().objects.select_related('role').filter(pk=pk,is_active=True, role_id=GlobalValues.USER.value)
        if user_queryset:
            return user_queryset[0]
        return None

    def get(self, request, pk):
        logger.info(f"UserDetailAPI accessed by user: {request.user}. Requested user ID: {pk}")

        if not pk:
            logger.warning("Bad request: No primary key provided.")
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        if not user:
            logger.error(f"Error retrieving user with ID {pk}", exc_info=True)
            return get_response_schema(
                {},
                ErrorMessage.NOT_FOUND.value,
                status.HTTP_404_NOT_FOUND
            )

        serializer = UserDisplaySerializer(user)
        logger.info(f"Successfully retrieved user with ID {pk}")
        return get_response_schema(
            serializer.data,
            SuccessMessage.RECORD_RETRIEVED.value,
            status.HTTP_200_OK
        )


    def delete(self, request, pk):

        logger.info(f"UserDetailAPI accessed by user: {request.user}. Requested user ID: {pk}")

        if not pk:
            logger.warning("Bad request: No primary key provided.")
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        if not user:
            logger.error(f"Error retrieving user with ID {pk}", exc_info=True)
            return get_response_schema(
                {},
                ErrorMessage.NOT_FOUND.value,
                status.HTTP_404_NOT_FOUND
            )

        user.is_active = False
        user.save()

        logger.info(f"Successfully deleted user with ID {pk}")

        return get_response_schema({}, SuccessMessage.RECORD_DELETED.value, status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last name'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'bio': openapi.Schema(type=openapi.TYPE_STRING, description='Biography'),
                'birth_date': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Birth date'),
                'location': openapi.Schema(type=openapi.TYPE_STRING, description='Location'),
                'website': openapi.Schema(type=openapi.TYPE_STRING, format='url', description='Website'),
                'profile_picture': openapi.Schema(type=openapi.TYPE_STRING, format='binary',
                                                  description='Profile picture'),
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username"),
                'is_private': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is private'),
            }
        )
    )
    def patch(self, request, pk):

        logger.info(f"UserDetailAPI accessed by user: {request.user}. Requested user ID: {pk}")

        if not pk:
            logger.warning("Bad request: No primary key provided.")
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        if not user:
            logger.error(f"Error retrieving user with ID {pk}", exc_info=True)
            return get_response_schema(
                {},
                ErrorMessage.NOT_FOUND.value,
                status.HTTP_404_NOT_FOUND
            )

        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            logger.info(f"Successfully updated user with ID {pk}")
            return get_response_schema(
                serializer.data,
                SuccessMessage.RECORD_UPDATED.value,
                status.HTTP_201_CREATED
            )

        logger.info(f"Error deleting user with ID {pk}")

        return get_response_schema(
            serializer.errors,
            ErrorMessage.BAD_REQUEST.value,
            status.HTTP_400_BAD_REQUEST
        )


class UserListFilterAPI(ListAPIView):
    """User List filter for Superadmin"""

    serializer_class = UserListFilterDisplaySerializer
    pagination_class = CustomPageNumberPagination

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get_queryset(self):

        user_queryset = get_user_model().objects.filter(role_id=GlobalValues.USER.value).order_by('-updated')

        # Filter by user email
        email = self.request.query_params.get("email", None)
        if email:
            user_queryset = user_queryset.filter(email__istartswith=email)

        # Filter by first name
        first_name = self.request.query_params.get("first_name", None)
        if first_name:
            user_queryset = user_queryset.filter(first_name__istartswith=first_name)

        # Filter by last name
        last_name = self.request.query_params.get("last_name", None)
        if last_name:
            user_queryset = user_queryset.filter(last_name__istartswith=last_name)

        # Filter by is_active
        is_active = self.request.query_params.get("is_active", None)
        if is_active:
            user_queryset = user_queryset.filter(is_active=is_active)

        return user_queryset


    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="email",
                in_=openapi.IN_QUERY,
                description="Filter by user email",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="first_name",
                in_=openapi.IN_QUERY,
                description="Filter by user first name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="last_name",
                in_=openapi.IN_QUERY,
                description="Filter by user last name",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                name="is_active",
                in_=openapi.IN_QUERY,
                description="Filter by user is_active",
                type=openapi.TYPE_STRING,
                enum=["True", "False"]
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ActivateUserAPI(GenericAPIView):
    """Activate user for Superadmin"""

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdmin]

    def get_object(self, pk):

        user_queryset = get_user_model().objects.filter(pk=pk,is_active=False, role_id=GlobalValues.USER.value)
        if user_queryset:
            return user_queryset[0]
        return None

    def post(self, request, pk):

        logger.info(f"ActivateUserAPI accessed by user: {request.user}. Requested user ID: {pk}")

        if not pk:
            logger.warning("Bad request: No primary key provided.")
            return get_response_schema({}, ErrorMessage.BAD_REQUEST.value, status.HTTP_400_BAD_REQUEST)

        user = self.get_object(pk)
        if not user:
            logger.error(f"Error retrieving user with ID {pk}", exc_info=True)
            return get_response_schema(
                {},
                ErrorMessage.NOT_FOUND.value,
                status.HTTP_404_NOT_FOUND
            )

        user.is_active = True
        user.save()

        logger.info(f"Successfully activated user with ID {pk}")

        return get_response_schema({}, SuccessMessage.RECORD_UPDATED.value, status.HTTP_200_OK)







