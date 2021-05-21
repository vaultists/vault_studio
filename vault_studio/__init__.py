import argparse
import json
import urllib.request
import urllib.parse


class M3UCreator(object):
    extension = "m3u"

    def __init__(self, uri, outuri="{path}.{extension}"):
        self._parsed_uri=urllib.parse.urlparse(uri)
        if not outuri:
            self._outuri=outuri.format(path=self._parsed_uri.path, extension=self.extension)

    def __call__(self):

        stream = urllib.request.urlopen(self._parsed_uri.geturl())
        with stream:
            for line in json.load(stream):
                print(line['url'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', type=str)
    args = parser.parse_args()
    json_file: str = args.json_file
    M3UCreator(json_file)()
