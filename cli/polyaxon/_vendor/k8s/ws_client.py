# Vendored from kubernetes==36.0.3 (kubernetes/stream/ws_client.py), Apache-2.0.
# Changes: kept WSClient, WSResponse, get_websocket_url, create_websocket and websocket_proxycare;
# kubernetes.client.rest import removed; no_proxy read with getattr, the Polyaxon SDK Configuration has none.

# Copyright 2018 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys

import certifi
import collections
import select
import socket
import ssl
import threading
import time
from urllib.parse import urlencode, urlparse, urlunparse
from io import StringIO, BytesIO
from websocket import WebSocket, ABNF, enableTrace, WebSocketConnectionClosedException
from base64 import urlsafe_b64decode

import yaml
from requests.utils import should_bypass_proxies

STDIN_CHANNEL = 0
STDOUT_CHANNEL = 1
STDERR_CHANNEL = 2
ERROR_CHANNEL = 3
RESIZE_CHANNEL = 4
CLOSE_CHANNEL = 255

V4_CHANNEL_PROTOCOL = "v4.channel.k8s.io"
V5_CHANNEL_PROTOCOL = "v5.channel.k8s.io"

class _IgnoredIO:
    def write(self, _x):
        pass

    def getvalue(self):
        raise TypeError("Tried to read_all() from a WSClient configured to not capture. Did you mean `capture_all=True`?")


