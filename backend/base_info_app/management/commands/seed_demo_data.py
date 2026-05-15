"""Seed the Coderr database with realistic demo data.

Usage:
    python manage.py seed_demo_data            # add demo data if missing
    python manage.py seed_demo_data --clear    # wipe coderr data first
    python manage.py seed_demo_data --reset    # wipe + reseed in one step

The script is idempotent: usernames are reused via ``get_or_create``,
so a second run does not duplicate accounts. Offers, orders, and
reviews are only created when the related users do not yet have any.
"""
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from offer_app.models import Offer, OfferDetail
from order_app.models import Order
from profile_app.models import Profile
from review_app.models import Review

User = get_user_model()

PASSWORD = "demo-pw-12345"

BUSINESSES = [
    {
        "username": "b_designer", "email": "designer@coderr.test",
        "first_name": "Lena", "last_name": "Bauer",
        "location": "Berlin", "tel": "+49 30 1112233",
        "description": "Grafikdesign & Branding seit 2018.",
        "working_hours": "Mo-Fr 9-17",
    },
    {
        "username": "b_developer", "email": "dev@coderr.test",
        "first_name": "Tarek", "last_name": "Yilmaz",
        "location": "Hamburg", "tel": "+49 40 4445566",
        "description": "Full-Stack Web-Entwicklung (Django, React).",
        "working_hours": "Mo-Fr 10-18",
    },
    {
        "username": "b_translator", "email": "trans@coderr.test",
        "first_name": "Sophie", "last_name": "Klein",
        "location": "München", "tel": "+49 89 7778899",
        "description": "DE/EN/FR Fachübersetzungen.",
        "working_hours": "Mo-Sa 8-20",
    },
    {
        "username": "b_copywriter", "email": "copy@coderr.test",
        "first_name": "Mara", "last_name": "Schulz",
        "location": "Köln", "tel": "+49 221 1212121",
        "description": "SEO-Texte und Werbetexte für Startups.",
        "working_hours": "Mo-Fr 9-16",
    },
]

CUSTOMERS = [
    {"username": "c_anna",  "email": "anna@coderr.test",
     "first_name": "Anna",  "last_name": "Schmidt"},
    {"username": "c_ben",   "email": "ben@coderr.test",
     "first_name": "Ben",   "last_name": "Hoffmann"},
    {"username": "c_clara", "email": "clara@coderr.test",
     "first_name": "Clara", "last_name": "Weber"},
    {"username": "c_dario", "email": "dario@coderr.test",
     "first_name": "Dario", "last_name": "Albrecht"},
]


