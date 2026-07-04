"""Backfill: the platform now trades in a single currency (EGP)."""

from django.db import migrations


def to_egp(apps, schema_editor):
    Store = apps.get_model("stores", "Store")
    Store.objects.all().update(currency="EGP")


def noop(apps, schema_editor):
    # No sensible reverse — historic multi-currency data is not restorable.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("stores", "0004_alter_store_currency"),
    ]
    operations = [migrations.RunPython(to_egp, noop)]
