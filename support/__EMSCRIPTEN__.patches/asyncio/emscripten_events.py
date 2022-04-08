"""Selector event loop for Em with signal handling."""
import sys
_emscripten = True #(sys.platform=='emscripten')

print(__file__, "5:loading emscripten event loop")

import errno
import os
import selectors
import signal
import socket
import stat

class subprocess:
    PIPE=-1
    STDOUT=-2

import sys
import threading
import warnings


from . import base_events
from . import base_subprocess
from . import constants
from . import events
from . import futures
from . import transports
from .log import logger




#=========================================================================
import types
import inspect

# A marker for iscoroutinefunction.
_is_coroutine = object()

_DEBUG=False

def coroutine(func):
    """Decorator to mark coroutines.

    If the coroutine is not yielded from before it is destroyed,
    an error message is logged.
    """

    global _DEBUG

    if inspect.iscoroutinefunction(func):
        # In Python 3.5 that's all we need to do for coroutines
        # defined with "async def".
        # Wrapping in CoroWrapper will happen via
        # 'sys.set_coroutine_wrapper' function.
        return func

    if inspect.isgeneratorfunction(func):
        coro = func
    else:
        @functools.wraps(func)
        def coro(*args, **kw):
            res = func(*args, **kw)
            if (base_futures.isfuture(res) or inspect.isgenerator(res) or
                isinstance(res, CoroWrapper)):
                res = yield from res
            else:
                # If 'func' returns an Awaitable (new in 3.5) we
                # want to run it.
                try:
                    await_meth = res.__await__
                except AttributeError:
                    pass
                else:
                    if isinstance(res, Awaitable):
                        res = yield from await_meth()
            return res

    if not _DEBUG:
        wrapper = types.coroutine(coro)
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwds):
            w = CoroWrapper(coro(*args, **kwds), func=func)
            if w._source_traceback:
                del w._source_traceback[-1]
            # Python < 3.5 does not implement __qualname__
            # on generator objects, so we set it manually.
            # We use getattr as some callables (such as
            # functools.partial may lack __qualname__).
            w.__name__ = getattr(func, '__name__', None)
            w.__qualname__ = getattr(func, '__qualname__', None)
            return w

    wrapper._is_coroutine = _is_coroutine  # For iscoroutinefunction().
    return wrapper

#======================================================================

import collections
import errno
import functools
import selectors
#import socket
import warnings
import weakref
try:
    import ssl
except ImportError:  # pragma: no cover
    ssl = None




__all__ = ('SelectorEventLoop',
           'AbstractChildWatcher', 'SafeChildWatcher',
           'FastChildWatcher', 'DefaultEventLoopPolicy',
           )


def _sighandler_noop(signum, frame):
    """Dummy signal handler."""
    pass


def _test_selector_event(selector, fd, event):
    # Test if the selector is monitoring 'event' events
    # for the file descriptor 'fd'.
    try:
        key = selector.get_key(fd)
    except KeyError:
        return False
    else:
        return bool(key.events & event)

if not _emscripten and hasattr(socket, 'TCP_NODELAY'):
    def _set_nodelay(sock):
        if (sock.family in {socket.AF_INET, socket.AF_INET6} and
                sock.type == socket.SOCK_STREAM and
                sock.proto == socket.IPPROTO_TCP):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
else:
    def _set_nodelay(sock):
        pass





class EmPipe:

    def _close_self_pipe(self):
        pdb("_close_self_pipe(self)")
        return

        self._remove_reader(self._ssock.fileno())
        self._ssock.close()
        self._ssock = None
        self._csock.close()
        self._csock = None
        self._internal_fds -= 1

    def _make_self_pipe(self):
        self._sq = self._cq = []
        self._add_reader( self._internal_fds , self._read_from_self)
        self._internal_fds += 1
        return

        self._ssock, self._csock = socket.socketpair()
        self._ssock.setblocking(False)
        self._csock.setblocking(False)
        self._internal_fds += 1
        self._add_reader(self._ssock.fileno(), self._read_from_self)

    def _read_from_self(self):
        #pdb("_read_from_self(self)")
        if len(self._cq):
            return self._cq.pop(0)
            self._process_self_data(data)
        return


    def _write_to_self(self):
        # This may be called from a different thread, possibly after
        # _close_self_pipe() has been called or even while it is
        # running.  Guard for self._csock being None or closed.  When
        # a socket is closed, send() raises OSError (with errno set to
        # EBADF, but let's not rely on the exact error code).
        self._sq.append('\0')

        return
        csock = self._csock
        if csock is not None:
            try:
                csock.send(b'\0')
            except OSError:
                if self._debug:
                    logger.debug("Fail to write a null byte into the "
                                 "self-pipe socket",
                                 exc_info=True)

