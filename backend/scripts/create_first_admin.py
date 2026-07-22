"""
One-time bootstrap: creates the very first admin account.

There's a chicken-and-egg problem otherwise — account creation is
admin-only (POST /api/v1/admin/users), but you need an admin to call
that. Run this script once, directly, to create that first admin.
After that, log in as this admin and use the app (or POST
/api/v1/admin/users) to create doctor/radiologist/other admin accounts.

Usage (from the backend/ directory, with your .env already filled in):

    python -m scripts.create_first_admin
"""

import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings  # noqa: E402
from supabase import create_client  # noqa: E402


def main():
    settings = get_settings()
    admin_auth = create_client(settings.SUPABASE_URL, settings.SUPABASE_LEGACY_SERVICE_ROLE_JWT)
    db = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)

    print("Create the first admin account\n")
    email = input("Email: ").strip()
    password = getpass.getpass("Password (min 8 chars): ")
    full_name = input("Full name: ").strip()

    if len(password) < 8:
        print("Password must be at least 8 characters.")
        return

    auth_result = admin_auth.auth.admin.create_user(
        {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"full_name": full_name, "role": "admin"},
            "app_metadata": {"role": "admin"},
        }
    )
    user_id = auth_result.user.id

    db.table("users").insert(
        {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": "admin",
        }
    ).execute()

    print(f"\nDone. Admin account created for {email}. Log in at /api/v1/auth/login.")


if __name__ == "__main__":
    main()
