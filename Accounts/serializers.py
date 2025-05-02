from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueValidator
from Accounts.models import CustomUser
# from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'username', 'password']

    def create(self, validate_data):
        user = User.objects.create_user(
            email=validate_data['email'],
            username=validate_data['username'],
            password=validate_data['password']
        )
        return user

# class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
#     def validate(self, attrs):
#         email = attrs.get("email")
#         password = attrs.get("password")

#         try:
#             user = User.objects.get(email=email)
#         except User.DoesNotExist:
#             raise serializers.ValidationError({"detail": "No user with this email"})

#         # Now rebuild the attrs so TokenObtainPairSerializer works as expected
#         new_attrs = {
#             "username": user.username,
#             "password": password
#         }

#         return super().validate(new_attrs)