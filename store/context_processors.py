from .models import Category


def categories(request):
    main_categories = (
        Category.objects
        .filter(parent__isnull=True)
        .prefetch_related('subcategories')
        .order_by('name')
    )
    return {
        'product_categories': main_categories,
    }