class BaseSelectorEventLoop(base_events.BaseEventLoop, EmPipe):
    """Selector event loop.

    See events.EventLoop for API specification.
    """

    def __init__(self, selector=None):
        super().__init__()
        if selector is None:
            if _emscripten:
                selector = selectors.SelectSelector()
            else:
                selector = selectors.DefaultSelector()

        self._selector = selector
        self._make_self_pipe()
        self._transports = weakref.WeakValueDictionary()

    def _make_socket_transport(self, sock, protocol, waiter=None, *,
                               extra=None, server=None):
        return _SelectorSocketTransport(self, sock, protocol, waiter,
                                        extra, server)

    def _make_ssl_transport(self, rawsock, protocol, sslcontext, waiter=None,
                            *, server_side=False, server_hostname=None,
                            extra=None, server=None):
        ssl_protocol = sslproto.SSLProtocol(self, protocol, sslcontext, waiter,
                                            server_side, server_hostname)
        _SelectorSocketTransport(self, rawsock, ssl_protocol,
                                 extra=extra, server=server)
        return ssl_protocol._app_transport

    def _make_datagram_transport(self, sock, protocol,
                                 address=None, waiter=None, extra=None):
        return _SelectorDatagramTransport(self, sock, protocol,
                                          address, waiter, extra)

    def close(self):
        if self.is_running():
            raise RuntimeError("Cannot close a running event loop")
        if self.is_closed():
            return
        if not _emscripten:
            self._close_self_pipe()
        super().close()
        if self._selector is not None:
            self._selector.close()
            self._selector = None


    def _process_self_data(self, data):
        pass



    def _start_serving(self, protocol_factory, sock,
                       sslcontext=None, server=None, backlog=100):
        self._add_reader(sock.fileno(), self._accept_connection,
                         protocol_factory, sock, sslcontext, server, backlog)

    def _accept_connection(self, protocol_factory, sock,
                           sslcontext=None, server=None, backlog=100):
        # This method is only called once for each event loop tick where the
        # listening socket has triggered an EVENT_READ. There may be multiple
        # connections waiting for an .accept() so it is called in a loop.
        # See https://bugs.python.org/issue27906 for more details.
        for _ in range(backlog):
            try:
                conn, addr = sock.accept()
                if self._debug:
                    logger.debug("%r got a new connection from %r: %r",
                                 server, addr, conn)
                conn.setblocking(False)
            except (BlockingIOError, InterruptedError, ConnectionAbortedError):
                # Early exit because the socket accept buffer is empty.
                return None
            except OSError as exc:
                # There's nowhere to send the error, so just log it.
                if exc.errno in (errno.EMFILE, errno.ENFILE,
                                 errno.ENOBUFS, errno.ENOMEM):
                    # Some platforms (e.g. Linux keep reporting the FD as
                    # ready, so we remove the read handler temporarily.
                    # We'll try again in a while.
                    self.call_exception_handler({
                        'message': 'socket.accept() out of system resource',
                        'exception': exc,
                        'socket': sock,
                    })
                    self._remove_reader(sock.fileno())
                    self.call_later(constants.ACCEPT_RETRY_DELAY,
                                    self._start_serving,
                                    protocol_factory, sock, sslcontext, server,
                                    backlog)
                else:
                    raise  # The event loop will catch, log and ignore it.
            else:
                extra = {'peername': addr}
                accept = self._accept_connection2(protocol_factory, conn, extra,
                                                  sslcontext, server)
                self.create_task(accept)

    @coroutine
    def _accept_connection2(self, protocol_factory, conn, extra,
                            sslcontext=None, server=None):
        protocol = None
        transport = None
        try:
            protocol = protocol_factory()
            waiter = self.create_future()
            if sslcontext:
                transport = self._make_ssl_transport(
                    conn, protocol, sslcontext, waiter=waiter,
                    server_side=True, extra=extra, server=server)
            else:
                transport = self._make_socket_transport(
                    conn, protocol, waiter=waiter, extra=extra,
                    server=server)

            try:
                yield from waiter
            except:
                transport.close()
                raise

            # It's now up to the protocol to handle the connection.
        except Exception as exc:
            if self._debug:
                context = {
                    'message': ('Error on transport creation '
                                'for incoming connection'),
                    'exception': exc,
                }
                if protocol is not None:
                    context['protocol'] = protocol
                if transport is not None:
                    context['transport'] = transport
                self.call_exception_handler(context)

    def _ensure_fd_no_transport(self, fd):
        fileno = fd
        if not isinstance(fileno, int):
            try:
                fileno = int(fileno.fileno())
            except (AttributeError, TypeError, ValueError):
                # This code matches selectors._fileobj_to_fd function.
                raise ValueError("Invalid file object: "
                                 "{!r}".format(fd)) from None
        try:
            transport = self._transports[fileno]
        except KeyError:
            pass
        else:
            if not transport.is_closing():
                raise RuntimeError(
                    'File descriptor {!r} is used by transport {!r}'.format(
                        fd, transport))

    def _add_reader(self, fd, callback, *args):
        self._check_closed()
        handle = events.Handle(callback, args, self)
        try:
            key = self._selector.get_key(fd)
        except KeyError:
            self._selector.register(fd, selectors.EVENT_READ,
                                    (handle, None))
        else:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_READ,
                                  (handle, writer))
            if reader is not None:
                reader.cancel()

    def _remove_reader(self, fd):
        if self.is_closed():
            return False
        try:
            key = self._selector.get_key(fd)
        except KeyError:
            return False
        else:
            mask, (reader, writer) = key.events, key.data
            mask &= ~selectors.EVENT_READ
            if not mask:
                self._selector.unregister(fd)
            else:
                self._selector.modify(fd, mask, (None, writer))

            if reader is not None:
                reader.cancel()
                return True
            else:
                return False

    def _add_writer(self, fd, callback, *args):
        self._check_closed()
        handle = events.Handle(callback, args, self)
        try:
            key = self._selector.get_key(fd)
        except KeyError:
            self._selector.register(fd, selectors.EVENT_WRITE,
                                    (None, handle))
        else:
            mask, (reader, writer) = key.events, key.data
            self._selector.modify(fd, mask | selectors.EVENT_WRITE,
                                  (reader, handle))
            if writer is not None:
                writer.cancel()

    def _remove_writer(self, fd):
        """Remove a writer callback."""
        if self.is_closed():
            return False
        try:
            key = self._selector.get_key(fd)
        except KeyError:
            return False
        else:
            mask, (reader, writer) = key.events, key.data
            # Remove both writer and connector.
            mask &= ~selectors.EVENT_WRITE
            if not mask:
                self._selector.unregister(fd)
            else:
                self._selector.modify(fd, mask, (reader, None))

            if writer is not None:
                writer.cancel()
                return True
            else:
                return False

    def add_reader(self, fd, callback, *args):
        """Add a reader callback."""
        self._ensure_fd_no_transport(fd)
        return self._add_reader(fd, callback, *args)

    def remove_reader(self, fd):
        """Remove a reader callback."""
        self._ensure_fd_no_transport(fd)
        return self._remove_reader(fd)

    def add_writer(self, fd, callback, *args):
        """Add a writer callback.."""
        self._ensure_fd_no_transport(fd)
        return self._add_writer(fd, callback, *args)

    def remove_writer(self, fd):
        """Remove a writer callback."""
        self._ensure_fd_no_transport(fd)
        return self._remove_writer(fd)

    def sock_recv(self, sock, n):
        """Receive data from the socket.

        The return value is a bytes object representing the data received.
        The maximum amount of data to be received at once is specified by
        nbytes.

        This method is a coroutine.
        """
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        fut = self.create_future()
        self._sock_recv(fut, None, sock, n)
        return fut

    def _sock_recv(self, fut, registered_fd, sock, n):
        # _sock_recv() can add itself as an I/O callback if the operation can't
        # be done immediately. Don't use it directly, call sock_recv().
        if registered_fd is not None:
            # Remove the callback early.  It should be rare that the
            # selector says the fd is ready but the call still returns
            # EAGAIN, and I am willing to take a hit in that case in
            # order to simplify the common case.
            self.remove_reader(registered_fd)
        if fut.cancelled():
            return
        try:
            data = sock.recv(n)
        except (BlockingIOError, InterruptedError):
            fd = sock.fileno()
            self.add_reader(fd, self._sock_recv, fut, fd, sock, n)
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result(data)

    def sock_recv_into(self, sock, buf):
        """Receive data from the socket.

        The received data is written into *buf* (a writable buffer).
        The return value is the number of bytes written.

        This method is a coroutine.
        """
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        fut = self.create_future()
        self._sock_recv_into(fut, None, sock, buf)
        return fut

    def _sock_recv_into(self, fut, registered_fd, sock, buf):
        # _sock_recv_into() can add itself as an I/O callback if the operation
        # can't be done immediately. Don't use it directly, call sock_recv_into().
        if registered_fd is not None:
            # Remove the callback early.  It should be rare that the
            # selector says the fd is ready but the call still returns
            # EAGAIN, and I am willing to take a hit in that case in
            # order to simplify the common case.
            self.remove_reader(registered_fd)
        if fut.cancelled():
            return
        try:
            nbytes = sock.recv_into(buf)
        except (BlockingIOError, InterruptedError):
            fd = sock.fileno()
            self.add_reader(fd, self._sock_recv_into, fut, fd, sock, buf)
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result(nbytes)

    def sock_sendall(self, sock, data):
        """Send data to the socket.

        The socket must be connected to a remote socket. This method continues
        to send data from data until either all data has been sent or an
        error occurs. None is returned on success. On error, an exception is
        raised, and there is no way to determine how much data, if any, was
        successfully processed by the receiving end of the connection.

        This method is a coroutine.
        """
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        fut = self.create_future()
        if data:
            self._sock_sendall(fut, None, sock, data)
        else:
            fut.set_result(None)
        return fut

    def _sock_sendall(self, fut, registered_fd, sock, data):
        if registered_fd is not None:
            self.remove_writer(registered_fd)
        if fut.cancelled():
            return

        try:
            n = sock.send(data)
        except (BlockingIOError, InterruptedError):
            n = 0
        except Exception as exc:
            fut.set_exception(exc)
            return

        if n == len(data):
            fut.set_result(None)
        else:
            if n:
                data = data[n:]
            fd = sock.fileno()
            self.add_writer(fd, self._sock_sendall, fut, fd, sock, data)

    @coroutine
    def sock_connect(self, sock, address):
        """Connect to a remote socket at address.

        This method is a coroutine.
        """
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")

        if not hasattr(socket, 'AF_UNIX') or sock.family != socket.AF_UNIX:
            resolved = base_events._ensure_resolved(
                address, family=sock.family, proto=sock.proto, loop=self)
            if not resolved.done():
                yield from resolved
            _, _, _, _, address = resolved.result()[0]

        fut = self.create_future()
        self._sock_connect(fut, sock, address)
        return (yield from fut)

    def _sock_connect(self, fut, sock, address):
        fd = sock.fileno()
        try:
            sock.connect(address)
        except (BlockingIOError, InterruptedError):
            # Issue #23618: When the C function connect() fails with EINTR, the
            # connection runs in background. We have to wait until the socket
            # becomes writable to be notified when the connection succeed or
            # fails.
            fut.add_done_callback(
                functools.partial(self._sock_connect_done, fd))
            self.add_writer(fd, self._sock_connect_cb, fut, sock, address)
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result(None)

    def _sock_connect_done(self, fd, fut):
        self.remove_writer(fd)

    def _sock_connect_cb(self, fut, sock, address):
        if fut.cancelled():
            return

        try:
            err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0:
                # Jump to any except clause below.
                raise OSError(err, 'Connect call failed %s' % (address,))
        except (BlockingIOError, InterruptedError):
            # socket is still registered, the callback will be retried later
            pass
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result(None)

    def sock_accept(self, sock):
        """Accept a connection.

        The socket must be bound to an address and listening for connections.
        The return value is a pair (conn, address) where conn is a new socket
        object usable to send and receive data on the connection, and address
        is the address bound to the socket on the other end of the connection.

        This method is a coroutine.
        """
        if self._debug and sock.gettimeout() != 0:
            raise ValueError("the socket must be non-blocking")
        fut = self.create_future()
        self._sock_accept(fut, False, sock)
        return fut

    def _sock_accept(self, fut, registered, sock):
        fd = sock.fileno()
        if registered:
            self.remove_reader(fd)
        if fut.cancelled():
            return
        try:
            conn, address = sock.accept()
            conn.setblocking(False)
        except (BlockingIOError, InterruptedError):
            self.add_reader(fd, self._sock_accept, fut, True, sock)
        except Exception as exc:
            fut.set_exception(exc)
        else:
            fut.set_result((conn, address))

    def _process_events(self, event_list):
        for key, mask in event_list:
            fileobj, (reader, writer) = key.fileobj, key.data
            if mask & selectors.EVENT_READ and reader is not None:
                if reader._cancelled:
                    self._remove_reader(fileobj)
                else:
                    self._add_callback(reader)
            if mask & selectors.EVENT_WRITE and writer is not None:
                if writer._cancelled:
                    self._remove_writer(fileobj)
                else:
                    self._add_callback(writer)

    def _stop_serving(self, sock):
        self._remove_reader(sock.fileno())
        sock.close()


























