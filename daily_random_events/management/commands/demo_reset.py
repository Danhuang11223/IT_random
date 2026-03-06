import os

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from rest_framework.authtoken.models import Token

from daily_random_events.models import Activity


class Command(BaseCommand):
    help = (
        "Reset database content for demos: migrate, flush, reseed activities, "
        "and optionally recreate a demo admin user."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-admin",
            action="store_true",
            help="Do not create the demo admin account.",
        )
        parser.add_argument(
            "--admin-username",
            default=os.getenv("DEMO_ADMIN_USERNAME", "admin"),
            help="Demo admin username.",
        )
        parser.add_argument(
            "--admin-email",
            default=os.getenv("DEMO_ADMIN_EMAIL", "admin@example.com"),
            help="Demo admin email.",
        )
        parser.add_argument(
            "--admin-password",
            default=os.getenv("DEMO_ADMIN_PASSWORD", "Admin123456!"),
            help="Demo admin password (must be at least 8 chars).",
        )
        parser.add_argument(
            "--skip-seed",
            action="store_true",
            help="Skip activity seed import.",
        )

    def handle(self, *args, **options):
        admin_username = options["admin_username"].strip()
        admin_email = options["admin_email"].strip()
        admin_password = options["admin_password"]

        if not options["skip_admin"]:
            if not admin_username:
                raise CommandError("Admin username cannot be empty.")
            if len(admin_password) < 8:
                raise CommandError("Admin password must be at least 8 characters.")

        self.stdout.write("Applying migrations...")
        call_command("migrate", interactive=False, verbosity=1)

        self.stdout.write("Flushing database data...")
        call_command("flush", interactive=False, verbosity=1)

        if not options["skip_seed"]:
            self.stdout.write("Seeding activities...")
            call_command("seed_activities", verbosity=1)

        token_key = None
        if not options["skip_admin"]:
            self.stdout.write("Creating demo admin account...")
            user_model = get_user_model()
            demo_admin = user_model.objects.create_user(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                is_staff=True,
                is_superuser=True,
                is_active=True,
            )
            token, _ = Token.objects.get_or_create(user=demo_admin)
            token_key = token.key

        summary = [
            f"Activities: {Activity.objects.count()}",
            f"Admin created: {'no' if options['skip_admin'] else 'yes'}",
        ]
        if token_key:
            summary.append(f"Admin token: {token_key}")

        self.stdout.write(self.style.SUCCESS("Demo reset complete."))
        self.stdout.write(" | ".join(summary))
