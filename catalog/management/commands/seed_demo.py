"""Create repeatable demo accounts, crafts and marketplace records."""

from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import Profile
from catalog import art
from catalog.models import Category, CraftTradition, Product, Review
from linkage.models import BuyerRequest, Proposal
from orders.models import Order, OrderItem


# This is a public DEMO password, never a production credential.
DEMO_PASSWORD = "VirasatDemo2026!"

CATEGORIES = [
    ("Paintings", "Art for walls and small painted keepsakes."),
    ("Textiles", "Handmade fabrics, scarves and embroidered pieces."),
    ("Home Decor", "Useful handmade pieces for the home."),
    ("Jewellery", "Small handmade pieces to wear."),
    ("Toys", "Traditional toys made by hand."),
    ("Tableware", "Handcrafted pieces for serving and display."),
    ("Accessories", "Handmade bags, pouches and everyday extras."),
]

CRAFTS = [
    ("Madhubani", "Bihar", "Madhubani painting is a folk art from Bihar, known for outlined figures and detailed patterns.", True),
    ("Pattachitra", "Odisha", "Pattachitra is a traditional painted art from Odisha, often made with careful lines and bold colour.", False),
    ("Bagru block print", "Rajasthan", "Bagru is a Rajasthan tradition of printing cloth with hand-carved wooden blocks.", False),
    ("Bandhani", "Gujarat", "Bandhani uses tiny tied points in cloth to make patterns when the fabric is dyed.", False),
    ("Phulkari", "Punjab", "Phulkari is a Punjabi embroidery tradition with colourful stitched floral patterns.", False),
    ("Kantha", "West Bengal", "Kantha is a stitching tradition from Bengal, recognised for its rows of running stitches.", False),
    ("Channapatna toys", "Karnataka", "Channapatna is known for turned wooden toys painted in bright colours.", True),
    ("Dhokra", "Odisha", "Dhokra is a metal-casting craft practised in parts of eastern and central India.", False),
    ("Blue Pottery", "Rajasthan", "Jaipur blue pottery is known for glazed decorative pieces with blue painted patterns.", False),
]

# username, first name, last name, city, state, phone, speciality, experience, verified
ARTISANS = [
    ("anita", "Anita", "Kumari", "Darbhanga", "Bihar", "9876500001", "Madhubani painting", 12, True),
    ("sulekha", "Sulekha", "Patra", "Puri", "Odisha", "9876500002", "Pattachitra and Dhokra", 9, True),
    ("shabnam", "Shabnam", "Khan", "Jaipur", "Rajasthan", "9876500003", "Bagru prints and blue pottery", 14, True),
    ("fatima", "Fatima", "Sheikh", "Bhuj", "Gujarat", "9876500004", "Bandhani textiles", 11, True),
    ("jaspreet", "Jaspreet", "Kaur", "Amritsar", "Punjab", "9876500005", "Phulkari and hand embroidery", 7, False),
    ("lakshmi", "Lakshmi", "Shetty", "Channapatna", "Karnataka", "9876500006", "Turned wooden toys", 6, False),
]

# username, first name, last name, city, state, phone
BUYERS = [
    ("neha", "Neha", "Gupta", "Delhi", "Delhi", "9876500011"),
    ("rohan", "Rohan", "Das", "Kolkata", "West Bengal", "9876500012"),
    ("tara", "Tara", "Mehta", "Mumbai", "Maharashtra", "9876500013"),
    ("imran", "Imran", "Ali", "Bengaluru", "Karnataka", "9876500014"),
]

