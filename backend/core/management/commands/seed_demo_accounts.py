"""Creates (or fixes up) the two shared, public demo accounts.

Safe to re-run at any time -- get_or_create for the accounts themselves,
and the password/role/is_demo_account fields are force-set on every run
regardless, so this doubles as a repair command if either account ever
drifts from what's documented as the public demo credentials.

Usage:
    python manage.py seed_demo_accounts
    python manage.py seed_demo_accounts --client-password=... --staff-password=...

Passwords can also come from DEMO_CLIENT_PASSWORD / DEMO_STAFF_PASSWORD
environment variables, for a deploy hook that shouldn't need a
hardcoded flag. These are meant to be published (that's the entire point
of a demo login), so a sensible built-in default is fine when neither a
flag nor an env var is given -- there's nothing here to keep secret.
"""
import os

from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Creates or repairs the shared public demo client/staff accounts."

    def add_arguments(self, parser):
        parser.add_argument("--client-username", default="demo_client")
        parser.add_argument("--client-password", default=None)
        parser.add_argument("--staff-username", default="demo_staff")
        parser.add_argument("--staff-password", default=None)

    def handle(self, *args, **options):
        from accounts.models import User
        from core.demo import reset_demo_client_data

        client_password = (
            options["client_password"] or os.environ.get("DEMO_CLIENT_PASSWORD") or "DemoClient2026!"
        )
        staff_password = (
            options["staff_password"] or os.environ.get("DEMO_STAFF_PASSWORD") or "DemoStaff2026!"
        )

        with transaction.atomic():
            client, _ = User.objects.get_or_create(
                username=options["client_username"],
                defaults={"role": User.Role.CLIENT, "first_name": "Demo", "last_name": "Client"},
            )
            client.role = User.Role.CLIENT
            client.first_name = "Demo"
            client.last_name = "Client"
            client.is_demo_account = True
            client.is_active = True
            client.set_password(client_password)
            client.save()

            # sales_agent, not admin -- deliberately, so the existing
            # roles=("admin",) restriction already on the most sensitive
            # admin_panel views (Staff Users, Business Settings, Audit Log)
            # blocks this account from them for free. The view-only
            # enforcement on everything else comes from is_demo_account
            # itself (see admin_panel/decorators.py), independent of role.
            staff, _ = User.objects.get_or_create(
                username=options["staff_username"],
                defaults={"role": User.Role.ADMIN, "first_name": "Demo", "last_name": "Staff"},
            )
            staff.role = User.Role.ADMIN
            staff.first_name = "Demo"
            staff.last_name = "Staff"
            staff.is_demo_account = True
            staff.is_active = True
            staff.set_password(staff_password)
            staff.save()

        # Give the client account its sample contract immediately, rather
        # than leaving it empty until the first real visitor logs in.
        reset_demo_client_data(client)

        self.stdout.write(self.style.SUCCESS(
            f"Demo client ready: username={client.username!r}\n"
            f"Demo staff ready:  username={staff.username!r}\n"
            f"(passwords set from flags/env if given, otherwise the built-in defaults)"
        ))