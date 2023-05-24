import fcntl
import logging
import socket
import struct
import time
from typing import Any
from boldui.utils import setup_logging, _FullAuxWriter, _FullAuxReader, eprint, _trace, _parse_relative_path
from boldui_protocol import *

logger = logging.getLogger(__name__)


class BoldUIExternalApp:
    SHARED_FD = 3

    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM, 0, BoldUIExternalApp.SHARED_FD)
        self.out = _FullAuxWriter(self.sock)
        self.inp = _FullAuxReader(self.sock)

    @staticmethod
    def setup_logging():
        setup_logging()

    def main_loop(self):
        if fcntl.fcntl(BoldUIExternalApp.SHARED_FD, fcntl.F_GETFD) == -1:
            eprint("This app must be run by a boldui renderer")
            exit(1)

        # Get hello
        logger.debug("reading hello")
        magic = self.inp.read(len(R2EA_MAGIC))
        assert magic == R2EA_MAGIC, "Missing magic"
        # noinspection PyTypeChecker
        hello = R2EAHello.bincode_deserialize_stream(self.inp)
        assert LATEST_EA_MAJOR_VER <= hello.max_protocol_major_version and (
            LATEST_EA_MAJOR_VER > hello.min_protocol_major_version
            or (
                LATEST_EA_MAJOR_VER == hello.min_protocol_major_version
                and LATEST_EA_MINOR_VER >= hello.min_protocol_minor_version
            )
        ), "Incompatible version"
        assert hello.extra_len == 0, "This protocol version specifies no extra data"

        # Reply with EA2RHelloResponse
        logger.debug("sending hello response")
        self.out.write(EA2R_MAGIC)
        self.out.write(
            EA2RHelloResponse(
                protocol_major_version=st.uint16(LATEST_EA_MAJOR_VER),
                protocol_minor_version=st.uint16(LATEST_EA_MINOR_VER),
                extra_len=st.uint32(0),
                error=None,
            ).bincode_serialize()
        )
        logger.debug("connected!")

        # Run app
        while True:
            msg_len_and_req_id = self.inp.read_or_none(8)
            if msg_len_and_req_id is None:
                logger.debug("connection closed, bye!")
                return
            msg_len, req_id = struct.unpack("<II", msg_len_and_req_id)
            logger.debug(f"reading message of size {msg_len}, req_id={req_id}")

            msg: Any = R2EAMessage.bincode_deserialize(self.inp.read(msg_len))
            logger.debug(f"R2EA: {msg}")

            if type(msg) == R2EAMessage__Update:
                msg: R2EAUpdate = msg.value
                logger.info(f"update: {msg}")
            elif type(msg) == R2EAMessage__Open:
                msg: R2EAOpen = msg.value
                path, params = _parse_relative_path(msg.path)

                logger.info(f"open: {path} ({params})")
                fd, metadata = self.create_texture()
                eprint("Sending FD", fd)
                self.send_message(req_id, EA2RMessage__CreatedExternalWidget(metadata), fds=(fd,))
                while True:
                    # FIXME
                    self.renderer.render()
                    time.sleep(0.005)

                # session_id = params.get("session", str(uuid.uuid4()))
                # scene_id = self._scene_id_counter
                # self._scene_id_counter += 1
                #
                # self._open_window(
                #     scene_id=scene_id,
                #     session_id=session_id,
                #     path=path,
                #     query_params=params,
                # )
            elif type(msg) == R2EAMessage__Error:
                msg: Error = msg.value
                logger.error(f"Renderer error: {msg.code}: {msg.text}")
            else:
                raise RuntimeError(f"Unknown message type: {type(msg)}")

    def create_texture(self) -> (int, bytes):
        raise NotImplementedError()

    def send_message(self, req_id: int, msg: EA2RMessage, fds=()):
        encoded_msg = msg.bincode_serialize()
        self.out.write(struct.pack("<II", len(encoded_msg), req_id), fds=fds)
        self.out.write(encoded_msg)