# Owner, craft, category, title, materials, technique, simple notes, Hindi notes,
# price, stock, comma-separated tags. Each title is a stable seed identifier.
PRODUCTS = [
    ("anita", "Madhubani", "Paintings", "Madhubani Lotus Wall Painting", "paper and colour", "hand painting with fine outlines", "Lotus flowers fill the centre with small leaves around the edge.", "इस चित्र में कमल और पत्तियों के सुंदर आकार हैं।", "1450.00", 6, "madhubani,lotus,painting,bihar,wall art"),
    ("anita", "Madhubani", "Accessories", "Madhubani Peacock Bookmarks", "thick paper and colour", "hand painting with fine outlines", "A set of four bookmarks with peacocks and leafy borders.", "चार बुकमार्क पर मोर और पत्तियों की सजावट है।", "320.00", 20, "madhubani,bookmark,peacock,handpainted,bihar"),
    ("anita", "Madhubani", "Home Decor", "Madhubani Fish Art Panel", "paper and colour", "hand painting with fine outlines", "Two fish sit inside a bright pattern made for a small wall space.", "दो मछलियों वाला यह चित्र छोटी दीवार पर अच्छा लगता है।", "950.00", 8, "madhubani,fish,home decor,painting,bihar"),
    ("sulekha", "Pattachitra", "Paintings", "Pattachitra Tree of Life Scroll", "canvas and colour", "brush painting and line work", "A small hanging scroll with a tree and birds in strong colours.", "इस छोटे स्क्रोल पर पेड़ और पक्षियों के चित्र हैं।", "2100.00", 4, "pattachitra,scroll,tree,odisha,painting"),
    ("sulekha", "Pattachitra", "Accessories", "Pattachitra Painted Bookmark Set", "thick paper and colour", "brush painting and line work", "Five slim bookmarks show flowers and small bird shapes.", "पाँच बुकमार्क पर फूल और छोटे पक्षियों के चित्र हैं।", "450.00", 16, "pattachitra,bookmark,flowers,odisha,gift"),
    ("sulekha", "Dhokra", "Home Decor", "Dhokra Bell Metal Elephant", "cast metal", "lost-wax metal casting", "A palm-sized elephant with a textured surface for a shelf.", "यह छोटी धातु की हाथी आकृति सजावट के लिए है।", "1850.00", 3, "dhokra,elephant,metal,odisha,decor"),
    ("shabnam", "Bagru block print", "Textiles", "Bagru Cotton Leaf Stole", "cotton and fabric dye", "wooden block printing", "A soft cotton stole with repeating leaf prints in earthy colours.", "इस सूती स्टोल पर पत्तियों की छपाई है।", "890.00", 12, "bagru,stole,cotton,block print,rajasthan"),
    ("shabnam", "Bagru block print", "Home Decor", "Bagru Block Print Cushion Pair", "cotton and fabric dye", "wooden block printing", "Two matching cushion covers with a simple repeated floral print.", "दो कुशन कवर पर फूलों की छपाई है।", "1200.00", 7, "bagru,cushion,block print,cotton,home"),
    ("shabnam", "Bagru block print", "Accessories", "Bagru Printed Market Tote", "cotton canvas and fabric dye", "wooden block printing", "A roomy cloth tote with hand-printed shapes on both sides.", "इस कपड़े के बैग के दोनों ओर हाथ की छपाई है।", "720.00", 10, "bagru,tote,bag,block print,rajasthan"),
    ("shabnam", "Blue Pottery", "Tableware", "Jaipur Blue Pottery Snack Bowl", "glazed ceramic", "hand painting and glazing", "A small blue-patterned bowl for dry snacks or display.", "नीली सजावट वाला यह कटोरा सूखे नाश्ते के लिए है।", "780.00", 8, "blue pottery,bowl,jaipur,ceramic,tableware"),
    ("shabnam", "Blue Pottery", "Home Decor", "Jaipur Blue Pottery Tile Pair", "glazed ceramic", "hand painting and glazing", "Two square blue-patterned tiles to display on a shelf.", "नीली सजावट वाली दो टाइलें शेल्फ पर रख सकते हैं।", "1050.00", 6, "blue pottery,tiles,jaipur,ceramic,decor"),
    ("fatima", "Bandhani", "Textiles", "Bandhani Cotton Dupatta", "cotton and fabric dye", "tie-dye knot work", "A light cotton dupatta with closely spaced dotted patterns.", "इस हल्के दुपट्टे पर बंधनी के छोटे बिंदु हैं।", "1350.00", 9, "bandhani,dupatta,cotton,gujarat,tie dye"),
    ("fatima", "Bandhani", "Textiles", "Bandhani Silk Blend Scarf", "silk-blend fabric and dye", "tie-dye knot work", "A narrow scarf with dotted bands and a bright border.", "इस स्कार्फ पर बिंदुओं की पट्टियाँ और रंगीन किनारा है।", "1690.00", 5, "bandhani,scarf,silk blend,gujarat,handmade"),
    ("fatima", "Bandhani", "Accessories", "Bandhani Drawstring Gift Pouch", "cotton and fabric dye", "tie-dye knot work", "A small fabric pouch for jewellery or a thoughtful gift.", "यह छोटा कपड़े का पाउच आभूषण रखने के लिए है।", "390.00", 18, "bandhani,pouch,gift,cotton,gujarat"),
    ("jaspreet", "Phulkari", "Textiles", "Phulkari Floral Cotton Dupatta", "cotton and embroidery thread", "hand embroidery", "Bright stitched flowers run along the ends of the dupatta.", "इस दुपट्टे के सिरों पर रंगीन फूलों की कढ़ाई है।", "2200.00", 4, "phulkari,dupatta,embroidery,punjab,flowers"),
    ("jaspreet", "Phulkari", "Home Decor", "Phulkari Embroidered Cushion", "cotton and embroidery thread", "hand embroidery", "A square cushion cover with a stitched flower in the centre.", "इस कुशन कवर के बीच में कढ़ाई का फूल है।", "1180.00", 6, "phulkari,cushion,embroidery,punjab,home"),
    ("jaspreet", "Kantha", "Home Decor", "Kantha Running Stitch Cushion", "cotton and sewing thread", "rows of running stitches", "Fine stitched rows cover this soft cushion cover.", "इस मुलायम कुशन कवर पर टाँकों की कतारें हैं।", "990.00", 7, "kantha,cushion,stitch,west bengal,home"),
    ("jaspreet", "Kantha", "Accessories", "Kantha Stitched Cloth Pouch", "cotton and sewing thread", "rows of running stitches", "A small zip pouch with neat stitched lines on the front.", "इस छोटे पाउच के सामने टाँकों की सीधी कतारें हैं।", "480.00", 13, "kantha,pouch,stitch,west bengal,gift"),
    ("lakshmi", "Channapatna toys", "Toys", "Channapatna Wooden Spinning Top", "turned wood and colour", "wood turning and hand colouring", "A round spinning top with stripes of bright colour.", "यह लकड़ी का लट्टू चमकीली रंगीन धारियों वाला है।", "520.00", 15, "channapatna,toy,spinning top,wood,karnataka"),
    ("lakshmi", "Channapatna toys", "Toys", "Channapatna Wooden Rattle", "turned wood and colour", "wood turning and hand colouring", "A smooth wooden rattle with alternating colour bands.", "यह लकड़ी का झुनझुना रंगीन पट्टियों वाला है।", "650.00", 11, "channapatna,toy,rattle,wood,karnataka"),
]