OFFER_BLUEPRINTS = {
    "b_designer": [
        {
            "title": "Logo-Design-Paket",
            "description": "Professionelle Logo-Erstellung inkl. Vektorgrafiken.",
            "tiers": [
                {"title": "Basic",    "rev": 1,  "dt":  3, "price": "60.00",
                 "features": ["1 Konzept", "PNG-Export"],
                 "offer_type": "basic"},
                {"title": "Standard", "rev": 3,  "dt":  5, "price": "120.00",
                 "features": ["3 Konzepte", "PNG + SVG", "Farbpalette"],
                 "offer_type": "standard"},
                {"title": "Premium",  "rev": 10, "dt":  7, "price": "280.00",
                 "features": ["5 Konzepte", "PNG + SVG + AI", "Brand-Guide", "Social-Templates"],
                 "offer_type": "premium"},
            ],
        },
        {
            "title": "Visitenkarten-Design",
            "description": "Klassische und moderne Visitenkarten-Layouts.",
            "tiers": [
                {"title": "Basic",    "rev": 1,  "dt":  2, "price": "30.00",
                 "features": ["1 Entwurf", "Druckfertige PDF"],
                 "offer_type": "basic"},
                {"title": "Standard", "rev": 2,  "dt":  3, "price": "55.00",
                 "features": ["2 Entwürfe", "Vorder- und Rückseite"],
                 "offer_type": "standard"},
                {"title": "Premium",  "rev": 5,  "dt":  4, "price": "95.00",
                 "features": ["3 Entwürfe", "Veredelungen", "Mock-up"],
                 "offer_type": "premium"},
            ],
        },
    ],
    "b_developer": [
        {
            "title": "Landingpage in Django",
            "description": "Schnelle, mobile-freundliche Landingpage.",
            "tiers": [
                {"title": "Basic",    "rev": 1,  "dt":  5, "price": "250.00",
                 "features": ["1 Sektion", "Mobile-Optimiert"],
                 "offer_type": "basic"},
                {"title": "Standard", "rev": 3,  "dt":  7, "price": "450.00",
                 "features": ["3 Sektionen", "Kontaktformular", "SEO-Basics"],
                 "offer_type": "standard"},
                {"title": "Premium",  "rev": 10, "dt": 10, "price": "950.00",
                 "features": ["Bis 8 Sektionen", "Admin-Bereich", "Analytics"],
                 "offer_type": "premium"},
            ],
        },
    ],
    "b_translator": [
        {
            "title": "Fachübersetzung DE↔EN",
            "description": "Korrekturlesen durch Muttersprachler inklusive.",
            "tiers": [
                {"title": "Basic",    "rev": 1,  "dt":  2, "price": "40.00",
                 "features": ["Bis 500 Wörter"],
                 "offer_type": "basic"},
                {"title": "Standard", "rev": 2,  "dt":  3, "price": "75.00",
                 "features": ["Bis 1500 Wörter", "Korrektorat"],
                 "offer_type": "standard"},
                {"title": "Premium",  "rev": 5,  "dt":  5, "price": "180.00",
                 "features": ["Bis 5000 Wörter", "Korrektorat", "Fachglossar"],
                 "offer_type": "premium"},
            ],
        },
    ],
    "b_copywriter": [
        {
            "title": "SEO-Blogposts",
            "description": "Keyword-recherchierte Texte für deinen Blog.",
            "tiers": [
                {"title": "Basic",    "rev": 1,  "dt":  3, "price": "50.00",
                 "features": ["1 Artikel à 500 Wörter"],
                 "offer_type": "basic"},
                {"title": "Standard", "rev": 2,  "dt":  4, "price": "95.00",
                 "features": ["1 Artikel à 1000 Wörter", "2 Keywords"],
                 "offer_type": "standard"},
                {"title": "Premium",  "rev": 4,  "dt":  6, "price": "190.00",
                 "features": ["2 Artikel à 1000 Wörter", "Keyword-Recherche"],
                 "offer_type": "premium"},
            ],
        },
    ],
}


# Recipe: (customer_username, business_username, offer_title, tier_type,
#         status, days_ago)
ORDER_RECIPES = [
    ("c_anna",  "b_designer",   "Logo-Design-Paket",    "standard", "completed",   18),
    ("c_anna",  "b_developer",  "Landingpage in Django","basic",    "in_progress",  4),
    ("c_anna",  "b_copywriter", "SEO-Blogposts",        "standard", "completed",   25),

    ("c_ben",   "b_designer",   "Visitenkarten-Design", "premium",  "completed",   31),
    ("c_ben",   "b_designer",   "Logo-Design-Paket",    "basic",    "in_progress",  2),
    ("c_ben",   "b_translator", "Fachübersetzung DE↔EN","basic",    "completed",   12),
    ("c_ben",   "b_translator", "Fachübersetzung DE↔EN","premium",  "cancelled",   40),

    ("c_clara", "b_designer",   "Logo-Design-Paket",    "premium",  "completed",   45),
    ("c_clara", "b_copywriter", "SEO-Blogposts",        "premium",  "in_progress",  1),

    ("c_dario", "b_developer",  "Landingpage in Django","standard", "in_progress",  6),
]

# Recipe: (reviewer_username, business_username, rating, description, days_ago)
REVIEW_RECIPES = [
    ("c_anna",  "b_designer",   5, "Top-Service, blitzschnelle Lieferung!", 17),
    ("c_anna",  "b_copywriter", 4, "Saubere Texte, ein kleiner Tippfehler.", 24),
    ("c_ben",   "b_designer",   5, "Sehr kreativ und kommunikativ.",         30),
    ("c_ben",   "b_translator", 4, "Übersetzung war fachlich exzellent.",    11),
    ("c_clara", "b_designer",   5, "Brandgenau auf den Punkt getroffen.",    44),
    ("c_clara", "b_copywriter", 3, "Inhaltlich okay, Stil etwas generisch.",  3),
]


