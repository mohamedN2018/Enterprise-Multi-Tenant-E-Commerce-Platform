"""Seed the new product gallery from the legacy single ``Product.image``.

Every product that already has an uploaded image gets one ``ProductImage`` row
(position 0) so galleries are populated on day one. Idempotent: skips products
that already have gallery rows.
"""

from django.db import migrations


def backfill_gallery(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    ProductImage = apps.get_model("catalog", "ProductImage")

    for product in Product.objects.filter(is_deleted=False):
        if not product.image:
            continue
        if ProductImage.objects.filter(product=product).exists():
            continue
        ProductImage.objects.create(
            store_id=product.store_id,
            product=product,
            image=product.image,
            position=0,
        )


def unbackfill(apps, schema_editor):
    ProductImage = apps.get_model("catalog", "ProductImage")
    ProductImage.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_productimage")]
    operations = [migrations.RunPython(backfill_gallery, unbackfill)]
