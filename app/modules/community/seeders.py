from core.seeders.BaseSeeder import BaseSeeder
from app.modules.community.models import Community
from app.modules.auth.models import User
from app import db


class CommunitySeeder(BaseSeeder):

    def run(self):

        demo_user1 = User.query.filter_by(email="user1@example.com").first()
        demo_user2 = User.query.filter_by(email="user2@example.com").first()

        data = [

            Community(
                name="Dragons",
                description="A community for the dragon type pokemon.",
                logo_path="https://d2bzx2vuetkzse.cloudfront.net/fit-in/0x450/unshoppable_producs/287a2ca2-4c4c-42cb-a74e-2a1795dd399e.png",
                banner_path="https://i.ytimg.com/vi/0dwjy-0uFVI/maxresdefault.jpg",
                curators=[demo_user1] if demo_user1 else [],
                members=[demo_user2] if demo_user2 else []
            ),

            Community(
                name="Grass",
                description="Datasets related to our green peaceful friends.",
                logo_path="https://d2bzx2vuetkzse.cloudfront.net/fit-in/0x450/unshoppable_producs/f12463d4-3da4-482b-ba9b-c080ba913f9c.png",
                banner_path="https://cdn.mos.cms.futurecdn.net/hFJe5P2C7yBNEb44jdpC43-1200-80.jpg",
                curators=[demo_user1] if demo_user1 else [],
            ),

            Community(
                name="Software Product Lines",
                description="Community for SPL research, feature models, and variability datasets.",
                logo_path="static/img/community/spl_logo.png",
                banner_path="static/img/community/spl_banner.jpg",
                curators=[demo_user2] if demo_user2 else [],
                members=[demo_user1] if demo_user1 else []
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
