from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import Order, Product,Category


def home(request):
    products = Product.objects.all()
    return render(request, 'store/home.html', {
        'products': products,
        'page_title': 'All Products',
        'active_category': '',
    })


def category_products(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    if category.is_main:
        # Show products directly in this main category plus all its sub-categories.
        category_ids = [category.id] + list(category.subcategories.values_list('id', flat=True))
        page_title = category.name
    else:
        category_ids = [category.id]
        page_title = f"{category.parent.name} > {category.name}" if category.parent else category.name

    products = Product.objects.filter(category_id__in=category_ids)

    return render(request, "store/home.html", {
        "products": products,
        "page_title": page_title,
        "active_category": category.id,
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'store/product_detail.html', {'product': product})


def checkout(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return render(request, 'store/checkout_error.html', {
            'product': product,
            'message': 'Razorpay test keys are not configured yet.',
        })

    try:
        import razorpay
    except ImportError:
        return render(request, 'store/checkout_error.html', {
            'product': product,
            'message': 'The Razorpay package is not installed in this Python environment.',
        })

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    amount = int(product.discounted_price * 100)

    try:
        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': '1',
        })
    except Exception as exc:
        return render(request, 'store/checkout_error.html', {
            'product': product,
            'message': str(exc),
        })

    order = Order.objects.create(
        product=product,
        quantity=1,
        customer_email=request.user.email if request.user.is_authenticated else '',
        razorpay_order_id=razorpay_order['id'],
    )

    return render(request, 'store/checkout.html', {
        'product': product,
        'amount': amount,
        'callback_url': request.build_absolute_uri(reverse('store:verify_payment')),
        'customer_email': order.customer_email,
        'customer_name': request.user.get_username() if request.user.is_authenticated else '',
        'order': order,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_order_id': razorpay_order['id'],
    })


@csrf_exempt
def verify_payment(request):
    if request.method != 'POST':
        return redirect('store:home')

    try:
        import razorpay
    except ImportError:
        return render(request, 'store/payment_cancel.html')

    razorpay_order_id = request.POST.get('razorpay_order_id', '')
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
    razorpay_signature = request.POST.get('razorpay_signature', '')

    order = get_object_or_404(Order, razorpay_order_id=razorpay_order_id)
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except Exception:
        return redirect('store:payment_cancel')

    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_signature = razorpay_signature
    order.paid = True
    order.save()
    return redirect('store:payment_success')


def payment_success(request):
    return render(request, 'store/payment_success.html')


def payment_cancel(request):
    return render(request, 'store/payment_cancel.html')