class Command(BaseCommand):
    """``python manage.py seed_demo_data`` — populate Coderr with demo data."""

    help = "Seed the Coderr database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Delete all coderr data before seeding (or use alone).",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Shortcut for --clear and re-seed in one step.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"] or options["reset"]:
            self._clear()
        if options["clear"] and not options["reset"]:
            self.stdout.write(self.style.SUCCESS("Cleared. Skipping seed."))
            return
        self._seed_users(BUSINESSES, profile_type="business")
        self._seed_users(CUSTOMERS, profile_type="customer")
        self._seed_offers()
        self._seed_orders()
        self._seed_reviews()
        self._summary()

    def _clear(self):
        self.stdout.write("Clearing demo data ...")
        Review.objects.all().delete()
        Order.objects.all().delete()
        OfferDetail.objects.all().delete()
        Offer.objects.all().delete()
        demo_usernames = (
            [u["username"] for u in BUSINESSES]
            + [u["username"] for u in CUSTOMERS]
        )
        User.objects.filter(username__in=demo_usernames).delete()

    def _seed_users(self, users, profile_type):
        for u in users:
            user, created = User.objects.get_or_create(
                username=u["username"],
                defaults={"email": u["email"]},
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            profile = user.profile
            for field in ("first_name", "last_name", "location",
                          "tel", "description", "working_hours"):
                if u.get(field):
                    setattr(profile, field, u[field])
            profile.type = profile_type
            profile.save()
            verb = "created" if created else "updated"
            self.stdout.write(f"  user {verb}: {user.username}")

    def _seed_offers(self):
        for biz_username, blueprints in OFFER_BLUEPRINTS.items():
            biz = User.objects.get(username=biz_username)
            for bp in blueprints:
                offer, created = Offer.objects.get_or_create(
                    user=biz, title=bp["title"],
                    defaults={"description": bp["description"]},
                )
                if not created:
                    continue
                for tier in bp["tiers"]:
                    OfferDetail.objects.create(
                        offer=offer,
                        title=tier["title"],
                        revisions=tier["rev"],
                        delivery_time_in_days=tier["dt"],
                        price=Decimal(tier["price"]),
                        features=tier["features"],
                        offer_type=tier["offer_type"],
                    )
                self.stdout.write(f"  offer created: {biz.username} / {offer.title}")

    def _seed_orders(self):
        for recipe in ORDER_RECIPES:
            customer_un, biz_un, offer_title, tier_type, status, days_ago = recipe
            customer = User.objects.get(username=customer_un)
            biz = User.objects.get(username=biz_un)
            offer = Offer.objects.get(user=biz, title=offer_title)
            detail = offer.details.get(offer_type=tier_type)
            exists = Order.objects.filter(
                customer_user=customer, business_user=biz,
                title=detail.title, offer_type=detail.offer_type,
                price=detail.price,
            ).exists()
            if exists:
                continue
            created_at = timezone.now() - timedelta(days=days_ago)
            order = Order.objects.create(
                customer_user=customer, business_user=biz,
                title=detail.title, revisions=detail.revisions,
                delivery_time_in_days=detail.delivery_time_in_days,
                price=detail.price, features=list(detail.features or []),
                offer_type=detail.offer_type, status=status,
            )
            Order.objects.filter(pk=order.pk).update(
                created_at=created_at, updated_at=created_at,
            )
            self.stdout.write(
                f"  order created: {customer.username} → {biz.username} "
                f"({offer.title}, {tier_type}, {status})"
            )

    def _seed_reviews(self):
        for recipe in REVIEW_RECIPES:
            reviewer_un, biz_un, rating, description, days_ago = recipe
            reviewer = User.objects.get(username=reviewer_un)
            biz = User.objects.get(username=biz_un)
            review, created = Review.objects.get_or_create(
                business_user=biz, reviewer=reviewer,
                defaults={"rating": rating, "description": description},
            )
            if not created:
                continue
            created_at = timezone.now() - timedelta(days=days_ago)
            Review.objects.filter(pk=review.pk).update(
                created_at=created_at, updated_at=created_at,
            )
            self.stdout.write(
                f"  review created: {reviewer.username} → {biz.username} ({rating}★)"
            )

    def _summary(self):
        biz_count = Profile.objects.filter(type="business").count()
        cust_count = Profile.objects.filter(type="customer").count()
        offer_count = Offer.objects.count()
        detail_count = OfferDetail.objects.count()
        order_count = Order.objects.count()
        review_count = Review.objects.count()
        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write("---")
        self.stdout.write(f"  business profiles : {biz_count}")
        self.stdout.write(f"  customer profiles : {cust_count}")
        self.stdout.write(f"  offers            : {offer_count}")
        self.stdout.write(f"  offer details     : {detail_count}")
        self.stdout.write(f"  orders            : {order_count}")
        self.stdout.write(f"  reviews           : {review_count}")
        self.stdout.write(f"  login password    : {PASSWORD!r}")