CARE = {
    "textiles": "Wash gently in cold water. Dry in shade and do not scrub the printed or stitched areas.",
    "paintings": "Keep away from water and direct sunlight. Dust lightly with a dry, soft cloth.",
    "home-decor": "Dust gently with a dry cloth. Keep away from prolonged moisture and harsh cleaners.",
    "accessories": "Wipe gently when needed. Keep dry and store away from direct sunlight.",
    "tableware": "Wipe with a soft cloth. Handle carefully and avoid strong knocks.",
    "toys": "Wipe with a slightly damp cloth and dry well. Check small parts before giving to a child.",
}


def create_groups():
    """Create the three role groups and grant the verifier permission."""
    groups = {}
    for name in ["Artisan", "Buyer", "Verifier"]:
        groups[name], _ = Group.objects.get_or_create(name=name)
    permission = Permission.objects.get(
        content_type__app_label="accounts", codename="can_verify_artisan"
    )
    groups["Verifier"].permissions.add(permission)
    return groups


def create_user(username, first_name, last_name, group=None, staff=False, superuser=False):
    """Create a demo user once without changing existing passwords."""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "first_name": first_name,
            "last_name": last_name,
            "email": f"{username}@example.com",
            "is_staff": staff,
            "is_superuser": superuser,
        },
    )
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=["password"])
    if group is not None:
        user.groups.add(group)
    return user