#=========================================================================

class SelectorEventLoop(BaseSelectorEventLoop):
    """Em event loop.

    Adds signal handling and Em Domain Socket support to SelectorEventLoop.
    """

    def __init__(self, selector=None):
        super().__init__(selector)
        self._signal_handlers = {}

    def close(self):
        super().close()
        for sig in list(self._signal_handlers):
            self.remove_signal_handler(sig)

    def _process_self_data(self, data):
        for signum in data:
            if not signum:
                # ignore null bytes written by _write_to_self()
                continue
            self._handle_signal(signum)

    def add_signal_handler(self, sig, callback, *args):
        """Add a handler for a signal.

        Raise ValueError if the signal number is invalid or uncatchable.
        Raise RuntimeError if there is a problem setting up the handler.
        """
        if (coroutines.iscoroutine(callback)
                or coroutines.iscoroutinefunction(callback)):
            raise TypeError("coroutines cannot be used "
                            "with add_signal_handler()")
        self._check_signal(sig)
        self._check_closed()
        pdb("signal.set_wakeup_fd(self._csock.fileno()) stub")
        try:
            # set_wakeup_fd() raises ValueError if this is not the
            # main thread.  By calling it early we ensure that an
            # event loop running in another thread cannot add a signal
            # handler.
            if _emscripten:
                self._cq.append('')
            else:
                signal.set_wakeup_fd(self._csock.fileno())
        except (ValueError, OSError) as exc:
            raise RuntimeError(str(exc))

        handle = events.Handle(callback, args, self)
        self._signal_handlers[sig] = handle

        try:
            # Register a dummy signal handler to ask Python to write the signal
            # number in the wakup file descriptor. _process_self_data() will
            # read signal numbers from this file descriptor to handle signals.
            if not _emscripten:
                signal.signal(sig, _sighandler_noop)

            # Set SA_RESTART to limit EINTR occurrences.
            if not _emscripten:
                signal.siginterrupt(sig, False)
        except OSError as exc:
            del self._signal_handlers[sig]
            if not self._signal_handlers:
                try:
                    signal.set_wakeup_fd(-1)
                except (ValueError, OSError) as nexc:
                    logger.info('set_wakeup_fd(-1) failed: %s', nexc)

            if exc.errno == errno.EINVAL:
                raise RuntimeError('sig {} cannot be caught'.format(sig))
            else:
                raise

    def _handle_signal(self, sig):
        """Internal helper that is the actual signal handler."""
        handle = self._signal_handlers.get(sig)
        if handle is None:
            return  # Assume it's some race condition.
        if handle._cancelled:
            self.remove_signal_handler(sig)  # Remove it properly.
        else:
            self._add_callback_signalsafe(handle)

    def remove_signal_handler(self, sig):
        """Remove a handler for a signal.  Em only.

        Return True if a signal handler was removed, False if not.
        """
        self._check_signal(sig)
        try:
            del self._signal_handlers[sig]
        except KeyError:
            return False

        if sig == signal.SIGINT:
            handler = signal.default_int_handler
        else:
            handler = signal.SIG_DFL

        try:
            if not _emscripten:
                signal.signal(sig, handler)
        except OSError as exc:
            if exc.errno == errno.EINVAL:
                raise RuntimeError('sig {} cannot be caught'.format(sig))
            else:
                raise

        if not self._signal_handlers:
            try:
                signal.set_wakeup_fd(-1)
            except (ValueError, OSError) as exc:
                logger.info('set_wakeup_fd(-1) failed: %s', exc)

        return True

    def _check_signal(self, sig):
        """Internal helper to validate a signal.

        Raise ValueError if the signal number is invalid or uncatchable.
        Raise RuntimeError if there is a problem setting up the handler.
        """
        if not isinstance(sig, int):
            raise TypeError('sig must be an int, not {!r}'.format(sig))

        if not (1 <= sig < signal.NSIG):
            raise ValueError(
                'sig {} out of range(1, {})'.format(sig, signal.NSIG))

    def _make_read_pipe_transport(self, pipe, protocol, waiter=None,
                                  extra=None):
        return _EmReadPipeTransport(self, pipe, protocol, waiter, extra)

    def _make_write_pipe_transport(self, pipe, protocol, waiter=None,
                                   extra=None):
        return _EmWritePipeTransport(self, pipe, protocol, waiter, extra)

    @coroutine
    def _make_subprocess_transport(self, protocol, args, shell,
                                   stdin, stdout, stderr, bufsize,
                                   extra=None, **kwargs):
        with events.get_child_watcher() as watcher:
            waiter = self.create_future()
            transp = _EmSubprocessTransport(self, protocol, args, shell,
                                              stdin, stdout, stderr, bufsize,
                                              waiter=waiter, extra=extra,
                                              **kwargs)

            watcher.add_child_handler(transp.get_pid(),
                                      self._child_watcher_callback, transp)
            try:
                yield from waiter
            except Exception as exc:
                # Workaround CPython bug #23353: using yield/yield-from in an
                # except block of a generator doesn't clear properly
                # sys.exc_info()
                err = exc
            else:
                err = None

            if err is not None:
                transp.close()
                yield from transp._wait()
                raise err

        return transp

    def _child_watcher_callback(self, pid, returncode, transp):
        self.call_soon_threadsafe(transp._process_exited, returncode)

    @coroutine
    def create_Em_connection(self, protocol_factory, path=None, *,
                               ssl=None, sock=None,
                               server_hostname=None):
        assert server_hostname is None or isinstance(server_hostname, str)
        if ssl:
            if server_hostname is None:
                raise ValueError(
                    'you have to pass server_hostname when using ssl')
        else:
            if server_hostname is not None:
                raise ValueError('server_hostname is only meaningful with ssl')

        if path is not None:
            if sock is not None:
                raise ValueError(
                    'path and sock can not be specified at the same time')

            path = os.fspath(path)
            sock = socket.socket(socket.AF_Em, socket.SOCK_STREAM, 0)
            try:
                sock.setblocking(False)
                yield from self.sock_connect(sock, path)
            except:
                sock.close()
                raise

        else:
            if sock is None:
                raise ValueError('no path and sock were specified')
            if (sock.family != socket.AF_Em or
                    not base_events._is_stream_socket(sock)):
                raise ValueError(
                    'A Em Domain Stream Socket was expected, got {!r}'
                    .format(sock))
            sock.setblocking(False)

        transport, protocol = yield from self._create_connection_transport(
            sock, protocol_factory, ssl, server_hostname)
        return transport, protocol

    @coroutine
    def create_Em_server(self, protocol_factory, path=None, *,
                           sock=None, backlog=100, ssl=None):
        if isinstance(ssl, bool):
            raise TypeError('ssl argument must be an SSLContext or None')

        if path is not None:
            if sock is not None:
                raise ValueError(
                    'path and sock can not be specified at the same time')

            path = os.fspath(path)
            sock = socket.socket(socket.AF_Em, socket.SOCK_STREAM)

            # Check for abstract socket. `str` and `bytes` paths are supported.
            if path[0] not in (0, '\x00'):
                try:
                    if stat.S_ISSOCK(os.stat(path).st_mode):
                        os.remove(path)
                except FileNotFoundError:
                    pass
                except OSError as err:
                    # Directory may have permissions only to create socket.
                    logger.error('Unable to check or remove stale Em socket '
                                 '%r: %r', path, err)

            try:
                sock.bind(path)
            except OSError as exc:
                sock.close()
                if exc.errno == errno.EADDRINUSE:
                    # Let's improve the error message by adding
                    # with what exact address it occurs.
                    msg = 'Address {!r} is already in use'.format(path)
                    raise OSError(errno.EADDRINUSE, msg) from None
                else:
                    raise
            except:
                sock.close()
                raise
        else:
            if sock is None:
                raise ValueError(
                    'path was not specified, and no sock specified')

            if (sock.family != socket.AF_Em or
                    not base_events._is_stream_socket(sock)):
                raise ValueError(
                    'A Em Domain Stream Socket was expected, got {!r}'
                    .format(sock))

        server = base_events.Server(self, [sock])
        sock.listen(backlog)
        sock.setblocking(False)
        self._start_serving(protocol_factory, sock, ssl, server)
        return server


