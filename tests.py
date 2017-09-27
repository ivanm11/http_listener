import json
import threading
import unittest

import requests

from client import Handler
from client import ThreadedHTTPServer


TEST_PORT = 8881
BASE_URL = 'http://localhost:{}'.format(TEST_PORT)
WAV_URL = '{}/wav-info?wavkey=test_103.wav'.format(BASE_URL)
WAV_RESPONSE = {"execution_time": 40.0, "channel_count": 1, "sample_rate": 22050}
MP3_URL = '{}/mp3-to-wav?mp3key=test_102.mp3&wavkey=unittest.wav'.format(BASE_URL)
MP3_RESPONSE = {"execution_time": 40.05, "file_size": 1766060}


class HTTPServerTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadedHTTPServer(('localhost', TEST_PORT), Handler)
        threading.Thread(target=cls.server.serve_forever).start()
        # cls.server.serve_forever()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_response_with_headers(self):
        resp = requests.get(BASE_URL, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(200, resp.status_code)
        self.assertEqual('{}', resp.content.decode())

    def test_response_without_headers(self):
        resp = requests.get(BASE_URL)
        self.assertEqual(401, resp.status_code)

    def test_response_without_headers_wav(self):
        resp = requests.get(WAV_URL)
        self.assertEqual(401, resp.status_code)

    def test_response_without_headers_mp3(self):
        resp = requests.get(MP3_URL)
        self.assertEqual(401, resp.status_code)

    def test_response_with_wrong_headers(self):
        resp = requests.get(BASE_URL, headers={'Authorization': 'UAR-20172017'})
        self.assertEqual(401, resp.status_code)

    def test_response_wav(self):
        resp = requests.get(WAV_URL, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(200, resp.status_code)
        self.assertEqual(WAV_RESPONSE, json.loads(resp.content.decode()))

    def test_response_wav_wrong_query_param(self):
        url = WAV_URL.replace('wavkey', 'waffkey')
        resp = requests.get(url, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(500, resp.status_code)

    def test_response_wav_wrong_s3_key_name(self):
        url = WAV_URL.replace('test_103.wav', '12345609_test_980.wav')
        resp = requests.get(url, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(500, resp.status_code)

    def test_response_mp3(self):
        resp = requests.get(MP3_URL, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(200, resp.status_code)
        self.assertEqual(MP3_RESPONSE, json.loads(resp.content.decode()))

    def test_response_mp3_wrong_query_param(self):
        url = MP3_URL.replace('mp3key', 'mp47key')
        resp = requests.get(url, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(500, resp.status_code)

    def test_response_mp3_wrong_s3_key_name(self):
        url = MP3_URL.replace('test_102.mp3', '12345609_test_98021.mp3')
        resp = requests.get(url, headers={'Authorization': 'UAR-2017'})
        self.assertEqual(500, resp.status_code)


if __name__ == '__main__':
    unittest.main()