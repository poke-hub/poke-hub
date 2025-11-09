from app.modules.auth.models import User
from app.modules.auth.services import AuthenticationService, encrypt_data
from app.modules.profile.models import UserProfile
from core.seeders.BaseSeeder import BaseSeeder
from flask import current_app

class AuthSeeder(BaseSeeder):

    priority = 1  # Higher priority

    def run(self):

        # Seeding users
        users = [
            User(email="user1@example.com", password="1234"),
            User(email="user2@example.com", password="1234"),
        ]

        # Inserted users with their assigned IDs are returned by `self.seed`.
        seeded_users = self.seed(users)

        # Create profiles for each user inserted.
        user_profiles = []
        names = [("John", "Doe"), ("Jane", "Doe")]

        for user, name in zip(seeded_users, names):
            profile_data = {
                "user_id": user.id,
                "orcid": "",
                "affiliation": "Some University",
                "name": name[0],
                "surname": name[1],
            }
            user_profile = UserProfile(**profile_data)
            user_profiles.append(user_profile)

        # Seeding user profiles
        self.seed(user_profiles)


        # Usuario para tests de 2FA
        KNOWN_2FA_SECRET = "5JEIF3ANYS7UJKZEN7PZJFG5RHTNRPR2" # Clave conocida para tests

        encrypted_secret = None
        hashed_codes = None

        with current_app.app_context():
            encrypted_secret = encrypt_data(KNOWN_2FA_SECRET)
            
            auth_service = AuthenticationService()
            _, hashed_codes = auth_service.generate_recovery_codes()

        user_2fa = User(
            email="test@example.com",
            password="test1234", 
            is_two_factor_enabled=True,
            two_factor_secret=encrypted_secret, 
            two_factor_recovery_codes=hashed_codes
        )
        
        seeded_2fa_user = self.seed([user_2fa])

        profile_data_2fa = {
            "user_id": seeded_2fa_user[0].id,
            "name": "Test",
            "surname": "User",
        }
        user_profile_2fa = UserProfile(**profile_data_2fa)
        self.seed([user_profile_2fa])