from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=500)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )

    class Meta:
        verbose_name_plural = 'categories'
        unique_together = ('name', 'parent')

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def is_main(self):
        return self.parent_id is None
class Product(models.Model):
    product_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    product_name = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    category_path = models.CharField(max_length=500, blank=True)

    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.IntegerField(default=0)
    rating = models.DecimalField(max_digits=5, decimal_places=2,null=True, blank=True)
    rating_count = models.IntegerField(default=0)
    about_product = models.TextField(blank=True)
    img_link = models.URLField(max_length=1000, blank=True)
    product_link = models.URLField(max_length=1000, blank=True)

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.alt_text or f"Image for {self.product.product_name}"


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    customer_email = models.EmailField(blank=True)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    paid = models.BooleanField(default=False)
    date_ordered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} ({'Paid' if self.paid else 'Pending'})"