class WSClient:
    def __init__(self, configuration, url, headers, capture_all, binary=False):
        """A websocket client with support for channels.

            Exec command uses different channels for different streams. for
        example, 0 is stdin, 1 is stdout and 2 is stderr. Some other API calls
        like port forwarding can forward different pods' streams to different
        channels.
        """
        self._connected = False
        self._channels = {}
        self._closed_channels = set()
        self.subprotocol = None
        self.binary = binary
        self.newline = '\n' if not self.binary else b'\n'
        if capture_all:
            self._all = StringIO() if not self.binary else BytesIO()
        else:
            self._all = _IgnoredIO()
        self.sock = create_websocket(configuration, url, headers)
        self.subprotocol = getattr(self.sock, 'subprotocol', None)
        if not self.subprotocol and self.sock:
            headers_dict = self.sock.getheaders()
            if headers_dict:
                for k, v in headers_dict.items():
                    if k.lower() == 'sec-websocket-protocol':
                        self.subprotocol = v
                        break
        self._connected = True
        self._returncode = None

    def peek_channel(self, channel, timeout=0):
        """Peek a channel and return part of the input,
        empty string otherwise."""
        if channel in self._closed_channels and channel not in self._channels:
            return b"" if self.binary else ""
        self.update(timeout=timeout)
        if channel in self._channels:
            return self._channels[channel]
        return b"" if self.binary else ""

    def read_channel(self, channel, timeout=0):
        """Read data from a channel."""
        if channel in self._closed_channels and channel not in self._channels:
            return b"" if self.binary else ""
        if channel not in self._channels:
            ret = self.peek_channel(channel, timeout)
        else:
            ret = self._channels[channel]
        if channel in self._channels:
            del self._channels[channel]
        return ret

    def readline_channel(self, channel, timeout=None):
        """Read a line from a channel."""
        if timeout is None:
            timeout = float("inf")
        start = time.time()
        while self.is_open() and time.time() - start < timeout:
            # Always try to drain the channel first
            if channel in self._channels:
                data = self._channels[channel]
                if self.newline in data:
                    index = data.find(self.newline)
                    ret = data[:index]
                    data = data[index+1:]
                    if data:
                        self._channels[channel] = data
                    else:
                        del self._channels[channel]
                    return ret

            if channel in self._closed_channels:
                if channel in self._channels:
                    ret = self._channels[channel]
                    del self._channels[channel]
                    return ret
                return b"" if self.binary else ""

            self.update(timeout=(timeout - time.time() + start))
        return b"" if self.binary else ""

    def write_channel(self, channel, data):
        """Write data to a channel."""
        # check if we're writing binary data or not
        binary = type(data) == bytes
        opcode = ABNF.OPCODE_BINARY if binary else ABNF.OPCODE_TEXT

        channel_prefix = chr(channel)
        if binary:
            channel_prefix = bytes(channel_prefix, "ascii")

        payload = channel_prefix + data
        self.sock.send(payload, opcode=opcode)

    def close_channel(self, channel):
        """Close a channel (v5 protocol only)."""
        if self.subprotocol != V5_CHANNEL_PROTOCOL:
            return
        data = bytes([CLOSE_CHANNEL, channel])
        self.sock.send(data, opcode=ABNF.OPCODE_BINARY)
        self._closed_channels.add(channel)

    def peek_stdout(self, timeout=0):
        """Same as peek_channel with channel=1."""
        return self.peek_channel(STDOUT_CHANNEL, timeout=timeout)

    def read_stdout(self, timeout=None):
        """Same as read_channel with channel=1."""
        return self.read_channel(STDOUT_CHANNEL, timeout=timeout)

    def readline_stdout(self, timeout=None):
        """Same as readline_channel with channel=1."""
        return self.readline_channel(STDOUT_CHANNEL, timeout=timeout)

    def peek_stderr(self, timeout=0):
        """Same as peek_channel with channel=2."""
        return self.peek_channel(STDERR_CHANNEL, timeout=timeout)

    def read_stderr(self, timeout=None):
        """Same as read_channel with channel=2."""
        return self.read_channel(STDERR_CHANNEL, timeout=timeout)

    def readline_stderr(self, timeout=None):
        """Same as readline_channel with channel=2."""
        return self.readline_channel(STDERR_CHANNEL, timeout=timeout)

    def read_all(self):
        """Return buffered data received on stdout and stderr channels.
        This is useful for non-interactive call where a set of command passed
        to the API call and their result is needed after the call is concluded.
        Should be called after run_forever() or update()

        TODO: Maybe we can process this and return a more meaningful map with
        channels mapped for each input.
        """
        out = self._all.getvalue()
        self._all = self._all.__class__()
        self._channels = {}
        return out

    def is_open(self):
        """True if the connection is still alive."""
        return self._connected

    def write_stdin(self, data):
        """The same as write_channel with channel=0."""
        self.write_channel(STDIN_CHANNEL, data)

    def update(self, timeout=0):
        """Update channel buffers with at most one complete frame of input."""
        if not self.is_open():
            return
        if not self.sock.connected:
            self._connected = False
            return

        # The options here are:
        # select.select() - this will work on most OS, however, it has a
        #                   limitation of only able to read fd numbers up to 1024.
        #                   i.e. does not scale well. This was the original
        #                   implementation.
        # select.poll()   - this will work on most unix based OS, but not as
        #                   efficient as epoll. Will work for fd numbers above 1024.
        # select.epoll()  - newest and most efficient way of polling.
        #                   However, only works on linux.
        if hasattr(select, "poll"):
            poll = select.poll()
            poll.register(self.sock.sock, select.POLLIN)
            if timeout is not None and timeout != float("inf"):
                timeout *= 1_000  # poll method uses milliseconds as the time unit
            else:
                timeout = None
            r = poll.poll(timeout)
            poll.unregister(self.sock.sock)
        else:
            if timeout == float("inf"):
                timeout = None
            r, _, _ = select.select(
                (self.sock.sock, ), (), (), timeout)

        if r:
            op_code, frame = self.sock.recv_data_frame(True)
            if op_code == ABNF.OPCODE_CLOSE:
                self._connected = False
                return
            elif op_code == ABNF.OPCODE_BINARY or op_code == ABNF.OPCODE_TEXT:
                data = frame.data
                if len(data) > 0:
                    # Parse channel from raw bytes to support v5 CLOSE signal AND avoid charset issues
                    channel = data[0]
                    # In Py3, iterating bytes gives int, but indexing bytes gives int.
                    # websocket-client frame.data might be bytes.

                    if channel == CLOSE_CHANNEL and self.subprotocol == V5_CHANNEL_PROTOCOL: # v5 CLOSE
                         if len(data) > 1:
                             # data[1] is already int in Py3 bytes
                             close_chan = data[1]
                             self._closed_channels.add(close_chan)
                         return

                    data = data[1:]
                    # Decode data if expected text
                    if not self.binary:
                        data = data.decode("utf-8", "replace")

                    if data:
                        if channel in [STDOUT_CHANNEL, STDERR_CHANNEL]:
                            # keeping all messages in the order they received
                            # for non-blocking call.
                            self._all.write(data)
                        if channel not in self._channels:
                            self._channels[channel] = data
                        else:
                            self._channels[channel] += data

    def run_forever(self, timeout=None):
        """Wait till connection is closed or timeout reached. Buffer any input
        received during this time."""
        if timeout:
            start = time.time()
            while self.is_open() and time.time() - start < timeout:
                self.update(timeout=(timeout - time.time() + start))
        else:
            while self.is_open():
                self.update(timeout=None)
    @property
    def returncode(self):
        """
        The return code, A None value indicates that the process hasn't
        terminated yet.
        """
        if self.is_open():
            return None
        else:
            if self._returncode is None:
                err = self.read_channel(ERROR_CHANNEL)
                err = yaml.safe_load(err)
                if err['status'] == "Success":
                    self._returncode = 0
                else:
                    self._returncode = int(err['details']['causes'][0]['message'])
            return self._returncode

    def close(self, **kwargs):
        """
        close websocket connection.
        """
        self._connected = False
        if self.sock:
            self.sock.close(**kwargs)