class _EmReadPipeTransport(transports.ReadTransport):

    max_size = 256 * 1024  # max bytes we read in one event loop iteration

    def __init__(self, loop, pipe, protocol, waiter=None, extra=None):
        super().__init__(extra)
        self._extra['pipe'] = pipe
        self._loop = loop
        self._pipe = pipe
        self._fileno = pipe.fileno()
        self._protocol = protocol
        self._closing = False

        mode = os.fstat(self._fileno).st_mode
        if not (stat.S_ISFIFO(mode) or
                stat.S_ISSOCK(mode) or
                stat.S_ISCHR(mode)):
            self._pipe = None
            self._fileno = None
            self._protocol = None
            raise ValueError("Pipe transport is for pipes/sockets only.")

        os.set_blocking(self._fileno, False)

        self._loop.call_soon(self._protocol.connection_made, self)
        # only start reading when connection_made() has been called
        self._loop.call_soon(self._loop._add_reader,
                             self._fileno, self._read_ready)
        if waiter is not None:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, None)

    def __repr__(self):
        info = [self.__class__.__name__]
        if self._pipe is None:
            info.append('closed')
        elif self._closing:
            info.append('closing')
        info.append('fd=%s' % self._fileno)
        selector = getattr(self._loop, '_selector', None)
        if self._pipe is not None and selector is not None:
            polling = listactor_events._test_selector_event(
                          selector,
                          self._fileno, selectors.EVENT_READ)
            if polling:
                info.append('polling')
            else:
                info.append('idle')
        elif self._pipe is not None:
            info.append('open')
        else:
            info.append('closed')
        return '<%s>' % ' '.join(info)

    def _read_ready(self):
        try:
            data = os.read(self._fileno, self.max_size)
        except (BlockingIOError, InterruptedError):
            pass
        except OSError as exc:
            self._fatal_error(exc, 'Fatal read error on pipe transport')
        else:
            if data:
                self._protocol.data_received(data)
            else:
                if self._loop.get_debug():
                    logger.info("%r was closed by peer", self)
                self._closing = True
                self._loop._remove_reader(self._fileno)
                self._loop.call_soon(self._protocol.eof_received)
                self._loop.call_soon(self._call_connection_lost, None)

    def pause_reading(self):
        self._loop._remove_reader(self._fileno)

    def resume_reading(self):
        self._loop._add_reader(self._fileno, self._read_ready)

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        return self._protocol

    def is_closing(self):
        return self._closing

    def close(self):
        if not self._closing:
            self._close(None)

    def __del__(self):
        if self._pipe is not None:
            warnings.warn("unclosed transport %r" % self, ResourceWarning,
                          source=self)
            self._pipe.close()

    def _fatal_error(self, exc, message='Fatal error on pipe transport'):
        # should be called by exception handler only
        if (isinstance(exc, OSError) and exc.errno == errno.EIO):
            if self._loop.get_debug():
                logger.debug("%r: %s", self, message, exc_info=True)
        else:
            self._loop.call_exception_handler({
                'message': message,
                'exception': exc,
                'transport': self,
                'protocol': self._protocol,
            })
        self._close(exc)

    def _close(self, exc):
        self._closing = True
        self._loop._remove_reader(self._fileno)
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._pipe.close()
            self._pipe = None
            self._protocol = None
            self._loop = None


