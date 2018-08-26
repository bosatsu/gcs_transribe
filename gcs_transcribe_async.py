# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Google Cloud Speech API sample application using the REST API for async
batch processing.

Code samples taken from:
https://cloud.google.com/speech-to-text/docs/sync-recognize
https://cloud.google.com/speech-to-text/docs/async-recognize
https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/speech/cloud-client/transcribe_async.py
"""

import argparse
import io
import os
import time
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types


def get_audio(path):
    """Transcribe the given audio file asynchronously."""

    if path.startswith('gs://'):
        audio = types.RecognitionAudio(uri=path)
    else:
        with io.open(path, 'rb') as audio_file:
            content = audio_file.read()
        audio = types.RecognitionAudio(content=content)

    return audio


def get_config(language, rate):
    config = types.RecognitionConfig(
        encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
        sample_rate_hertz=rate,
        language_code=language)

    return config


def write_file(path, language, transcription):
    dir, ext_name = os.path.split(path)
    name, _ = os.path.splitext(ext_name)
    name += '_{}.txt'.format(language)
    with open(name, encoding='utf-8', mode='w+') as f:
        f.write(transcription)
        f.close()
    new_path = os.path.join(dir, name)
    print('Saved transcription to {}'.format(new_path))
    return new_path


def get_wait_time(start_time):
    total_time = round(time.time() - start_time, 2)
    if total_time <= 60:
        wait_time = '{} seconds'.format(total_time)
    elif total_time <= 3600:
        m, s = divmod(total_time, 60)
        wait_time = '{} minutes {} seconds'.format(m, round(s, 2))
    return wait_time


def transcribe_short_audio_file(config, audio):
    client = speech.SpeechClient()

    response = client.recognize(config, audio)
    for result in response.results:
        print(u'Transcript: {}'.format(result.alternatives[0].transcript))


def transcribe_long_audio_file(config, audio):
    client = speech.SpeechClient()

    operation = client.long_running_recognize(config, audio)

    print('Operation sent to Google Cloud for transcription at {}\n'.format(time.ctime()))
    start_time = time.time()
    while operation.done() is not True:
        if (start_time - time.time()) > 43200:
            print('Operation is still running after 12 hours, exiting program')
            exit()
        else:
            print(
                'Waiting for transcription to complete, total operation time is {}\n'.format(get_wait_time(start_time))
            )
            time.sleep(120)

    print('Operation completed at {}\n'.format(time.ctime()))
    print('Total operation time was {}'.format(get_wait_time(start_time)))

    transcription = ''
    for result in operation.result().results:
        transcription += u'{}\n'.format(result.alternatives[0].transcript)
    return transcription


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-p",
        "--path",
        required=True,
        type=str,
        help="File or GCS path for audio file to be recognized"
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default='en-US',
        help='Language contained in the audio file, must follow the BCP-47 format, ex: en-US'
    )
    parser.add_argument(
        "-r",
        "--rate",
        default=44100,
        type=int,
        help='Sampling rate for audio file'
    )
    parser.add_argument(
        "-ln",
        "--length",
        choices=['short', 'long'],
        default='long',
        type=str,
        help='Length of the audio file, options are "short"(1 minute or under) and "long" (over 1 minute)'
    )

    args = parser.parse_args()
    audio = get_audio(args.path)
    config = get_config(args.language, args.rate)

    if args.length == 'short':
        transcription = transcribe_short_audio_file(config, audio)
    else:
        transcription = transcribe_long_audio_file(config, audio)
    write_file(args.path, args.language, transcription)
