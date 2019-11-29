from django.db import models


class Unsigned256IntegerField(models.DecimalField):
    def __init__(self, *args, **kw):
        kw["decimal_places"] = 0
        kw["max_digits"] = 78

        super().__init__(*args, **kw)
