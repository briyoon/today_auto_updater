from enum import Enum
from typing import Optional, Tuple, Any, Dict
import time
import os
import logging
import logging.handlers
import requests


class ReponseStatus(Enum):
    """An enumeration representing the different response statuses."""
    USER_ONLINE = 0
    USER_OFFLINE = 1
    USER_NOT_FOUND = 2
    UNAUTHORIZED = 3
    ERROR = 4


class TwitchListener:
    def __init__(self, client_id: str, client_secret: str, sleep_time: int = 60) -> None:
        """Initialize a TwitchListener instance.

        Args:
            client_id (str): Twitch API client ID.
            client_secret (str): Twitch API client secret.
            sleep_time (int, optional): Time (in seconds) to wait between polling user status. Defaults to 60.
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        os.makedirs('logs', exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler('logs/twitch_listener.log', maxBytes=10 * 1024 * 1024, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self.sleep_time = sleep_time

        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_access_token()

    def get_access_token(self) -> str:
        """Get an access token for the Twitch API.

        Returns:
            str: An access token.

        Raises:
            Exception: If unable to get access token.
        """
        try:
            response = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={self.client_id}&client_secret={self.client_secret}&grant_type=client_credentials")
            response.raise_for_status()
            return response.json()['access_token']
        except requests.exceptions.RequestException as e:
            response: Optional[requests.Response] = e.response
            if response:
                status = response.status_code
                message = response.json().get('message', response.text)
                self.logger.critical(f"Error getting access token ({status}): {message}")
                raise Exception(f"Error getting access token ({status}): {message}")
            else:
                self.logger.critical(f"Error getting access token: {e}")
                raise Exception(f"Error getting access token: {e}")

    def get_user_status(self, username: str) -> Tuple[Optional[Dict[str, Any]], ReponseStatus]:
        """Check the online status of a Twitch user.

        Args:
            username (str): The username of the Twitch user.

        Returns:
            Tuple[Optional[Dict[str, Any]], ReponseStatus]: A tuple containing the user's information (if available) and the corresponding ReponseStatus value.
        """
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Client-ID': self.client_id,
        }
        params = {
            'user_login': username,
            'type': 'live'
        }
        response = requests.get('https://api.twitch.tv/helix/streams', headers=headers, params=params)

        if response.status_code == 200:
            response_data = response.json()
            if response_data['data']:
                return response_data, ReponseStatus.USER_ONLINE
            return None, ReponseStatus.USER_OFFLINE
        elif response.status_code == 401:
            return None, ReponseStatus.UNAUTHORIZED
        elif response.status_code == 404:
            return None, ReponseStatus.USER_NOT_FOUND
        else:
            self.logger.error(f"Error retrieving user status for {username} ({response.status_code}): {response.text}")
            return None, ReponseStatus.ERROR

    def wait_for_user(self, username: str, last_stream_id: int) -> str:
        """Wait for a Twitch user to go online.

        Args:
            username (str): The username of the Twitch user.

        Returns:
            str: The user's ID if they go online.

        Raises:
            Exception: If the user is not found or unable to get access token after 3 attempts.
        """
        unauthorized_attempts = 0
        while True:
            info, status = self.get_user_status(username)

            if status == ReponseStatus.USER_ONLINE:
                if last_stream_id == info['data'][0]['id']:
                    self.logger.info(f"{username} is still live, sleeping for {self.sleep_time} seconds")
                    time.sleep(self.sleep_time)
                else:
                    self.logger.info(f"{username} is online!")
                return info['data'][0]['id']
            elif status == ReponseStatus.USER_OFFLINE:
                self.logger.info(f"{username} is offline, sleeping for {self.sleep_time} seconds")
                time.sleep(self.sleep_time)
                unauthorized_attempts = 0
            elif status == ReponseStatus.USER_NOT_FOUND:
                self.logger.critical(f"{username} not found!")
                raise Exception(f"{username} not found!")
            elif status == ReponseStatus.UNAUTHORIZED:
                self.logger.error(f"Unauthorized request, grabbing new access token")
                self.access_token = self.get_access_token()
                unauthorized_attempts += 1
                if unauthorized_attempts >= 3:
                    self.logger.critical(f"Unable to get access token after 3 attempts")
                    raise Exception(f"Unable to get access token after 3 attempts")
