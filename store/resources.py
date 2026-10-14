import re
from decimal import Decimal, InvalidOperation

from import_export import resources

from .models import Category, Product


def to_decimal_str(value, default=''):
    """'₹ 1,099' -> '1099'; junk -> default."""
    cleaned = re.sub(r'[^\d.]', '', str(value or ''))
    try:
        Decimal(cleaned)
    except InvalidOperation:
        return default
    return cleaned


def to_int_str(value, default='0'):
    """'24,269' -> '24269', '64%' -> '64', '' -> '0'."""
    cleaned = re.sub(r'[^\d]', '', str(value or '').split('.')[0])
    return cleaned or default


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        import_id_fields = ['product_id']   # duplicate IDs update the same product
        fields = (
            'product_id', 'product_name', 'category', 'category_path',
            'discounted_price', 'actual_price', 'discount_percentage',
            'rating', 'rating_count', 'about_product', 'img_link', 'product_link',
        )

    def before_import_row(self, row, **kwargs):
        # --- category: "Main|Sub|..." -> Category rows ---
        raw = (row.get('category') or '').strip()
        parts = [p.strip() for p in raw.split('|') if p.strip()]

        row['category_path'] = raw
        if parts:
            main, _ = Category.objects.get_or_create(name=parts[0], parent=None)
            target = main
            if len(parts) > 1:
                target, _ = Category.objects.get_or_create(name=parts[1], parent=main)
            row['category'] = target.pk
        else:
            row['category'] = None

        # --- numbers ---
        row['discounted_price'] = to_decimal_str(row.get('discounted_price'), '0')
        row['actual_price'] = to_decimal_str(row.get('actual_price'), '0')
        row['discount_percentage'] = to_int_str(row.get('discount_percentage'))
        row['rating_count'] = to_int_str(row.get('rating_count'))
        row['rating'] = to_decimal_str(row.get('rating'), '')   # '|' -> blank -> NULL