class _EmWritePipeTransport(transports._FlowControlMixin,
                              transports.WriteTransport):

    def __init__(self, loop, pipe, protocol, waiter=None, extra=None):
        super().__init__(extra, loop)
        self._extra['pipe'] = pipe
        self._pipe = pipe
        self._fileno = pipe.fileno()
        self._protocol = protocol
        self._buffer = bytearray()
        self._conn_lost = 0
        self._closing = False  # Set when close() or write_eof() called.

        mode = os.fstat(self._fileno).st_mode
        is_char = stat.S_ISCHR(mode)
        is_fifo = stat.S_ISFIFO(mode)
        is_socket = stat.S_ISSOCK(mode)
        if not (is_char or is_fifo or is_socket):
            self._pipe = None
            self._fileno = None
            self._protocol = None
            raise ValueError("Pipe transport is only for "
                             "pipes, sockets and character devices")

        os.set_blocking(self._fileno, False)
        self._loop.call_soon(self._protocol.connection_made, self)

        # On AIX, the reader trick (to be notified when the read end of the
        # socket is closed) only works for sockets. On other platforms it
        # works for pipes and sockets. (Exception: OS X 10.4?  Issue #19294.)
        if is_socket or (is_fifo and not sys.platform.startswith("aix")):
            # only start reading when connection_made() has been called
            self._loop.call_soon(self._loop._add_reader,
                                 self._fileno, self._read_ready)

        if waiter is not None:
            # only wake up the waiter when connection_made() has been called
            self._loop.call_soon(futures._set_result_unless_cancelled,
                                 waiter, None)

    def __repr__(self):
        info = [self.__class__.__name__]
        if self._pipe is None:
            info.append('closed')
        elif self._closing:
            info.append('closing')
        info.append('fd=%s' % self._fileno)
        selector = getattr(self._loop, '_selector', None)
        if self._pipe is not None and selector is not None:
            polling = listactor_events._test_selector_event(
                          selector,
                          self._fileno, selectors.EVENT_WRITE)
            if polling:
                info.append('polling')
            else:
                info.append('idle')

            bufsize = self.get_write_buffer_size()
            info.append('bufsize=%s' % bufsize)
        elif self._pipe is not None:
            info.append('open')
        else:
            info.append('closed')
        return '<%s>' % ' '.join(info)

    def get_write_buffer_size(self):
        return len(self._buffer)

    def _read_ready(self):
        # Pipe was closed by peer.
        if self._loop.get_debug():
            logger.info("%r was closed by peer", self)
        if self._buffer:
            self._close(BrokenPipeError())
        else:
            self._close()

    def write(self, data):
        assert isinstance(data, (bytes, bytearray, memoryview)), repr(data)
        if isinstance(data, bytearray):
            data = memoryview(data)
        if not data:
            return

        if self._conn_lost or self._closing:
            if self._conn_lost >= constants.LOG_THRESHOLD_FOR_CONNLOST_WRITES:
                logger.warning('pipe closed by peer or '
                               'os.write(pipe, data) raised exception.')
            self._conn_lost += 1
            return

        if not self._buffer:
            # Attempt to send it right away first.
            try:
                n = os.write(self._fileno, data)
            except (BlockingIOError, InterruptedError):
                n = 0
            except Exception as exc:
                self._conn_lost += 1
                self._fatal_error(exc, 'Fatal write error on pipe transport')
                return
            if n == len(data):
                return
            elif n > 0:
                data = memoryview(data)[n:]
            self._loop._add_writer(self._fileno, self._write_ready)

        self._buffer += data
        self._maybe_pause_protocol()

    def _write_ready(self):
        assert self._buffer, 'Data should not be empty'

        try:
            n = os.write(self._fileno, self._buffer)
        except (BlockingIOError, InterruptedError):
            pass
        except Exception as exc:
            self._buffer.clear()
            self._conn_lost += 1
            # Remove writer here, _fatal_error() doesn't it
            # because _buffer is empty.
            self._loop._remove_writer(self._fileno)
            self._fatal_error(exc, 'Fatal write error on pipe transport')
        else:
            if n == len(self._buffer):
                self._buffer.clear()
                self._loop._remove_writer(self._fileno)
                self._maybe_resume_protocol()  # May append to buffer.
                if self._closing:
                    self._loop._remove_reader(self._fileno)
                    self._call_connection_lost(None)
                return
            elif n > 0:
                del self._buffer[:n]

    def can_write_eof(self):
        return True

    def write_eof(self):
        if self._closing:
            return
        assert self._pipe
        self._closing = True
        if not self._buffer:
            self._loop._remove_reader(self._fileno)
            self._loop.call_soon(self._call_connection_lost, None)

    def set_protocol(self, protocol):
        self._protocol = protocol

    def get_protocol(self):
        return self._protocol

    def is_closing(self):
        return self._closing

    def close(self):
        if self._pipe is not None and not self._closing:
            # write_eof is all what we needed to close the write pipe
            self.write_eof()

    def __del__(self):
        if self._pipe is not None:
            warnings.warn("unclosed transport %r" % self, ResourceWarning,
                          source=self)
            self._pipe.close()

    def abort(self):
        self._close(None)

    def _fatal_error(self, exc, message='Fatal error on pipe transport'):
        # should be called by exception handler only
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
        self._close(exc)

    def _close(self, exc=None):
        self._closing = True
        if self._buffer:
            self._loop._remove_writer(self._fileno)
        self._buffer.clear()
        self._loop._remove_reader(self._fileno)
        self._loop.call_soon(self._call_connection_lost, exc)

    def _call_connection_lost(self, exc):
        try:
            self._protocol.connection_lost(exc)
        finally:
            self._pipe.close()
            self._pipe = None
            self._protocol = None
            self._loop = None