class WSResponse:

    def __init__(self, data, status):
        self.status = status
        self.data = data

    def getheader(self, name, default=None):
        """Returns a given response header."""
        return None


def get_websocket_url(url, query_params=None):
    parsed_url = urlparse(url)
    parts = list(parsed_url)
    if parsed_url.scheme == 'http':
        parts[0] = 'ws'
    elif parsed_url.scheme == 'https':
        parts[0] = 'wss'
    if query_params:
        query = []
        for key, value in query_params:
            if key == 'command' and isinstance(value, list):
                for command in value:
                    query.append((key, command))
            else:
                query.append((key, value))
        if query:
            parts[4] = urlencode(query)
    return urlunparse(parts)


def create_websocket(configuration, url, headers=None):
    enableTrace(False)

    # We just need to pass the Authorization, ignore all the other
    # http headers we get from the generated code
    header = []
    if headers and 'authorization' in headers:
            header.append("authorization: %s" % headers['authorization'])
    if headers and 'sec-websocket-protocol' in headers:
        header.append("sec-websocket-protocol: %s" %
                      headers['sec-websocket-protocol'])
    else:
        header.append("sec-websocket-protocol: %s,%s" % (V5_CHANNEL_PROTOCOL, V4_CHANNEL_PROTOCOL))

    if url.startswith('wss://') and configuration.verify_ssl:
        ssl_opts = {
            'cert_reqs': ssl.CERT_REQUIRED,
            'ca_certs': configuration.ssl_ca_cert or certifi.where(),
        }
        if configuration.assert_hostname is not None:
            ssl_opts['check_hostname'] = configuration.assert_hostname
    else:
        ssl_opts = {'cert_reqs': ssl.CERT_NONE}

    if configuration.cert_file:
        ssl_opts['certfile'] = configuration.cert_file
    if configuration.key_file:
        ssl_opts['keyfile'] = configuration.key_file
    if configuration.tls_server_name:
        ssl_opts['server_hostname'] = configuration.tls_server_name

    websocket = WebSocket(sslopt=ssl_opts, skip_utf8_validation=False)
    connect_opt = {
         'header': header
    }

    if configuration.proxy or configuration.proxy_headers:
        connect_opt = websocket_proxycare(connect_opt, configuration, url, headers)

    websocket.connect(url, **connect_opt)
    return websocket

def websocket_proxycare(connect_opt, configuration, url, headers):
    """ An internal function to be called in api-client when a websocket
        create is requested.
    """
    if getattr(configuration, "no_proxy", None):
        connect_opt.update({ 'http_no_proxy': configuration.no_proxy.split(',') })

    if configuration.proxy:
        proxy_url = urlparse(configuration.proxy)
        connect_opt.update({'http_proxy_host': proxy_url.hostname, 'http_proxy_port': proxy_url.port})
    if configuration.proxy_headers:
        for key,value in configuration.proxy_headers.items():
            if key == 'proxy-authorization' and value.startswith('Basic'):
                b64value = value.split()[1]
                auth = urlsafe_b64decode(b64value).decode().split(':')
                connect_opt.update({'http_proxy_auth': (auth[0], auth[1]) })
    return(connect_opt)
