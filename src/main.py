import argparse
import os

from dotenv import load_dotenv
import whisper

from twitch_audio_listener import TwitchAudioListener

def parse_args():
    parser = argparse.ArgumentParser(description='Run the program')
    parser.add_argument('--user', help='User to grab the audio from')
    parser.add_argument('--listen_time', default=15, help='How much audio to grab in minutes')
    parser.add_argument('--prompt', help='Prompt used to help give chatGPT context on a streamer for the summary')
    return parser.parse_args()

def main(args):
    audio_listener = TwitchAudioListener(os.getenv('TWITCH_CLIENT_ID'), os.getenv('TWITCH_CLIENT_SECRET'))
    model = whisper.load_model('base.en')
    while True:
        # get audio
        audio_listener.record_audio(args.user, args.listen_time, f"resources/{args.user}.aac")
        # transcribe
        transcript = model.transcribe(f"resources/{args.user}.aac")['text']
        # summarize

        # update command

if __name__ == '__main__':
    args = parse_args()
    load_dotenv()
    main(args)