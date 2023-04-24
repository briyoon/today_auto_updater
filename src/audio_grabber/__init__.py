import logging
import logging.handlers
import os
import subprocess
import streamlink


def _setup_logging() -> logging.Logger:
    """
    Set up a logging instance for the audio grabber.

    Returns:
    - logger (logging.Logger): The logger instance with the configured file handler and formatter.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    os.makedirs('logs', exist_ok=True)

    # Create a rotating file handler to limit the log file size and number of backups
    file_handler = logging.handlers.RotatingFileHandler('logs/audio_grabber.log', maxBytes=10 * 1024 * 1024, backupCount=10)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Initialize the logger automatically at the module level
logger = _setup_logging()


def record_audio(username: str, duration: int, output_file: str) -> None:
    """
    Record audio from a Twitch stream for a specified duration and save it to a file.

    Args:
    - logger (logging.Logger): The logger instance to use for logging
    - username (str): The Twitch username to record from
    - duration (int): The duration of the recording in seconds
    - output_file (str): The path to save the recorded audio file to

    Raises:
    - ValueError: If no streams are found for the given username
    - Exception: If a plugin error occurs during the recording process
    """
    logger.info(f"Recording audio from {username} for {duration} seconds")

    try:
        # Get available stream qualities for the given Twitch username
        streams = streamlink.streams(f"https://twitch.tv/{username}")

        if not streams:
            logger.critical(f"No streams found for {username}")
            raise ValueError(f"No streams found for {username}")

        # Choose the audio-only stream
        audio_only = streams["audio_only"]

        # Generate the ffmpeg command to record the audio, skipping the first 15 seconds (Twitch preroll)
        ffmpeg_command = f"ffmpeg -i {audio_only.url} -ss 15 -vn -acodec copy -t {duration} {output_file} -y"

        # Run the ffmpeg command
        subprocess.run(ffmpeg_command, shell=True, check=True)

    except streamlink.exceptions.NoPluginError:
        logger.critical(f"No plugin found for {username}'s stream")
        raise Exception(f"No plugin found for {username}'s stream")

    except streamlink.exceptions.PluginError as e:
        logger.critical(f"Error in the plugin for {username}: {e}")
        raise Exception(f"Error in the plugin for {username}: {e}")

    except Exception as e:
        logger.critical(f"Error recording audio from {username}: {e}")
        raise


if __name__ == "__main__":
    username = "xqc"
    record_audio(username, 15, f"resources/{username}.aac")
