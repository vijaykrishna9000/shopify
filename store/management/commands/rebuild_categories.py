from django.core.management.base import BaseCommand
from django.db import transaction

from store.models import Category, Product


class Command(BaseCommand):
    help = (
        "Rebuild Category (main + sub) records from each product's category "
        "path text, and re-point each product's category to the correct "
        "sub-category. Reads from Product.category_path if set, otherwise "
        "falls back to the current (flat) Product.category.name, which is "
        "how older imports stored the full 'Main|Sub|...' path as one name."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-old',
            action='store_true',
            help=(
                'After rebuilding, delete leftover old category rows that '
                'no longer have any products or subcategories attached. '
                'Safe to use: it only removes categories with nothing '
                'pointing to them, so it will never delete products.'
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        products = Product.objects.select_related('category').all()
        total = products.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No products found."))
            return

        main_cache = {}
        sub_cache = {}
        new_category_ids = set()
        updated = 0
        skipped = 0

        for product in products.iterator():
            path_text = (product.category_path or '').strip()
            if not path_text and product.category_id:
                path_text = (product.category.name or '').strip()

            parts = [p.strip() for p in path_text.split('|') if p.strip()]
            if not parts:
                skipped += 1
                continue

            main_name = parts[0]
            sub_name = parts[1] if len(parts) > 1 else None

            if main_name not in main_cache:
                main_cache[main_name], _ = Category.objects.get_or_create(
                    name=main_name, parent=None
                )
            main_category = main_cache[main_name]
            new_category_ids.add(main_category.id)

            if sub_name:
                sub_key = (main_name, sub_name)
                if sub_key not in sub_cache:
                    sub_cache[sub_key], _ = Category.objects.get_or_create(
                        name=sub_name, parent=main_category
                    )
                target_category = sub_cache[sub_key]
                new_category_ids.add(target_category.id)
            else:
                target_category = main_category

            update_fields = []
            if product.category_id != target_category.id:
                product.category = target_category
                update_fields.append('category')
            if not product.category_path:
                product.category_path = path_text
                update_fields.append('category_path')

            if update_fields:
                product.save(update_fields=update_fields)
                updated += 1

        main_count = Category.objects.filter(parent=None).count()
        sub_count = Category.objects.exclude(parent=None).count()

        self.stdout.write(self.style.SUCCESS(
            f"Processed {total} products (updated {updated}, skipped {skipped} "
            f"with no usable category text). Now have {main_count} main "
            f"categories and {sub_count} sub-categories."
        ))

        if options['delete_old']:
            leftover = Category.objects.exclude(id__in=new_category_ids).filter(
                product__isnull=True, subcategories__isnull=True
            )
            leftover_count = leftover.count()
            leftover.delete()
            self.stdout.write(self.style.SUCCESS(
                f"Deleted {leftover_count} leftover empty category rows."
            ))
        else:
            leftover_count = Category.objects.exclude(id__in=new_category_ids).filter(
                product__isnull=True, subcategories__isnull=True
            ).count()
            if leftover_count:
                self.stdout.write(
                    f"{leftover_count} old, now-unused category rows are still "
                    f"in the database. Re-run with --delete-old to remove them "
                    f"(this is safe and will not touch any products)."
                )
