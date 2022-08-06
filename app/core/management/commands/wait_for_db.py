import time

from psycopg2 import OperationalError as Psycopg2_OpError

# from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to pause execution until db is available"""

    def handle(self, *args, **options):
        self.stdout.write("Waiting for database...")
        db_check = False
        # db_conn = None
        while db_check is False:
            # while not db_conn:
            try:
                # db_conn = connections["default"]
                self.check(databases=["default"])
                db_check = True
            except (Psycopg2_OpError, OperationalError):
                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
