from enum import Enum
import logging
from typing import Optional
import time
import os
import requests
import streamlink


class ReponseStatus(Enum):
    """An enumeration representing the different response statuses."""
    USER_ONLINE = 0
    USER_OFFLINE = 1
    USER_NOT_FOUND = 2
    UNAUTHORIZED = 3
    ERROR = 4


class TwitchAudioListener:
    def __init__(self, client_id, client_secret, sleep_time=30, recording_duration=15):
        ### LOGGING ###
        # Logging setup
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Add a RotatingFileHandler to rotate the log file based on size
        file_handler = logging.handlers.TimedRotatingFileHandler('twitch_audio_listener_%Y%m%d.log', when='midnight', interval=1, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        ### TIMEOUT ###
        if sleep_time < 15:
            self.logger.warning("Sleep time is less than 15 seconds, setting to 15 seconds")
            sleep_time = 15
        self.sleep_time = sleep_time
        self.record_duration = recording_duration
        self.last_stream_id = None

        ### TWITCH API AUTH ###
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = self.get_access_token()

    def get_access_token(self):
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

    def wait_for_user(self, username):
        unauthorized_attempts = 0
        while True:
            info, status = self.get_user_status(username)

            if status == ReponseStatus.USER_ONLINE:
                self.logger.info(f"{username} is online! Now recording audio for {self.record_duration} seconds")
                return info['data'][0]['id']
            elif status == ReponseStatus.USER_OFFLINE:
                self.logger.info(f"{username} is offline, sleeping for {self.sleep_time} seconds")
                time.sleep(self.sleep_time)
                unauthorized_attempts = 0
            elif status == ReponseStatus.USER_NOT_FOUND:
                self.logger.critical(f"{username} not found!")
                raise Exception(f"{username} not found!")
            elif status == ReponseStatus.UNAUTHORIZED: # need to grab new access token, if unauthorized 3 times in a row, raise exception
                self.logger.error(f"Unauthorized request, grabbing new access token")
                self.access_token = self.get_access_token()
                unauthorized_attempts += 1
                if unauthorized_attempts >= 3:
                    self.logger.critical(f"Unable to get access token after 3 attempts")
                    raise Exception(f"Unable to get access token after 3 attempts")

    def get_user_status(self, username):
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
            else:
                return None, ReponseStatus.USER_OFFLINE
        elif response.status_code == 401:
            return None, ReponseStatus.UNAUTHORIZED
        elif response.status_code == 404:
            return None, ReponseStatus.USER_NOT_FOUND
        else:
            self.logger.error(f"Error retrieving user status for {username} ({response.status_code}): {response.text}")
            return None, ReponseStatus.ERROR

    def get_audio_from_twitch_stream(self, username, duration, output_file):
        try:
            # Get available stream qualities
            streams = streamlink.streams(f"https://twitch.tv/{username}")

            # Choose the best quality available
            audio_only = streams["audio_only"]

            # Generate the ffmpeg command
            ffmpeg_command = f"ffmpeg -i {audio_only.url} -vn -acodec copy -t {duration} {output_file} -y"

            # Run the ffmpeg command
            os.system(ffmpeg_command)

        except streamlink.exceptions.NoPluginError:
            self.logger.critical(f"No plugin found for {username}'s stream")
            raise Exception(f"No plugin found for {username}'s stream")

        except streamlink.exceptions.PluginError as e:
            self.logger.critical(f"Error in the plugin: {str(e)}")
            raise Exception(f"Error in the plugin: {str(e)}")

    def trim_audio(self, input_file, output_file, start_time, end_time):
        ffmpeg_command = f"ffmpeg -i {input_file} -ss {start_time} -to {end_time} -c copy {output_file} -y"
        os.system(ffmpeg_command)
        os.rename(output_file, input_file)

    def record_audio(self, username, duration, output_file):
        stream_id = self.wait_for_user(username)
        if stream_id != self.last_stream_id:
            self.last_stream_id = stream_id
            self.logger.info(f"Recording audio from {username} for {duration} seconds")
            self.get_audio_from_twitch_stream(username, duration, output_file)