class _EmSubprocessTransport(base_subprocess.BaseSubprocessTransport):

    def _start(self, args, shell, stdin, stdout, stderr, bufsize, **kwargs):
        stdin_w = None
        if stdin == subprocess.PIPE:
            # Use a socket pair for stdin, since not all platforms
            # support selecting read events on the write end of a
            # socket (which we use in order to detect closing of the
            # other end).  Notably this is needed on AIX, and works
            # just fine on other platforms.
            stdin, stdin_w = socket.socketpair()
        self._proc = subprocess.Popen(
            args, shell=shell, stdin=stdin, stdout=stdout, stderr=stderr,
            universal_newlines=False, bufsize=bufsize, **kwargs)
        if stdin_w is not None:
            stdin.close()
            self._proc.stdin = open(stdin_w.detach(), 'wb', buffering=bufsize)


class AbstractChildWatcher:
    """Abstract base class for monitoring child processes.

    Objects derived from this class monitor a collection of subprocesses and
    report their termination or interruption by a signal.

    New callbacks are registered with .add_child_handler(). Starting a new
    process must be done within a 'with' block to allow the watcher to suspend
    its activity until the new process if fully registered (this is needed to
    prevent a race condition in some implementations).

    Example:
        with watcher:
            proc = subprocess.Popen("sleep 1")
            watcher.add_child_handler(proc.pid, callback)

    Notes:
        Implementations of this class must be thread-safe.

        Since child watcher objects may catch the SIGCHLD signal and call
        waitpid(-1), there should be only one active object per process.
    """

    def add_child_handler(self, pid, callback, *args):
        """Register a new child handler.

        Arrange for callback(pid, returncode, *args) to be called when
        process 'pid' terminates. Specifying another callback for the same
        process replaces the previous handler.

        Note: callback() must be thread-safe.
        """
        raise NotImplementedError()

    def remove_child_handler(self, pid):
        """Removes the handler for process 'pid'.

        The function returns True if the handler was successfully removed,
        False if there was nothing to remove."""

        raise NotImplementedError()

    def attach_loop(self, loop):
        """Attach the watcher to an event loop.

        If the watcher was previously attached to an event loop, then it is
        first detached before attaching to the new loop.

        Note: loop may be None.
        """
        raise NotImplementedError()

    def close(self):
        """Close the watcher.

        This must be called to make sure that any underlying resource is freed.
        """
        raise NotImplementedError()

    def __enter__(self):
        """Enter the watcher's context and allow starting new processes

        This function must return self"""
        raise NotImplementedError()

    def __exit__(self, a, b, c):
        """Exit the watcher's context"""
        raise NotImplementedError()


