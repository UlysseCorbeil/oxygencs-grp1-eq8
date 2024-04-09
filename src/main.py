from signalrcore.hub_connection_builder import HubConnectionBuilder
import logging
import requests
import json
import time
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class App:
    def __init__(self):
        self._hub_connection = None
        self.TICKS = 10

        # To be configured by your team
        self.HOST = os.getenv("HOST")  # Setup your host here
        self.TOKEN = os.getenv("TOKEN")  # Setup your token here
        self.T_MAX = os.getenv("T_MAX")  # Setup your max temperature here
        self.T_MIN = os.getenv("T_MIN")  # Setup your min temperature here
        self.DATABASE_URL = os.getenv("DATABASE_URL")  # Setup your database here

        self.USER = os.getenv("DB_USER")
        self.PASSWORD = os.getenv("DB_PWD")
        self.DB_PORT = os.getenv("DB_PORT")
        self.DB_NAME = os.getenv("DB_NAME")

        self.db_connection = None

        self.ac_activated = False
        self.heater_activated = False

    def __del__(self):
        if self._hub_connection != None:
            self._hub_connection.stop()

    def start(self):
        """Start Oxygen CS."""
        self.setup_sensor_hub()
        self._hub_connection.start()
        self.db_connection = psycopg2.connect(
            database=self.DB_NAME,
            host=self.DATABASE_URL,
            user=self.USER,
            password=self.PASSWORD,
            port=self.DB_PORT,
        )
        print("Press CTRL+C to exit.")
        while True:
            time.sleep(2)

    def setup_sensor_hub(self):
        """Configure hub connection and subscribe to sensor data events."""
        self._hub_connection = (
            HubConnectionBuilder()
            .with_url(f"{self.HOST}/SensorHub?token={self.TOKEN}")
            .configure_logging(logging.INFO)
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                    "max_attempts": 999,
                }
            )
            .build()
        )
        self._hub_connection.on("ReceiveSensorData", self.on_sensor_data_received)
        self._hub_connection.on_open(lambda: print("||| Connection opened."))
        self._hub_connection.on_close(lambda: print("||| Connection closed."))
        self._hub_connection.on_error(
            lambda data: print(f"||| An exception was thrown closed: {data.error}")
        )

    def on_sensor_data_received(self, data):
        """Callback method to handle sensor data on reception."""
        try:
            print(data[0]["date"] + " --> " + data[0]["data"], flush=True)
            timestamp = data[0]["date"]
            temperature = float(data[0]["data"])
            self.take_action(temperature)
            self.save_event_to_database(timestamp, temperature)
        except Exception as err:
            print(err)

    def take_action(self, temperature):
        """Take action to HVAC depending on current temperature."""
        if float(temperature) >= float(self.T_MAX):
            self.send_action_to_hvac("TurnOnAc")
            self.ac_activated = True
        elif float(temperature) <= float(self.T_MIN):
            self.send_action_to_hvac("TurnOnHeater")
            self.heater_activated = True
        else:
            self.ac_activated = False
            self.heater_activated = False

    def send_action_to_hvac(self, action):
        """Send action query to the HVAC service."""
        r = requests.get(f"{self.HOST}/api/hvac/{self.TOKEN}/{action}/{self.TICKS}")
        details = json.loads(r.text)
        print(details, flush=True)

    def save_event_to_database(self, timestamp, temperature):
        """Save sensor data into database."""
        try:
            cursor = self.db_connection.cursor()

            cursor.execute(
                "INSERT INTO rt_temperatures (timestamp, c_temp, ac_activated, heater_activated) VALUES (%s, %s, %s, %s)",
                (timestamp, temperature, self.ac_activated, self.heater_activated),
            )

            self.db_connection.commit()
        except requests.exceptions.RequestException as e:
            print(e)
            if self.connection:
                cursor.close()
                self.connection.close()


if __name__ == "__main__":
    app = App()
    app.start()
