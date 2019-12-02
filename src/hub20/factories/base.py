from django.contrib.auth import get_user_model

import factory


User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: f"test-user-{n:03}")

    class Meta:
        model = User


__all__ = ["UserFactory"]