class BaseChildWatcher(AbstractChildWatcher):

    def __init__(self):
        self._loop = None
        self._callbacks = {}

    def close(self):
        self.attach_loop(None)

    def _do_waitpid(self, expected_pid):
        raise NotImplementedError()

    def _do_waitpid_all(self):
        raise NotImplementedError()

    def attach_loop(self, loop):
        assert loop is None or isinstance(loop, events.AbstractEventLoop)

        if self._loop is not None and loop is None and self._callbacks:
            warnings.warn(
                'A loop is being detached '
                'from a child watcher with pending handlers',
                RuntimeWarning)

        if self._loop is not None:
            self._loop.remove_signal_handler(signal.SIGCHLD)

        self._loop = loop
        if loop is not None:
            loop.add_signal_handler(signal.SIGCHLD, self._sig_chld)

            # Prevent a race condition in case a child terminated
            # during the switch.
            self._do_waitpid_all()

    def _sig_chld(self):
        try:
            self._do_waitpid_all()
        except Exception as exc:
            # self._loop should always be available here
            # as '_sig_chld' is added as a signal handler
            # in 'attach_loop'
            self._loop.call_exception_handler({
                'message': 'Unknown exception in SIGCHLD handler',
                'exception': exc,
            })

    def _compute_returncode(self, status):
        if os.WIFSIGNALED(status):
            # The child process died because of a signal.
            return -os.WTERMSIG(status)
        elif os.WIFEXITED(status):
            # The child process exited (e.g sys.exit()).
            return os.WEXITSTATUS(status)
        else:
            # The child exited, but we don't understand its status.
            # This shouldn't happen, but if it does, let's just
            # return that status; perhaps that helps debug it.
            return status


