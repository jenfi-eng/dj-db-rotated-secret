from django.conf import settings
from django.db import connection, connections
from django.test import TransactionTestCase, override_settings

from example_project.posts.models import Post
from example_project.posts.tests.factories import PostFactory


def get_rotated_creds():
    return {
        "username": TestDbPwRotated.rotate_pw_username,
        "password": TestDbPwRotated.rotated_password,
    }


@override_settings(DJ_DB_ROTATED_SECRET_FUNC="example_project.tests.test_db_pw_rotated.get_rotated_creds")
class TestDbPwRotated(TransactionTestCase):
    databases = {"default", "original"}  # Add this line to allow both connections
    rotate_pw_username = "rotate_pw_user"
    initial_password = "initial_password"
    rotated_password = "rotated_password"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.original_db_settings = settings.DATABASES["default"].copy()

    def setUp(self):
        with connection.cursor() as cur:
            self.remove_test_user()

            # Create new user
            cur.execute(f"CREATE USER {self.rotate_pw_username} WITH PASSWORD '{self.initial_password}';")

            # Grant necessary permissions
            cur.execute(
                f"GRANT ALL PRIVILEGES ON DATABASE {settings.DATABASES['default']['NAME']} TO {self.rotate_pw_username};"  # noqa E501
            )
            cur.execute(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {Post._meta.db_table} TO {self.rotate_pw_username};"
            )
            cur.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {self.rotate_pw_username};")
            cur.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {self.rotate_pw_username};")

        connection.commit()

        # Switch to the new user
        settings.DATABASES["default"]["USER"] = self.rotate_pw_username
        settings.DATABASES["default"]["PASSWORD"] = self.initial_password

        # Close existing connections to force new connections with the new user
        connections.close_all()

        connections["default"].connect()

    def tearDown(self):
        # Restore original database settings
        settings.DATABASES["default"]["USER"] = self.original_db_settings["USER"]
        settings.DATABASES["default"]["PASSWORD"] = self.original_db_settings["PASSWORD"]

        connections.close_all()

        connections["default"].connect()

    def remove_test_user(self):
        # Connect with the original user and remove the test user
        with connection.cursor() as cur:
            cur.execute(f"DROP USER IF EXISTS {self.rotate_pw_username};")
            connection.commit()

    # --------------------------------------------
    # Actual Tests
    # --------------------------------------------

    def test_db_pw_rotated(self):
        # Create a Post, simply ensure the basic connection works
        PostFactory()

        assert Post.objects.count() == 1

        # Ensure we're connected as the new user
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]
        assert current_user == self.rotate_pw_username

        # Use a the sparate, but 'original' connection to change the password
        with connections["original"].cursor() as cursor:
            cursor.execute(f"ALTER USER {self.rotate_pw_username} WITH PASSWORD '{self.rotated_password}';")

        # Force a reconnect
        connections.close_all()

        # Try to connect with the old password (should fail)
        with self.assertRaises(Exception) as context:
            connections["default"].connect()
        self.assertIn("password authentication failed", str(context.exception).lower())

        # Finally, import the monkey patch handler and allow it to work!
        import dj_db_rotated_secret  # noqa F401

        PostFactory()

        # Verify that the new connection works
        assert Post.objects.count() == 2
