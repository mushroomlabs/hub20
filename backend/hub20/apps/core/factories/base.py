import factory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"test-user-{n:03}")
    is_active = True
    is_staff = False
    is_superuser = False

    class Meta:
        model = User


__all__ = ["UserFactory"]
