from rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers


class UserProfileSerializer(UserDetailsSerializer):
    has_admin_access = serializers.BooleanField(source="is_staff", read_only=True)

    class Meta:
        model = UserDetailsSerializer.Meta.model
        fields = UserDetailsSerializer.Meta.fields + ("has_admin_access",)
        read_only_fields = UserDetailsSerializer.Meta.read_only_fields + ("has_admin_access",)
