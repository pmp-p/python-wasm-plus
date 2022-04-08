"""Event loop using a selector and related classes.

A selector is a "notify-when-ready" multiplexer.  For a subclass which
also includes support for signal handling, see the unix_events sub-module.
"""

__all__ = ['BaseSelectorEventLoop']
import sys
_emscripten = True # (sys.platform == "emscripten")



from . import base_events
from . import constants
from . import events
from . import futures
from . import transports
from . import sslproto
#from .coroutines import coroutine
from .log import logger




class _SelectorTransport(transports._FlowControlMixin,
                         transports.Transport):

    max_size = 256 * 1024  # Buffer size passed to recv().

    _buffer_factory = bytearray  # Constructs initial value for self._buffer.

    # Attribute used in the destructor: it must be set even if the constructor
    # is not called (see _SelectorSslTransport which may start by raising an
    # exception)
    _sock = None

    def __init__(self, loop, sock, protocol, extra=None, server=None):
        super().__init__(extra, loop)
        self._extra['socket'] = sock
        self._extra['sockname'] = sock.getsockname()
        if 'peername' not in self._extra:
            try:
                self._extra['peername'] = sock.getpeername()
            except socket.error:
                self._extra['peername'] = None
        self._sock = sock
        self._sock_fd = sock.fileno()
        self._protocol = protocol
        self._protocol_connected = True
        self._server = server
        self._buffer = self._buffer_factory()
        self._conn_lost = 0  # Set when call to connection_lost scheduled.
        self._closing = False  # Set when close() called.
        if self._server is not None:
            self._server._attach()
        loop._transports[self._sock_fd] = self

    def __repr__(self):
        info = [self.__class__.__name__]
        if self._sock is None:
            info.append('closed')
        elif self._closing:
            info.append('closing')
        info.append('fd=%s' % self._sock_fd)
        # test if the transport was closed
        if self._loop is not None and not self._loop.is_closed():
            polling = _test_selector_event(self._loop._selector,
                                           self._sock_fd, selectors.EVENT_READ)
            if polling:
                info.append('read=polling')
            else:
                info.append('read=idle')

            polling = _test_selector_event(self._loop._selector,
                                           self._sock_fd,
                                           selectors.EVENT_WRITE)
            if polling:
                state = 'polling'
            else:
                state = 'idle'

            bufsize = self.get_write_buffer_size()
            info.append('write=<%s, bufsize=%s>' % (state, bufsize))
        return '<%s>' % ' '.join(info)

    def abort(self):
        self._force_close(None)

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        return self._protocol

    def is_closing(self):
        return self._closing

    def close(self):
        if self._closing:
            return
        self._closing = True
        self._loop._remove_reader(self._sock_fd)
        if not self._buffer:
            self._conn_lost += 1
            self._loop._remove_writer(self._sock_fd)
            self._loop.call_soon(self._call_connection_lost, None)

    def __del__(self):
        if self._sock is not None:
            warnings.warn("unclosed transport %r" % self, ResourceWarning,
                          source=self)
            self._sock.close()

    def _fatal_error(self, exc, message='Fatal error on transport'):
        # Should be called from exception handler only.
        if isinstance(exc, base_events._FATAL_ERROR_IGNORE):
            if self._loop.get_debug():
                logger.debug("%r: %s", self, message, exc_info=True)
        else:
            self._loop.call_exception_handler({
                'message': message,
                'exception': exc,
                'transport': self,
                'protocol': self._protocol,
            })
        self._force_close(exc)

    def _force_close(self, exc):
        if self._conn_lost:
            return
        if self._buffer:
            self._buffer.clear()
            self._loop._remove_writer(self._sock_fd)
        if not self._closing:
            self._closing = True
            self._loop._remove_reader(self._sock_fd)
        self._conn_lost += 1
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            if self._protocol_connected:
                self._protocol.connection_lost(exc)
        finally:
            self._sock.close()
            self._sock = None
            self._protocol = None
            self._loop = None
            server = self._server
            if server is not None:
                server._detach()
                self._server = None

    def get_write_buffer_size(self):
        return len(self._buffer)


