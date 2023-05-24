import os
import socket
import sys
import logging
from functools import partial
from typing import List, Dict, BinaryIO, Optional, Tuple

logger = logging.getLogger(__name__)

eprint = partial(print, file=sys.stderr)


def print():
    raise NotImplementedError("Use eprint() instead of print(), since stdout is used for BoldUI protocol")


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.DEBUG,
    )
    logging.addLevelName(5, "TRACE")


def _trace(msg, *args, **kwargs):
    logger.log(5, msg, *args, **kwargs)


def _parse_relative_path(path: str) -> (List[str], Dict[str, str]):
    import urllib.parse

    before_query, _, query = path.partition("?")
    query_dict = urllib.parse.parse_qs(query, keep_blank_values=True, strict_parsing=True) if query else {}
    query_dict = {k: v[0] for k, v in query_dict.items()}  # Ignore multiple values

    return before_query.lstrip("/").split("/"), query_dict


class _FullWriter:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def write(self, data: bytes):
        while data:
            wrote = self.stream.write(data)
            if wrote == 0:
                raise RuntimeError("Failed to write to stream")
            data = data[wrote:]
        self.stream.flush()


class _FullReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream

    def read(self, size: int) -> bytes:
        data = self.read_or_none(size)
        if data is None:
            raise RuntimeError("Failed to read from stream")
        return data

    def read_or_none(self, size: int) -> Optional[bytes]:
        data = b""
        while len(data) < size:
            chunk = self.stream.read(size - len(data))
            if not chunk:
                return None
            data += chunk
        return data


class _FullAuxWriter:
    def __init__(self, stream: socket.socket):
        self.stream = stream

    def write(self, data: bytes, fds: List[int] = ()):
        while data:
            wrote = socket.send_fds(self.stream, [data], fds)
            fds = ()
            if wrote == 0:
                raise RuntimeError("Failed to write to stream")
            data = data[wrote:]


class _FullAuxReader:
    def __init__(self, stream: socket.socket):
        self.stream = stream

    def read_fds(self, size: int) -> (bytes, List[int]):
        res = self.read_or_none(size)
        if res is None:
            raise RuntimeError("Failed to read from stream")
        return res

    def read_fds_or_none(self, size: int) -> Optional[Tuple[bytes, List[int]]]:
        data = b""
        fds = []
        while len(data) < size:
            logger.info("Reading %d bytes", min(1024 * 1024, size - len(data)))
            chunk, fds_chunk, _flags, _addr = socket.recv_fds(self.stream, min(1024 * 1024, size - len(data)), 64)
            logger.info("Got chunk %s, fds %s", repr(chunk), repr(fds_chunk))
            fds += fds_chunk
            if not chunk:
                for fd in fds:
                    os.close(fd)
                return None
            data += chunk
        return data, fds

    def read(self, size: int) -> bytes:
        res = self.read_or_none(size)
        if res is None:
            raise RuntimeError("Failed to read from stream")
        return res

    def read_or_none(self, size: int) -> Optional[bytes]:
        res = self.read_fds_or_none(size)
        if res is None:
            return None
        data, fds = res

        if fds:
            for fd in fds:
                os.close(fd)
            raise RuntimeError("Unexpected fds")
        return data
