"""Tests for the original Pillow artwork used by the seeded marketplace."""

from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase
from PIL import Image

from . import art


CRAFT_SAMPLES = [
    ("madhubani", "madhubani-lotus-wall-painting", "Madhubani Lotus Wall Painting", "Paintings"),
    ("pattachitra", "pattachitra-tree-of-life-scroll", "Pattachitra Tree of Life Scroll", "Paintings"),
    ("dhokra", "dhokra-bell-metal-elephant", "Dhokra Bell Metal Elephant", "Home Decor"),
    ("bagru-block-print", "bagru-cotton-leaf-stole", "Bagru Cotton Leaf Stole", "Textiles"),
    ("blue-pottery", "jaipur-blue-pottery-snack-bowl", "Jaipur Blue Pottery Snack Bowl", "Tableware"),
    ("bandhani", "bandhani-cotton-dupatta", "Bandhani Cotton Dupatta", "Textiles"),
    ("phulkari", "phulkari-floral-cotton-dupatta", "Phulkari Floral Cotton Dupatta", "Textiles"),
    ("kantha", "kantha-running-stitch-cushion", "Kantha Running Stitch Cushion", "Home Decor"),
    ("channapatna-toys", "channapatna-wooden-spinning-top", "Channapatna Wooden Spinning Top", "Toys"),
]


class ArtGeneratorTests(SimpleTestCase):
    """Keep every generated image valid, reproducible and small enough to load."""

    def test_product_kind_mapping(self):
        """The seed titles map to the intended item silhouette."""
        cases = {
            "Madhubani Peacock Bookmarks": "bookmarks",
            "Pattachitra Tree of Life Scroll": "scroll",
            "Dhokra Bell Metal Elephant": "elephant",
            "Bagru Block Print Cushion Pair": "cushion",
            "Bagru Printed Market Tote": "tote",
            "Jaipur Blue Pottery Snack Bowl": "bowl",
            "Jaipur Blue Pottery Tile Pair": "tiles",
            "Bandhani Cotton Dupatta": "dupatta",
            "Bandhani Silk Blend Scarf": "scarf",
            "Bandhani Drawstring Gift Pouch": "pouch",
            "Channapatna Wooden Spinning Top": "spinning_top",
            "Channapatna Wooden Rattle": "rattle",
            "Madhubani Lotus Wall Painting": "wall_hanging",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(art.product_kind(title, ""), expected)

    def test_every_craft_makes_a_valid_jpeg(self):
        """Every craft renderer writes a 1200x1500 JPEG below 250 KB."""
        with TemporaryDirectory() as temp_dir:
            hashes = set()
            for craft_slug, slug, title, category in CRAFT_SAMPLES:
                with self.subTest(craft=craft_slug):
                    path = Path(temp_dir) / f"{slug}.jpg"
                    art.save_product_image(path, slug, craft_slug, title, category)
                    self.assertLessEqual(path.stat().st_size, art.JPEG_LIMIT)
                    with Image.open(path) as image:
                        self.assertEqual(image.format, "JPEG")
                        self.assertEqual(image.size, art.CANVAS)
                        image.verify()
                    hashes.add(path.read_bytes())
            self.assertEqual(len(hashes), len(CRAFT_SAMPLES))

    def test_every_craft_cover_is_square_and_small(self):
        """Craft covers are distinct 800x800 JPEGs with a strict size budget."""
        with TemporaryDirectory() as temp_dir:
            hashes = set()
            for craft_slug, _slug, _title, _category in CRAFT_SAMPLES:
                with self.subTest(craft=craft_slug):
                    path = Path(temp_dir) / f"cover-{craft_slug}.jpg"
                    art.save_craft_image(path, craft_slug, craft_slug.replace("-", " ").title())
                    self.assertLessEqual(path.stat().st_size, 180 * 1024)
                    with Image.open(path) as image:
                        self.assertEqual(image.format, "JPEG")
                        self.assertEqual(image.size, art.COVER_SIZE)
                        image.verify()
                    hashes.add(path.read_bytes())
            self.assertEqual(len(hashes), len(CRAFT_SAMPLES))

    def test_same_slug_is_byte_for_byte_reproducible(self):
        """Seeded randomness keeps the same slug and craft perfectly stable."""
        first = art.product_art(
            "madhubani-lotus-wall-painting", "madhubani",
            "Madhubani Lotus Wall Painting", "Paintings",
        )
        second = art.product_art(
            "madhubani-lotus-wall-painting", "madhubani",
            "Madhubani Lotus Wall Painting", "Paintings",
        )
        self.assertEqual(first.tobytes(), second.tobytes())

    def test_different_slugs_change_the_composition(self):
        """Two wall paintings in one craft still get different seeded art."""
        first = art.product_art(
            "madhubani-lotus-wall-painting", "madhubani",
            "Madhubani Lotus Wall Painting", "Paintings",
        )
        second = art.product_art(
            "madhubani-fish-art-panel", "madhubani",
            "Madhubani Fish Art Panel", "Home Decor",
        )
        self.assertNotEqual(first.tobytes(), second.tobytes())

    def test_owned_seed_photo_is_cropped_and_compressed(self):
        """A local owned photo becomes a 4:5 JPEG below the size limit."""
        with TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "owned.png"
            destination = Path(temp_dir) / "photo.jpg"
            Image.new("RGB", (640, 960), "#B5482A").save(source, format="PNG")
            art.import_seed_photo(source, destination)
            self.assertLessEqual(destination.stat().st_size, art.JPEG_LIMIT)
            with Image.open(destination) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.size, art.CANVAS)
