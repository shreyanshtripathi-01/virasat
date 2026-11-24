# Django shell: Virasat ORM practice

Run `python manage.py seed_demo` first. Then run `python manage.py shell` and type the commands after each `>>>`. The outputs below were produced against the freshly seeded SQLite database. Primary keys may differ on your computer. The practice category is deleted, and the view count is restored, so the demo products stay unchanged.

## Import the models and query helpers

```pycon
>>> from django.contrib.auth.models import User
>>> from django.db.models import Avg, F, Q, Sum
>>> from catalog.models import Category, Product
>>> from orders.models import Order, OrderItem
```

## Insert, update and delete

Build a model instance, then insert it with `save()`:

```pycon
>>> sample = Category(name="Shell Practice", slug="shell-practice", description="Temporary shell category.")
>>> sample.save()
>>> print(sample.pk, str(sample))
8 Shell Practice
```

Update just one field, read it back with `get()`, and remove the practice row:

```pycon
>>> sample.description = "Updated in the Django shell."
>>> sample.save(update_fields=["description"])
>>> print(Category.objects.get(pk=sample.pk).description)
Updated in the Django shell.
>>> sample.delete()
>>> print(Category.objects.filter(slug="shell-practice").exists())
False
```

Alternatively, `objects.create()` inserts and saves in one step:

```pycon
>>> extra = Category.objects.create(name="Shell Create", slug="shell-create", description="Temporary practice entry.")
>>> print(extra.pk, extra.name)
9 Shell Create
>>> extra.delete()
>>> print(Category.objects.filter(slug="shell-create").exists())
False
```

## Filter, exclude, get, Q and ordering

Use `filter()` for matches across a foreign key and `exclude()` for the rest:

```pycon
>>> print(list(Product.objects.filter(craft__slug="madhubani").order_by("title").values_list("title", flat=True)))
['Madhubani Fish Art Panel', 'Madhubani Lotus Wall Painting', 'Madhubani Peacock Bookmarks']
>>> print(Product.objects.exclude(artisan__username="anita").count())
17
>>> print(Product.objects.get(title="Bagru Cotton Leaf Stole"))
Bagru Cotton Leaf Stole
```

`Q` combines conditions with OR. `order_by()` sorts the results:

```pycon
>>> print(list(Product.objects.filter(Q(title__icontains="cushion") | Q(tags__icontains="cushion")).order_by("title").values_list("title", flat=True)))
['Bagru Block Print Cushion Pair', 'Kantha Running Stitch Cushion', 'Phulkari Embroidered Cushion']
>>> print(list(Product.objects.order_by("-price").values_list("title", "price")[:3]))
[('Phulkari Floral Cotton Dupatta', Decimal('2200.00')), ('Pattachitra Tree of Life Scroll', Decimal('2100.00')), ('Dhokra Bell Metal Elephant', Decimal('1850.00'))]
```

## Annotate and aggregate

`annotate()` adds a value to each product; `aggregate()` returns one total for all orders:

```pycon
>>> print(list(Product.objects.annotate(score=Avg("reviews__rating")).filter(score__isnull=False).order_by("title").values_list("title", "score")))
[('Bagru Cotton Leaf Stole', 4.0), ('Bandhani Cotton Dupatta', 5.0), ('Madhubani Lotus Wall Painting', 5.0)]
>>> print(Order.objects.aggregate(total=Sum("total")))
{'total': Decimal('7970')}
```

## Follow related records

`select_related()` loads single related objects with joins. `prefetch_related()` loads collections in a separate query:

```pycon
>>> item = OrderItem.objects.select_related("product", "order__buyer").get(product__title="Madhubani Lotus Wall Painting")
>>> print(item.product.title, item.order.buyer.username)
Madhubani Lotus Wall Painting neha
>>> buyer = User.objects.prefetch_related("orders__items").get(username="neha")
>>> print([len(order.items.all()) for order in buyer.orders.all()])
[3]
```

## F expressions and reverse relations

`F()` reads the field in the database while updating it. Restore the count so the demo stays as seeded:

```pycon
>>> Product.objects.filter(title="Bagru Cotton Leaf Stole").update(view_count=F("view_count") + 1)
1
>>> print(Product.objects.get(title="Bagru Cotton Leaf Stole").view_count)
1
>>> Product.objects.filter(title="Bagru Cotton Leaf Stole").update(view_count=F("view_count") - 1)
1
>>> print(Product.objects.get(title="Bagru Cotton Leaf Stole").view_count)
0
```

The `related_name` on a foreign key gives access in the other direction:

```pycon
>>> print(User.objects.get(username="anita").products.count())
3
>>> print(Product.objects.get(title="Bagru Cotton Leaf Stole").reviews.count())
1
```
