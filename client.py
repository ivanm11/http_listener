import argparse
import json
import os
import wave
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import parse_qs
from urllib.parse import urlparse
from uuid import uuid4

import boto.s3
from boto.s3.key import Key
from boto.exception import S3ResponseError
from pydub import AudioSegment

from config import ACCESS_KEY
from config import SECRET_KEY

BUCKET_FOLDER = 'cdt-925b'

s3_connection = boto.s3.connect_to_region(
    'us-east-2',
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY
)
s3_bucket = s3_connection.get_bucket('uar-patrick-code-test')


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # check authorization
        headers = self.headers
        if 'Authorization' not in headers or headers['Authorization'] != 'UAR-2017':
            self.send_response(401)
            self.end_headers()
            return

        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)

        data={}
        # WAV
        if parsed_url.path == '/wav-info':
            if not 'wavkey' in query_params:
                self.send_response(500)
                self.end_headers()
                return
            wav_name = query_params['wavkey'][0]
            full_wav_name = os.path.join(BUCKET_FOLDER, wav_name)
            key = Key(s3_bucket)
            key.key = full_wav_name
            try:
                key.open()
            except S3ResponseError:
                self.send_response(500)
                self.end_headers()
                return

            wav_obj = wave.open(key, 'r')
            params = wav_obj.getparams()
            # duration = number of frames / framerate (frames per second)
            data = {
                'channel_count': params.nchannels,  # wav_obj.getnchannels(),
                'sample_rate': params.framerate,  # wav_obj.getframerate(),
                'execution_time': round((params.nframes / params.framerate), 2)
            }
        # MP3
        elif parsed_url.path == '/mp3-to-wav':
            if not 'wavkey' in query_params or not 'mp3key' in query_params:
                self.send_response(500)
                self.end_headers()
                return
            mp3_name = query_params['mp3key'][0]
            wav_name = query_params['wavkey'][0]
            full_mp3_name = os.path.join(BUCKET_FOLDER, mp3_name)
            full_wav_name = os.path.join(BUCKET_FOLDER, wav_name)
            key = Key(s3_bucket)
            key.key = full_mp3_name
            try:
                key.open()
            except S3ResponseError:
                self.send_response(500)
                self.end_headers()
                return

            sound = AudioSegment.from_mp3(key)
            tmp_file_path = '/tmp/{}'.format(uuid4())
            with sound.export(tmp_file_path, format="wav"):  # avoid `ResourceWarning: unclosed file` warning
                pass
            k = s3_bucket.new_key(full_wav_name)
            k.set_contents_from_filename(tmp_file_path)

            wav_obj = wave.open(tmp_file_path, 'r')
            params = wav_obj.getparams()
            # duration = number of frames / framerate (frames per second)
            data = {
                'file_size': os.path.getsize(tmp_file_path),
                'execution_time': round((params.nframes / params.framerate), 2)
            }

        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
        return


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='multi-threaded HTTP listener')
    parser.add_argument('-p', '--port', help='port', required=True)
    args = vars(parser.parse_args())
    port = int(args['port'])
    server = ThreadedHTTPServer(('localhost', port), Handler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
