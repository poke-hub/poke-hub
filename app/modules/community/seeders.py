from app.modules.auth.models import User
from app.modules.community.models import Community
from core.seeders.BaseSeeder import BaseSeeder


class CommunitySeeder(BaseSeeder):

    def run(self):

        demo_user1 = User.query.filter_by(email="user1@example.com").first()
        demo_user2 = User.query.filter_by(email="user2@example.com").first()

        data = [
            Community(
                name="Dragons",
                description="A community for the dragon type pokemon.",
                logo_path="/img/logos/dragon-logo.jpeg",
                banner_path="/img/banners/dragon-banner.jpeg",
                curators=[demo_user1] if demo_user1 else [],
                members=[demo_user2] if demo_user2 else [],
            ),
            Community(
                name="Grass",
                description="Datasets related to our green peaceful friends.",
                logo_path="/img/logos/grass-logo.jpeg",
                banner_path="/img/banners/grass-banner.jpeg",
                curators=[demo_user1] if demo_user1 else [],
            ),
            Community(
                name="Poke-hub research",
                description="Community for Poke-Hub research, Poke-Hub models, and variability datasets.",
                logo_path="/img/logos/logo_pokehub.png",
                banner_path="/img/logos/logo_pokehub.png",
                curators=[demo_user2] if demo_user2 else [],
                members=[demo_user1] if demo_user1 else [],
            ),
            Community(
                name="Public Institutions",
                description="Datasets published by international and national institutions.",
                logo_path=None,
                banner_path=None,
            ),
            Community(
                name="Education & Teaching",
                description="Material, datasets, and resources aimed at supporting teaching and academic studies.",
            ),
        ]

        self.seed(data)