def create_users(groups):
    """Add an admin, a verifier, six artisans and four buyers."""
    create_user("admin", "Site", "Admin", staff=True, superuser=True)
    verifier = create_user("verifier", "Meera", "Rao", groups["Verifier"], staff=True)
    Profile.objects.get_or_create(
        user=verifier,
        defaults={
            "role": "verifier", "phone": "9876500000", "state": "Delhi", "city": "Delhi"
        },
    )
    for username, first, last, city, state, phone, speciality, years, verified in ARTISANS:
        user = create_user(username, first, last, groups["Artisan"])
        Profile.objects.get_or_create(
            user=user,
            defaults={
                "role": "artisan",
                "phone": phone,
                "city": city,
                "state": state,
                "craft_speciality": speciality,
                "years_of_experience": years,
                "bio": f"I make {speciality.lower()} in {city}. Each piece is made with care.",
                "is_verified": verified,
                "verification_status": "approved" if verified else "pending",
                "verified_by": verifier if verified else None,
                "verified_at": timezone.now() if verified else None,
            },
        )
    for username, first, last, city, state, phone in BUYERS:
        user = create_user(username, first, last, groups["Buyer"])
        Profile.objects.get_or_create(
            user=user,
            defaults={"role": "buyer", "phone": phone, "city": city, "state": state},
        )


def create_crafts_and_categories():
    """Create heritage craft records and product categories once."""
    for name, description in CATEGORIES:
        Category.objects.get_or_create(
            slug=slugify(name), defaults={"name": name, "description": description}
        )
    for name, state, description, gi_tagged in CRAFTS:
        CraftTradition.objects.get_or_create(
            slug=slugify(name),
            defaults={
                "name": name, "state": state, "description": description,
                "gi_tagged": gi_tagged,
            },
        )


PHOTO_SUFFIXES = (".jpg", ".jpeg", ".png", ".webp")


def seed_photo_for(slug):
    """Return an optional owned photo at media/seed_photos/<slug>.<ext>."""
    photo_dir = Path(settings.MEDIA_ROOT) / "seed_photos"
    for suffix in PHOTO_SUFFIXES:
        candidate = photo_dir / f"{slug}{suffix}"
        if candidate.exists():
            return candidate
    return None


def create_craft_images(refresh_images=False):
    """Generate one square cover per craft and assign it when appropriate."""
    created = 0
    for craft in CraftTradition.objects.all():
        filename = f"crafts/{craft.slug}.jpg"
        target = Path(settings.MEDIA_ROOT) / filename
        if craft.image and not refresh_images:
            # Keep an admin-uploaded cover. Only repair a missing generated file.
            if craft.image.name == filename and not target.exists():
                art.save_craft_image(target, craft.slug, craft.name)
                created += 1
            continue
        if refresh_images or not target.exists():
            art.save_craft_image(target, craft.slug, craft.name)
            created += 1
        if craft.image.name != filename:
            craft.image.name = filename
            craft.save(update_fields=["image"])
    return created


