from __future__ import annotations

import abc
import argparse
import json
import typing
import urllib.request
import urllib.parse
import urllib.response
from abc import abstractmethod
from io import TextIOBase

from urllib.parse import ParseResult


class IOHandler(object):
    class URLHandler(object):
        class FileHandler(object):
            @staticmethod
            def out(uri: ParseResult) -> typing.Any:
                return open("/{}".format(uri.path), 'w+')

            @staticmethod
            def input(uri: ParseResult) -> typing.Any:
                return open("/{}".format(uri.path), 'r')

        class FallbackHandler(object):
            @staticmethod
            def out(uri: ParseResult) -> typing.Any:
                return urllib.request.urlopen(uri.geturl())

            input = out

        handlers = {'file': FileHandler}

        @staticmethod
        def ostream(uri: ParseResult) -> TextIOBase:
            return IOHandler.URLHandler.handlers.get(uri.scheme, IOHandler.URLHandler.FallbackHandler).out(uri)

        @staticmethod
        def istream(uri: ParseResult) -> TextIOBase:
            return IOHandler.URLHandler.handlers.get(uri.scheme, IOHandler.URLHandler.FallbackHandler).input(uri)

    def __init__(self, uri: str, extension: str):
        parsed_uri: ParseResult = urllib.parse.urlparse(uri)
        self.istream: typing.Optional[TextIOBase] = None
        self.ostream: typing.Optional[TextIOBase] = None
        self._iurl = parsed_uri
        self._ourl: ParseResult = self.get_out_url(parsed_uri, extension)

    def get_out_url(self, parsed_uri: ParseResult, extension: str) -> ParseResult:
        return parsed_uri._replace(path="{}.{}".format(parsed_uri.path, extension))

    def __enter__(self) -> IOHandler:
        self.istream = urllib.request.urlopen(self._iurl.geturl())
        self.ostream = IOHandler.URLHandler.ostream(self._ourl)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.istream.close()
        self.ostream.close()


IOHandlerType = typing.TypeVar('IOHandlerType', bound=IOHandler)


class VaultEntry(typing.NamedTuple):
    description: str
    url: str


class PlaylistCreator(typing.Generic[IOHandlerType]):
    _io_handler: typing.Type[IOHandler]
    extension: str

    @classmethod
    def build(cls, io_handler: typing.Type[IOHandlerType] = IOHandler) -> PlaylistCreator[IOHandlerType]:
        result = cls()
        result._io_handler = io_handler
        return result

    def write(self: PlaylistCreator, uri: str):
        with self._io_handler(uri, self.extension) as handler:
            vault_entries = (VaultEntry(**x) for x in json.load(handler.istream))
            handler.ostream.write(self.convert(vault_entries))

    @abstractmethod
    def convert(self, vault_entries: typing.Iterable[VaultEntry]) -> str:
        pass


class M3UCreator(PlaylistCreator):
    extension = "m3u"

    def convert(self, vault_entries: typing.Iterable[VaultEntry]) -> str:
        return "\n".join(x.url for x in vault_entries)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('json_file', type=str)
    args = parser.parse_args()
    json_file: str = args.json_file
    creator = M3UCreator.build(IOHandler)
    creator.write(json_file)