class _SelectorSocketTransport(_SelectorTransport):

    def __init__(self, loop, sock, protocol, waiter=None,
                 extra=None, server=None):
        super().__init__(loop, sock, protocol, extra, server)
        self._eof = False
        self._paused = False

        # Disable the Nagle algorithm -- small writes will be
        # sent without waiting for the TCP ACK.  This generally
        # decreases the latency (in some cases significantly.)
        _set_nodelay(self._sock)

        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._loop._add_reader,
                             self._sock_fd, self._read_ready)
        if waiter is not None:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, None)

    def pause_reading(self):
        if self._closing:
            raise RuntimeError('Cannot pause_reading() when closing')
        if self._paused:
            raise RuntimeError('Already paused')
        self._paused = True
        self._loop._remove_reader(self._sock_fd)
        if self._loop.get_debug():
            logger.debug("%r pauses reading", self)

    def resume_reading(self):
        if not self._paused:
            raise RuntimeError('Not paused')
        self._paused = False
        if self._closing:
            return
        self._loop._add_reader(self._sock_fd, self._read_ready)
        if self._loop.get_debug():
            logger.debug("%r resumes reading", self)

    def _read_ready(self):
        if self._conn_lost:
            return
        try:
            data = self._sock.recv(self.max_size)
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as exc:
            self._fatal_error(exc, 'Fatal read error on socket transport')
        else:
            if data:
                self._protocol.data_received(data)
            else:
                if self._loop.get_debug():
                    logger.debug("%r received EOF", self)
                keep_open = self._protocol.eof_received()
                if keep_open:
                    # We're keeping the connection open so the
                    # protocol can write more, but we still can't
                    # receive more, so remove the reader callback.
                    self._loop._remove_reader(self._sock_fd)
                else:
                    self.close()

    def write(self, data):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError('data argument must be a bytes-like object, '
                            'not %r' % type(data).__name__)
        if self._eof:
            raise RuntimeError('Cannot call write() after write_eof()')
        if not data:
            return

        if self._conn_lost:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        if not self._buffer:
            # Optimization: try to send now.
            try:
                n = self._sock.send(data)
            except (BlockingIOError, InterruptedError):
                pass
            except Exception as exc:
                self._fatal_error(exc, 'Fatal write error on socket transport')
                return
            else:
                data = data[n:]
                if not data:
                    return
            # Not all was written; register write handler.
            self._loop._add_writer(self._sock_fd, self._write_ready)

        # Add it to the buffer.
        self._buffer.extend(data)
        self._maybe_pause_protocol()

    def _write_ready(self):
        assert self._buffer, 'Data should not be empty'

        if self._conn_lost:
            return
        try:
            n = self._sock.send(self._buffer)
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as exc:
            self._loop._remove_writer(self._sock_fd)
            self._buffer.clear()
            self._fatal_error(exc, 'Fatal write error on socket transport')
        else:
            if n:
                del self._buffer[:n]
            self._maybe_resume_protocol()  # May append to buffer.
            if not self._buffer:
                self._loop._remove_writer(self._sock_fd)
                if self._closing:
                    self._call_connection_lost(None)
                elif self._eof:
                    self._sock.shutdown(socket.SHUT_WR)

    def write_eof(self):
        if self._eof:
            return
        self._eof = True
        if not self._buffer:
            self._sock.shutdown(socket.SHUT_WR)

    def can_write_eof(self):
        return True


class _SelectorDatagramTransport(_SelectorTransport):

    _buffer_factory = collections.deque

    def __init__(self, loop, sock, protocol, address=None,
                 waiter=None, extra=None):
        super().__init__(loop, sock, protocol, extra)
        self._address = address
        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._loop._add_reader,
                             self._sock_fd, self._read_ready)
        if waiter is not None:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, None)

    def get_write_buffer_size(self):
        return sum(len(data) for data, _ in self._buffer)

    def _read_ready(self):
        if self._conn_lost:
            return
        try:
            data, addr = self._sock.recvfrom(self.max_size)
        except (BlockingIOError, InterruptedError):
            pass
        except OSError as exc:
            self._protocol.error_received(exc)
        except Exception as exc:
            self._fatal_error(exc, 'Fatal read error on datagram transport')
        else:
            self._protocol.datagram_received(data, addr)

    def sendto(self, data, addr=None):
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError('data argument must be a bytes-like object, '
                            'not %r' % type(data).__name__)
        if not data:
            return

        if self._address and addr not in (None, self._address):
            raise ValueError('Invalid address: must be None or %s' %
                             (self._address,))

        if self._conn_lost and self._address:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('socket.send() raised exception.')
            self._conn_lost += 1
            return

        if not self._buffer:
            # Attempt to send it right away first.
            try:
                if self._address:
                    self._sock.send(data)
                else:
                    self._sock.sendto(data, addr)
                return
            except (BlockingIOError, InterruptedError):
                self._loop._add_writer(self._sock_fd, self._sendto_ready)
            except OSError as exc:
                self._protocol.error_received(exc)
                return
            except Exception as exc:
                self._fatal_error(exc,
                                  'Fatal write error on datagram transport')
                return

        # Ensure that what we buffer is immutable.
        self._buffer.append((bytes(data), addr))
        self._maybe_pause_protocol()

    def _sendto_ready(self):
        while self._buffer:
            data, addr = self._buffer.popleft()
            try:
                if self._address:
                    self._sock.send(data)
                else:
                    self._sock.sendto(data, addr)
            except (BlockingIOError, InterruptedError):
                self._buffer.appendleft((data, addr))  # Try again later.
                break
            except OSError as exc:
                self._protocol.error_received(exc)
                return
            except Exception as exc:
                self._fatal_error(exc,
                                  'Fatal write error on datagram transport')
                return

        self._maybe_resume_protocol()  # May append to buffer.
        if not self._buffer:
            self._loop._remove_writer(self._sock_fd)
            if self._closing:
                self._call_connection_lost(None)