def create_products(refresh_images=False):
    """Create twenty published listings with original craft-specific art."""
    image_count = 0
    for number, item in enumerate(PRODUCTS):
        (owner, craft_name, category_name, title, materials, technique, notes,
         hindi_notes, price, stock, tags) = item
        artisan = User.objects.get(username=owner)
        craft = CraftTradition.objects.get(slug=slugify(craft_name))
        category = Category.objects.get(slug=slugify(category_name))
        product_slug = slugify(title)
        filename = f"products/demo/{product_slug}.jpg"
        target = Path(settings.MEDIA_ROOT) / filename
        existing = Product.objects.filter(artisan=artisan, title=title).first()
        existing_image = existing.image.name if existing else ""
        keep_upload = bool(existing_image) and not refresh_images and existing_image != filename
        should_generate = not keep_upload and (
            refresh_images or not existing_image
            or (existing_image == filename and not target.exists())
        )
        if should_generate:
            photo = seed_photo_for(product_slug)
            if photo is not None:
                art.import_seed_photo(photo, target)
            else:
                art.save_product_image(
                    target, product_slug, craft.slug, title, category.name,
                )
            image_count += 1
        source = ["fallback", "manual", "ai"][number % 3]
        product, _ = Product.objects.get_or_create(
            artisan=artisan,
            title=title,
            defaults={
                "craft": craft,
                "category": category,
                "raw_notes": notes,
                "materials": materials,
                "technique": technique,
                "description": (
                    f"{title} is made by hand from {materials}. {notes} "
                    f"The artisan uses {technique} to bring out its details. "
                    f"This piece reflects the {craft.name} tradition of {craft.state}. "
                    "Small differences in pattern are a natural part of handmade work."
                ),
                "hindi_description": (
                    f"यह {title} {craft.name} शिल्प से जुड़ी हस्तनिर्मित वस्तु है। "
                    f"{hindi_notes} हर वस्तु में हाथ के काम की अपनी पहचान होती है।"
                ),
                "heritage_story": craft.description,
                "care_instructions": CARE[slugify(category_name)],
                "tags": tags,
                "price": Decimal(price),
                "stock": stock,
                "image": filename,
                "status": "published",
                "ai_source": source,
                "ai_edited": source == "ai" and number % 7 == 0,
            },
        )
        if should_generate and product.image.name != filename:
            product.image.name = filename
            product.save(update_fields=["image"])
    return image_count


def create_orders_and_reviews():
    """Add three orders with different item stages and eligible reviews."""
    order_data = [
        ("neha", "New Delhi", "Delhi", "110001", "cod", [
            ("Madhubani Lotus Wall Painting", 1, "delivered"),
            ("Bagru Cotton Leaf Stole", 1, "delivered"),
            ("Bandhani Cotton Dupatta", 1, "delivered"),
        ]),
        ("rohan", "Kolkata", "West Bengal", "700001", "upi_demo", [
            ("Jaipur Blue Pottery Snack Bowl", 2, "shipped"),
            ("Channapatna Wooden Spinning Top", 1, "confirmed"),
        ]),
        ("tara", "Mumbai", "Maharashtra", "400001", "cod", [
            ("Phulkari Floral Cotton Dupatta", 1, "placed"),
            ("Kantha Running Stitch Cushion", 1, "cancelled"),
        ]),
    ]
    for username, city, state, pincode, method, lines in order_data:
        buyer = User.objects.get(username=username)
        total = Decimal("0.00")
        for title, quantity, status in lines:
            if status != "cancelled":
                total += Product.objects.get(title=title).price * quantity
        order, _ = Order.objects.get_or_create(
            buyer=buyer,
            full_name=buyer.get_full_name(),
            defaults={
                "phone": buyer.profile.phone,
                "address": f"12 Craft Lane, {city}",
                "city": city,
                "state": state,
                "pincode": pincode,
                "payment_method": method,
                "total": total,
            },
        )
        for title, quantity, status in lines:
            product = Product.objects.get(title=title)
            OrderItem.objects.get_or_create(
                order=order, product=product,
                defaults={
                    "quantity": quantity, "unit_price": product.price, "status": status,
                },
            )
    reviews = [
        ("Madhubani Lotus Wall Painting", 5, "The lines and colours are lovely."),
        ("Bagru Cotton Leaf Stole", 4, "Soft cloth and a neat print."),
        ("Bandhani Cotton Dupatta", 5, "The dotted pattern is beautiful."),
    ]
    for title, rating, comment in reviews:
        Review.objects.get_or_create(
            product=Product.objects.get(title=title),
            buyer=User.objects.get(username="neha"),
            defaults={"rating": rating, "comment": comment},
        )


