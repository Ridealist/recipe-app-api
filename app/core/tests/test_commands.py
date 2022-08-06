from unittest.mock import patch

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import TestCase

from psycopg2.errors import OperationalError as Psycopg2_OpError


@patch("core.management.commands.wait_for_db.Command.check")
class CommandsTests(TestCase):
    def test_wait_for_db_ready(self, patched_check):
        """Test waiting for db when db is available"""
        # with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
        # gi.return_value = True
        patched_check.return_value = True
        call_command("wait_for_db")
        self.assertEqual(patched_check.call_count, 1)
        patched_check.assert_called_once_with(databases=["default"])

    @patch("time.sleep", return_value=True)
    def test_wait_for_db(self, patched_time, patched_check):
        """Test waiting for db"""
        # with patch('django.db.utils.ConnectionHandler.__getitem__') as gi:
        patched_check.side_effect = (
            [OperationalError] * 3 + [Psycopg2_OpError] * 3 + [True]
        )
        patched_check.return_value = True
        call_command("wait_for_db")
        self.assertEqual(patched_check.call_count, 7)
        patched_check.assert_called_with(databases=["default"])
