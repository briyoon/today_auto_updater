import argparse
import os
import time

from dotenv import load_dotenv
import whisper

import audio_grabber
from twitch_listener import TwitchListener

def parse_args():
    parser = argparse.ArgumentParser(description='Run the program')
    parser.add_argument('--user', help='User to grab the audio from')
    parser.add_argument('--listen_time', default=900, help='How much audio to grab in seconds')
    parser.add_argument('--prompt', help='Prompt used to help give chatGPT context on a streamer for the summary')
    return parser.parse_args()

def main(args):
    twitch_listener = TwitchListener(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))
    model = whisper.load_model('base.en')
    last_stream_id = None
    while True:
        # wait for user to go live, only look for a new stream
        stream_id = twitch_listener.wait_for_user(args.user, last_stream_id)
        if stream_id == last_stream_id:
            continue

        last_stream_id = stream_id

        # get audio
        audio_grabber.record_audio(args.user, args.listen_time, f"resources/{args.user}.aac")

        # transcribe
        transcript = model.transcribe(f"resources/{args.user}.aac")['text']

        # summarize
        print(transcript)

        # update command

if __name__ == '__main__':
    args = parse_args()
    load_dotenv()
    main(args)