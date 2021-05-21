from __future__ import annotations
import argparse
import json
import typing
import urllib.request
import urllib.parse
import urllib.response

from urllib.parse import ParseResult


class IOHandler(object):
    def __init__(self, uri: str, extension: str):
        parsed_uri: ParseResult = urllib.parse.urlparse(uri)
        self._iurl = parsed_uri
        self._ourl: ParseResult = self.get_out_url(parsed_uri, extension)

    def get_out_url(self, parsed_uri: ParseResult, extension: str) -> ParseResult:
        return parsed_uri._replace(path="{}.{}".format(parsed_uri.path, extension))

    def __enter__(self) -> IOHandler:
        self.istream = urllib.request.urlopen(self._iurl.geturl())

        def file_handler(uri: ParseResult) -> typing.Any:
            return open("/{}".format(uri.path), 'w+')

        def fallback_handler(uri: ParseResult) -> typing.Any:
            return urllib.request.urlopen(uri.geturl())
        handlers = {'file': file_handler}
        handler = handlers.get(self._ourl.scheme, fallback_handler)
        self.ostream = handler(self._ourl)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.istream.close()
        self.ostream.close()


IOHandlerType = typing.TypeVar('IOHandlerType', bound=IOHandler)


class M3UCreator(object):
    _io_handler: typing.Type[IOHandler]
    extension = "m3u"

    def __new__(cls: M3UCreator, uri: str):
        with cls._io_handler(uri, cls.extension) as handler:
            for line in json.load(handler.istream):
                handler.ostream.write(line['url'])

    @classmethod
    def __class_getitem__(cls, io_handler: typing.Type[IOHandler]) -> typing.Type[M3UCreator]:
        class Result(M3UCreator):
            _io_handler = io_handler
            extension = M3UCreator.extension
        return Result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', type=str)
    args = parser.parse_args()
    json_file: str = args.json_file
    M3UCreator[IOHandler](json_file)