def create_requests_and_proposals():
    """Add three buyer requests and four artisan offers."""
    today = timezone.localdate()
    request_data = [
        ("neha", "Hand-painted Madhubani wedding keepsakes", "Paintings", "Madhubani",
         "Small paintings with flower patterns for wedding guests.", 20, "250.00", "450.00", 45, "Bihar", "open"),
        ("imran", "Block-printed cotton table runners", "Textiles", "Bagru block print",
         "Cotton runners with a simple repeating leaf pattern.", 12, "750.00", "950.00", 60, "Rajasthan", "open"),
        ("tara", "Small wooden toys for a school fair", "Toys", "Channapatna toys",
         "Colourful hand-turned wooden toys for a school display.", 15, "300.00", "550.00", 80, "Karnataka", "closed"),
    ]
    for (buyer, title, category, craft, description, quantity, minimum, maximum,
         days, state, status) in request_data:
        BuyerRequest.objects.get_or_create(
            buyer=User.objects.get(username=buyer),
            title=title,
            defaults={
                "description": description,
                "category": Category.objects.get(slug=slugify(category)),
                "craft": CraftTradition.objects.get(slug=slugify(craft)),
                "quantity": quantity,
                "budget_min": Decimal(minimum),
                "budget_max": Decimal(maximum),
                "needed_by": today + timedelta(days=days),
                "preferred_state": state,
                "status": status,
            },
        )
    proposals = [
        ("Hand-painted Madhubani wedding keepsakes", "anita", "I can paint small flower designs for each guest.", "390.00", 25, "pending"),
        ("Block-printed cotton table runners", "shabnam", "I can print a leaf pattern on cotton runners.", "850.00", 30, "pending"),
        ("Small wooden toys for a school fair", "lakshmi", "I can make bright wooden tops for your fair.", "420.00", 35, "accepted"),
        ("Small wooden toys for a school fair", "shabnam", "I can arrange simple painted wooden toys.", "500.00", 40, "rejected"),
    ]
    for title, artisan, message, price, days, status in proposals:
        Proposal.objects.get_or_create(
            request=BuyerRequest.objects.get(title=title),
            artisan=User.objects.get(username=artisan),
            defaults={
                "message": message,
                "price_per_unit": Decimal(price),
                "delivery_days": days,
                "status": status,
            },
        )


class Command(BaseCommand):
    """Seed a safe-to-repeat local demo of the Virasat marketplace."""

    help = "Create local demo users, craft products, orders and requests."

    def add_arguments(self, parser):
        """Allow a deliberate rebuild of generated product and craft art."""
        parser.add_argument(
            "--refresh-images",
            action="store_true",
            help="Regenerate every product image and craft cover, including existing ones.",
        )

    def handle(self, *args, **options):
        """Run the seed steps in dependency order and show the demo login."""
        # Syllabus: Unit V - insert and query records using Django's ORM.
        if not settings.DEBUG:
            raise CommandError("Demo accounts have a public password. Seed only with DEBUG=True.")
        groups = create_groups()
        create_users(groups)
        create_crafts_and_categories()
        covers = create_craft_images(options["refresh_images"])
        product_images = create_products(options["refresh_images"])
        create_orders_and_reviews()
        create_requests_and_proposals()
        self.stdout.write(self.style.SUCCESS(
            "Demo ready: 3 groups, 12 users, 7 categories, 9 crafts, 20 products, "
            "3 orders, 3 reviews, 3 requests and 4 proposals."
        ))
        self.stdout.write(
            f"Artwork generated this run: {product_images} product images, {covers} craft covers."
        )
        self.stdout.write("Demo usernames: admin, verifier, anita, sulekha, shabnam, "
                          "fatima, jaspreet, lakshmi, neha, rohan, tara, imran")
        self.stdout.write(f"Password for newly created demo users: {DEMO_PASSWORD}")
        self.stdout.write("Existing account passwords and edited demo records are not reset.")
