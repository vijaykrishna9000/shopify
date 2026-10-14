from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .models import Category, Product
from .resources import ProductResource


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = [ProductResource]   # on django-import-export 3.x use: resource_class = ProductResource


admin.site.register(Category)