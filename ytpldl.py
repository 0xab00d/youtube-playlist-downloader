import re
import os
import sys
from argparse import ArgumentParser
from datetime import datetime

import pafy
import pydub


class Track(object):
    def __init__(self, url):
        self.url = url
        self.song = pafy.new(url)
        self.title = clean(self.song.title)
        self.description = self.song.description
        self.length = self.song.length
        self.timestamps = []
        self.output = os.path.abspath(args.output)
        self.multitrack = self.is_multitrack()
        self.stream = self.song.getbestaudio()

    def download(self):
        print_info('Downloading %s' % self.title)
        if self.multitrack:
            path = self.download_multitrack()
            if path:
                self.split_multitrack(path)
        else:
            self.download_singletrack()

    def download_singletrack(self):
        if create_directory('%s' % (self.output)):
            path = self.download_audio('%s/%s.%s' % (self.output, self.title, self.stream.extension))
            track = pydub.AudioSegment.from_file(path, self.stream.extension)
            track.export('%s/%s.mp3' % (os.path.dirname(path), self.title), format='mp3', bitrate='320k')
            os.remove('%s/%s.%s' % (self.output, self.title, self.stream.extension))

    def download_multitrack(self):
        if create_directory('%s/%s' % (self.output, self.title)):
            return self.download_audio('%s/%s/%s.%s' % (self.output, self.title, self.title, self.stream.extension))

    def download_audio(self, path):
        if not os.path.exists(path):
            self.stream.download(filepath=path, quiet=True)
        return path

    def split_multitrack(self, path):
        track = pydub.AudioSegment.from_file(path, self.stream.extension)
        previous_time = 0
        for count, (timestamp, title) in enumerate(self.timestamps):
            try:
                song = track[timestamp:self.timestamps[count+1][0]]
            except IndexError:
                song = track[timestamp:]
            song.export('%s/%s.mp3' % (os.path.dirname(path), title), format='mp3', bitrate='320k')
        os.remove(path)

    def is_multitrack(self):
        if self.length > 10 * 60:
            self.tracks = re.findall(r'(?:((?:[0-9]\:)?(?:[0-9]{2}\:[0-9]{2}))(.*?)(?:\n|$))|'
                                      '(?:(.*?)((?:[0-9]{1,2}\:)?(?:[0-9]{1,2}\:[0-9]{1,2})))', self.description)
            if self.tracks:
                self.get_timestamps()
                return True

    def get_timestamps(self):
        if not self.tracks[0][0]:
            for ts in self.tracks:
                self.timestamps.append((normalise(ts[3]), clean(ts[2].strip())))
        else:
            for ts in self.tracks:
                self.timestamps.append((normalise(ts[0]), clean(ts[1].strip())))


def get_urls(url):
    playlist = pafy.get_playlist(url)
    return ['https://www.youtube.com/watch?v=%s' % track['playlist_meta']['encrypted_id']
            for track in playlist['items']]


def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    return None


def clean(path):
    return path.replace('/', '-')


def normalise(time_string):
    start = datetime.strptime('00:00:00', '%H:%M:%S')
    if time_string.count(':') == 2:
        return (datetime.strptime(time_string.strip(), '%H:%M:%S') - start).total_seconds() * 1000
    else:
        return (datetime.strptime(time_string.strip(), '%M:%S') - start).total_seconds() * 1000


def print_info(s):
    print '[*] %s' % s


def main():
    for url in get_urls(args.input_url[0]):
        track = Track(url)
        track.download()


if __name__ == '__main__':
    parser = ArgumentParser(prog=__file__, description='yt audio dl')
    parser.add_argument('-i', '--input_url', type=str, nargs=1, help='playlist url')
    parser.add_argument('-o', '--output', nargs='?', type=str, help='output path')
    args = parser.parse_args()
    main()
