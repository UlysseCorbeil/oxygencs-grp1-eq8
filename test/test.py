import json
import unittest
from unittest.mock import patch, MagicMock
from src.main import App
import os


class TestApp(unittest.TestCase):

    # Setup override to init mock data
    def setUp(self):
        # Directly set environment variables
        os.environ["HOST"] = "http://test.com"
        os.environ["DB_USER"] = "test user"
        os.environ["TOKEN"] = "this_is_a_token"
        os.environ["T_MAX"] = "80"
        os.environ["T_MIN"] = "20"
        os.environ["DATABASE_URL"] = "test_db"
        os.environ["DB_PWD"] = "password"
        os.environ["DB_PORT"] = "5432"
        os.environ["DB_NAME"] = "db_name"

        # Now initialize your App
        self.app = App()

    # Override teardown
    def tearDown(self):
        del os.environ["HOST"]
        del os.environ["DB_USER"]
        del os.environ["TOKEN"]
        del os.environ["T_MAX"]
        del os.environ["T_MIN"]
        del os.environ["DATABASE_URL"]
        del os.environ["DB_PWD"]
        del os.environ["DB_PORT"]
        del os.environ["DB_NAME"]

    # Mock env variables
    def test_env_vars(self):
        self.assertEqual(self.app.HOST, "http://test.com")
        self.assertEqual(self.app.TOKEN, "this_is_a_token")
        self.assertEqual(self.app.T_MAX, "80")
        self.assertEqual(self.app.T_MIN, "20")
        self.assertEqual(self.app.DATABASE_URL, "test_db")
        self.assertEqual(self.app.USER, "test user")

    @patch("src.main.App.send_action_to_hvac")
    def test_take_action_turn_on_ac(self, mock_method):
        self.app.take_action(float(self.app.T_MAX) + 1)
        mock_method.assert_called_once_with("TurnOnAc")

    @patch("src.main.App.send_action_to_hvac")
    def test_take_action_turn_on_heater(self, mock_method):
        self.app.take_action(float(self.app.T_MIN) - 1)
        mock_method.assert_called_once_with("TurnOnHeater")

    @patch("requests.get")
    def test_send_action_to_hvac(self, mock_method):
        action = "TurnOnAc"

        self.app.send_action_to_hvac(action)
        mock_method.assert_called_once_with(
            f"{self.app.HOST}/api/hvac/{self.app.TOKEN}/TurnOnAc/{self.app.TICKS}"
        )

    @patch("psycopg2.connect")
    def test_save_event_to_database(self, mock_method):

        # Setup mock connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_method.return_value = mock_connection
        mock_connection.cursor.return_value = mock_cursor

        self.app.save_event_to_database("2021-01-01 00:00:00", -10)

        mock_method.assert_called_with(
            database=self.app.DB_NAME,
            host=self.app.DATABASE_URL,
            user=self.app.USER,
            password=self.app.PASSWORD,
            port=self.app.DB_PORT,
        )

        mock_cursor.execute.assert_called_once_with(
            "INSERT INTO rt_temperatures (timestamp, c_temp, ac_activated, heater_activated) VALUES (%s, %s, %s, %s)",
            (
                "2021-01-01 00:00:00",
                -10,
                self.app.ac_activated,
                self.app.heater_activated,
            ),
        )

        mock_connection.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