class SafeChildWatcher(BaseChildWatcher):
    """'Safe' child watcher implementation.

    This implementation avoids disrupting other code spawning processes by
    polling explicitly each process in the SIGCHLD handler instead of calling
    os.waitpid(-1).

    This is a safe solution but it has a significant overhead when handling a
    big number of children (O(n) each time SIGCHLD is raised)
    """

    def close(self):
        self._callbacks.clear()
        super().close()

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        pass

    def add_child_handler(self, pid, callback, *args):
        if self._loop is None:
            raise RuntimeError(
                "Cannot add child handler, "
                "the child watcher does not have a loop attached")

        self._callbacks[pid] = (callback, args)

        # Prevent a race condition in case the child is already terminated.
        self._do_waitpid(pid)

    def remove_child_handler(self, pid):
        try:
            del self._callbacks[pid]
            return True
        except KeyError:
            return False

    def _do_waitpid_all(self):

        for pid in list(self._callbacks):
            self._do_waitpid(pid)

    def _do_waitpid(self, expected_pid):
        assert expected_pid > 0

        try:
            pid, status = os.waitpid(expected_pid, os.WNOHANG)
        except ChildProcessError:
            # The child process is already reaped
            # (may happen if waitpid() is called elsewhere).
            pid = expected_pid
            returncode = 255
            logger.warning(
                "Unknown child process pid %d, will report returncode 255",
                pid)
        else:
            if pid == 0:
                # The child process is still alive.
                return

            returncode = self._compute_returncode(status)
            if self._loop.get_debug():
                logger.debug('process %s exited with returncode %s',
                             expected_pid, returncode)

        try:
            callback, args = self._callbacks.pop(pid)
        except KeyError:  # pragma: no cover
            # May happen if .remove_child_handler() is called
            # after os.waitpid() returns.
            if self._loop.get_debug():
                logger.warning("Child watcher got an unexpected pid: %r",
                               pid, exc_info=True)
        else:
            callback(pid, returncode, *args)


class FastChildWatcher(BaseChildWatcher):
    """'Fast' child watcher implementation.

    This implementation reaps every terminated processes by calling
    os.waitpid(-1) directly, possibly breaking other code spawning processes
    and waiting for their termination.

    There is no noticeable overhead when handling a big number of children
    (O(1) each time a child terminates).
    """
    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()
        self._zombies = {}
        self._forks = 0

    def close(self):
        self._callbacks.clear()
        self._zombies.clear()
        super().close()

    def __enter__(self):
        with self._lock:
            self._forks += 1

            return self

    def __exit__(self, a, b, c):
        with self._lock:
            self._forks -= 1

            if self._forks or not self._zombies:
                return

            collateral_victims = str(self._zombies)
            self._zombies.clear()

        logger.warning(
            "Caught subprocesses termination from unknown pids: %s",
            collateral_victims)

    def add_child_handler(self, pid, callback, *args):
        assert self._forks, "Must use the context manager"

        if self._loop is None:
            raise RuntimeError(
                "Cannot add child handler, "
                "the child watcher does not have a loop attached")

        with self._lock:
            try:
                returncode = self._zombies.pop(pid)
            except KeyError:
                # The child is running.
                self._callbacks[pid] = callback, args
                return

        # The child is dead already. We can fire the callback.
        callback(pid, returncode, *args)

    def remove_child_handler(self, pid):
        try:
            del self._callbacks[pid]
            return True
        except KeyError:
            return False

    def _do_waitpid_all(self):
        # Because of signal coalescing, we must keep calling waitpid() as
        # long as we're able to reap a child.
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                # No more child processes exist.
                return
            else:
                if pid == 0:
                    # A child process is still alive.
                    return

                returncode = self._compute_returncode(status)

            with self._lock:
                try:
                    callback, args = self._callbacks.pop(pid)
                except KeyError:
                    # unknown child
                    if self._forks:
                        # It may not be registered yet.
                        self._zombies[pid] = returncode
                        if self._loop.get_debug():
                            logger.debug('unknown process %s exited '
                                         'with returncode %s',
                                         pid, returncode)
                        continue
                    callback = None
                else:
                    if self._loop.get_debug():
                        logger.debug('process %s exited with returncode %s',
                                     pid, returncode)

            if callback is None:
                logger.warning(
                    "Caught subprocess termination from unknown pid: "
                    "%d -> %d", pid, returncode)
            else:
                callback(pid, returncode, *args)


class DefaultEventLoopPolicy(events.BaseDefaultEventLoopPolicy):
    """event loop policy with a watcher for child processes."""
    _loop_factory = SelectorEventLoop

    def __init__(self):
        super().__init__()
        self._watcher = None

    def _init_watcher(self):
        with events._lock:
            if self._watcher is None:  # pragma: no branch
                self._watcher = SafeChildWatcher()
                if isinstance(threading.current_thread(),
                              threading._MainThread):
                    self._watcher.attach_loop(self._local._loop)

    def set_event_loop(self, loop):
        """Set the event loop.

        As a side effect, if a child watcher was set before, then calling
        .set_event_loop() from the main thread will call .attach_loop(loop) on
        the child watcher.
        """

        super().set_event_loop(loop)

        if (self._watcher is not None and
                isinstance(threading.current_thread(), threading._MainThread)):
            self._watcher.attach_loop(loop)

    def get_child_watcher(self):
        """Get the watcher for child processes.

        If not yet set, a SafeChildWatcher object is automatically created.
        """
        if self._watcher is None:
            self._init_watcher()

        return self._watcher

    def set_child_watcher(self, watcher):
        """Set the watcher for child processes."""

        assert watcher is None or isinstance(watcher, AbstractChildWatcher)

        if self._watcher is not None:
            self._watcher.close()

        self._watcher = watcher


