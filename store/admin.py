from decimal import Decimal, InvalidOperation

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget, Widget

from .models import Order, Product, ProductImage, Category


class CurrencyWidget(Widget):
    """Cleans values like '₹1,099' or '1,099' into a Decimal."""

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        text = str(value)
        for ch in ('₹', 'Rs.', 'Rs', ',', ' '):
            text = text.replace(ch, '')
        text = text.strip()
        if not text:
            return None
        try:
            return Decimal(text)
        except InvalidOperation:
            return None

    def render(self, value, obj=None):
        return '' if value is None else str(value)


class PercentWidget(Widget):
    """Cleans values like '64%' into an int."""

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return 0
        text = str(value).replace('%', '').strip()
        if not text:
            return 0
        try:
            return int(round(float(text)))
        except ValueError:
            return 0

    def render(self, value, obj=None):
        return '' if value is None else str(value)


class CommaIntWidget(Widget):
    """Cleans values like '24,269' into an int."""

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return 0
        text = str(value).replace(',', '').strip()
        if not text:
            return 0
        try:
            return int(float(text))
        except ValueError:
            return 0

    def render(self, value, obj=None):
        return '' if value is None else str(value)


class DecimalCleanWidget(Widget):
    """Cleans a plain-ish decimal field (e.g. rating) that may have stray text."""

    def clean(self, value, row=None, **kwargs):
        if value in (None, ''):
            return None
        text = str(value).replace(',', '').strip()
        if not text:
            return None
        try:
            return Decimal(text)
        except InvalidOperation:
            return None

    def render(self, value, obj=None):
        return '' if value is None else str(value)


class ProductResource(resources.ModelResource):
    category = fields.Field(
        column_name="category",
        attribute="category",
        widget=ForeignKeyWidget(Category, "name")
    )
    category_path = fields.Field(
        column_name="category",
        attribute="category_path",
    )
    discounted_price = fields.Field(
        column_name="discounted_price",
        attribute="discounted_price",
        widget=CurrencyWidget(),
    )
    actual_price = fields.Field(
        column_name="actual_price",
        attribute="actual_price",
        widget=CurrencyWidget(),
    )
    discount_percentage = fields.Field(
        column_name="discount_percentage",
        attribute="discount_percentage",
        widget=PercentWidget(),
    )
    rating = fields.Field(
        column_name="rating",
        attribute="rating",
        widget=DecimalCleanWidget(),
    )
    rating_count = fields.Field(
        column_name="rating_count",
        attribute="rating_count",
        widget=CommaIntWidget(),
    )

    class Meta:
        model = Product
        fields = (
            "product_id",
            "product_name",
            "category",
            "category_path",
            "discounted_price",
            "actual_price",
            "discount_percentage",
            "rating",
            "rating_count",
            "about_product",
            "img_link",
            "product_link",
        )
        import_id_fields = ("product_id",)


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'customer_email', 'paid', 'date_ordered')
    list_filter = ('paid', 'date_ordered')
    search_fields = ('customer_email', 'product__name')
