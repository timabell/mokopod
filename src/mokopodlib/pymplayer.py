#!/usr/bin/env python
# -*- coding: utf-8 -*-
# $Id: pymplayer.py 567 2009-02-10 04:34:33Z darwin $
#
# Copyright (C) 2007-2008  UP EEEI Computer Networks Laboratory
# Copyright (C) 2007-2009  Darwin M. Bautista <djclue917@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Thin, out-of-source wrapper and client/server for MPlayer

Classes:

MPlayer -- thin, out-of-process wrapper for MPlayer
Server -- asynchronous server that manages an MPlayer instance
Client -- client for sending MPlayer commands

Function:

loop() -- the asyncore.loop function, provided here for convenience

Constants:

PIPE -- subprocess.PIPE, provided here for convenience
STDOUT -- subprocess.STDOUT, provided here for convenience

"""

import sys

sys.path.append('/usr/lib/site-python')

import socket
from mokopodlib import asyncore
from mokopodlib import asynchat
from select import select
from subprocess import Popen, PIPE, STDOUT


__all__ = [
    'MPlayer',
    'Server',
    'Client',
    'loop',
    'PIPE',
    'STDOUT'
    ]

__version__ = '0.4.0'
__author__ = 'Darwin M. Bautista <djclue917@gmail.com>'


# For convenience
loop = asyncore.loop


class MPlayer(object):
    """MPlayer(args=())

    An out-of-process wrapper for MPlayer. It provides the basic
    interface for sending commands and receiving responses to and from
    MPlayer. Take note that MPlayer is always started in 'slave',
    'idle', and 'quiet' modes.

    @class attribute executable: path to or filename of MPlayer
    @property args: MPlayer arguments
    @property stdout: process' stdout (read-only)
    @property stderr: process' stderr (read-only)

    """

    executable = 'mokopod_mplayer'

    def __init__(self, args=()):
        self.args = args
        self._process = None
        self._stdout = _file()
        self._stderr = _file()

    def __del__(self):
        # Be sure to stop the MPlayer process.
        self.quit()

    @staticmethod
    def _check_command_args(name, types, min_argc, max_argc, args):
        argc = len(args) + 1
        if not min_argc and argc:
            raise TypeError('%s() takes no arguments (%d given)' %
                (name, argc))
        if argc < min_argc:
            s = ('s' if min_argc > 1 else '')
            raise TypeError('%s() takes at least %d argument%s (%d given)' %
                (name, min_argc, s, argc))
        if min_argc == max_argc and argc != max_argc:
            s = ('s' if max_argc > 1 else '')
            raise TypeError('%s() takes exactly %d argument%s (%d given)' %
                (name, max_argc, s, argc))
        if argc > max_argc:
            s = ('s' if max_argc > 1 else '')
            raise TypeError('%s() takes at most %d argument%s (%d given)' %
                (name, max_argc, s, argc))
        for i in xrange(argc - 1):
            if not isinstance(args[i], types[i]):
                raise TypeError('%s() argument %d should be %s' %
                    (name, i + 1, types[i].__name__.replace('base', '')))

    def _get_args(self):
        return self._args[3:]

    def _set_args(self, args):
        _args = ['-slave', '-idle', '-quiet']
        try:
            _args.extend(args)
        except TypeError:
            raise TypeError('args should be an iterable')
        for i in xrange(3, len(_args)):
            if not isinstance(_args[i], basestring):
                _args[i] = str(_args[i])
        self._args = _args

    args = property(_get_args, _set_args, doc='list of MPlayer arguments')

    @property
    def stdout(self):
        """stdout of the MPlayer process"""
        return self._stdout

    @property
    def stderr(self):
        """stderr of the MPlayer process"""
        return self._stderr

    @classmethod
    def introspect(cls):
        """Introspect the MPlayer executable

        Generate methods based on the available commands. The generated
        methods check the number and type of the passed parameters.
        """
        args = [cls.executable, '-input', 'cmdlist', '-really-quiet']
        try:
            mplayer = Popen(args, bufsize=1, stdout=PIPE)
        except OSError:
            return False
        types = {'integer': int, 'float': float, 'string': basestring}
        for line in mplayer.communicate()[0].split('\n'):
            if not line or line.startswith('quit') or \
               line.startswith('get_property'):
                continue
            args = line.lower().split()
            name = args.pop(0)
            if not name.startswith('get_'):
                required = 0
                for arg in args:
                    if not arg.startswith('['):
                        required += 1
                arg_types = str([types[arg.strip('[]')].__name__ for arg in
                    args]).replace("'", '')
                code = '''
                def %(name)s(self, *args):
                    """%(name)s(%(args)s)"""
                    try:
                        self._check_command_args('%(name)s', %(types)s,
                            %(min_argc)d, %(max_argc)d, args)
                    except TypeError, msg:
                        raise TypeError(msg)
                    return self.command('%(name)s', *args)
                ''' % dict(
                    name = name, args = ', '.join(args), types = arg_types,
                    min_argc = required + 1, max_argc = len(args) + 1
                )
            else:
                code = '''
                def %(name)s(self, timeout=0.25):
                    """%(name)s(timeout=0.25)"""
                    try:
                        return self.query('%(name)s', timeout)
                    except TypeError, msg:
                        raise TypeError(msg)
                ''' % dict(name = name)
            scope = {}
            exec code.strip() in globals(), scope
            setattr(cls, name, scope[name])
        # Just manually define get_property
        def get_property(self, name, timeout=0.25):
            """get_property(name, timeout=0.25)"""
            if not isinstance(name, basestring):
                raise TypeError('property name should be a string')
            return self.query(' '.join(['get_property', name]), timeout)
        cls.get_property = get_property
        return True

    def start(self, stdout=None, stderr=None):
        """Start the MPlayer process.

        @param stdout: subprocess.PIPE | None
        @param stderr: subprocess.PIPE | subprocess.STDOUT | None

        Returns True on success, False on failure, or None if MPlayer
        is already running. stdout/stderr will be PIPEd regardless of
        the passed parameters if subscribers were added to them.

        """
        if stdout not in (PIPE, None):
            raise ValueError('stdout should either be PIPE or None')
        if stderr not in (PIPE, STDOUT, None):
            raise ValueError('stderr should be one of PIPE, STDOUT, or None')
        if not self.is_alive():
            args = [self.__class__.executable]
            args.extend(self._args)
            # Force PIPE if subscribers were added
            if self._stdout._subscribers:
                stdout = PIPE
            if self._stderr._subscribers:
                stderr = PIPE
            try:
                # Start the MPlayer process (unbuffered)
                self._process = Popen(args, stdin=PIPE, stdout=stdout,
                    stderr=stderr)
            except OSError:
                return False
            else:
                if self._process.stdout is not None:
                    self._stdout._bind(self._process.stdout)
                if self._process.stderr is not None:
                    self._stderr._bind(self._process.stderr)
                return True

    def quit(self, retcode=0):
        """Stop the MPlayer process.

        Returns the exit status of MPlayer or None if not running.

        """
        if self.is_alive():
            self._stdout._unbind()
            self._stderr._unbind()
            self._process.stdin.write('quit %d\n' % (retcode, ))
            return self._process.wait()

    def is_alive(self):
        """Check if MPlayer process is alive.

        Returns True if alive, else, returns False.

        """
        if self._process is not None:
            return (self._process.poll() is None)
        else:
            return False

    def command(self, name, *args):
        """Send a command to MPlayer.

        @param name: command string

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        """
        if not isinstance(name, basestring):
            raise TypeError('command name should be a string')
        if 'quit'.startswith(name.split()[0].lower()):
            raise ValueError('use the quit() method instead')
        if self.is_alive() and name:
            command = ['pausing_keep', name]
            command.extend([str(arg) for arg in args])
            command.append('\n')
            self._process.stdin.write(' '.join(command))

    def query(self, name, timeout=0.25):
        """Send a query to MPlayer. The result is returned, if there is any.

        query() will first consume all data in stdout before proceeding.
        This is to ensure that it'll get the response from the command
        given and not just some random data.

        WARNING: This function is not thread-safe. You might want to implement
                 a locking mechanism to ensure that you get the correct result
        """
        if not isinstance(timeout, (int, float)):
            raise TypeError('timeout should either be int or float')
        if self._stdout._file is not None and name.lower().startswith('get_'):
            self._stdout._query_in_progress = True
            # Consume all data in stdout before proceeding
            while self._stdout.readline() is not None:
                pass
            self.command(name)
            response = self._stdout.readline(timeout) or ''
            self._stdout._query_in_progress = False
            if not response.startswith('ANS_'):
                return None
            ans = response.split('=')[1].strip('\'"')
            if ans.isdigit():
                ans = int(ans)
            elif ans.count('.') == 1:
                try:
                    ans = float(ans)
                except ValueError:
                    pass
            return ans


class Server(asyncore.dispatcher):
    """Server(mplayer, port, host='', max_conn=1)

    The log method can be overridden to provide more sophisticated
    logging and warning methods.

    """

    def __init__(self, mplayer, port, host='', max_conn=1):
        asyncore.dispatcher.__init__(self)
        self._mplayer = mplayer
        self._max_conn = max_conn
        self._channels = {}
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(self._max_conn)
        self.log('Server started.')

    def __del__(self):
        self.stop()

    def writable(self):
        return False

    def handle_close(self):
        for channel in self._channels.values():
            channel.handle_close()
        self.close()
        self.log('Server closed.')

    stop = handle_close

    def handle_accept(self):
        conn, addr = self.accept()
        if len(self._channels) < self._max_conn:
            self.log('Connection accepted: %s' % (addr, ))
            # Dispatch connection to a _ClientHandler
            _ClientHandler(self._channels, self._mplayer, conn, self.log)
        else:
            self.log('Max number of connections reached, rejected: %s' %
                (addr, ))
            conn.close()


class Client(asynchat.async_chat):
    """Client()

    The PyMPlayer Client

    """

    ac_in_buffer_size = 512
    ac_out_buffer_size = 512

    def __init__(self):
        asynchat.async_chat.__init__(self)
        self.buffer = []
        self.set_terminator('\r\n')

    def handle_connect(self):
        return

    def handle_error(self):
        self.close()
        raise socket.error('Connection lost.')

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.buffer)
        self.buffer = []
        self.handle_data(data)

    def handle_data(self, data):
        self.log(data)

    def connect(self, (host, port)):
        if self.connected:
            return
        if self.socket:
            self.close()
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        asynchat.async_chat.connect(self, (host, port))

    def send_command(self, cmd):
        """Send an MPlayer command to the server

        @param cmd: valid MPlayer command

        Valid MPlayer commands are documented in:
        http://www.mplayerhq.hu/DOCS/tech/slave.txt

        """
        self.push(''.join([cmd, '\r\n\r\n']))
        if 'quit'.startswith(cmd.split()[0].lower()):
            self.close()
            return False
        else:
            return True


class _ClientHandler(asynchat.async_chat):
    """Handler for Client connections"""

    ac_in_buffer_size = 512
    ac_out_buffer_size = 512

    def __init__(self, connections, mplayer, conn, log):
        asynchat.async_chat.__init__(self, conn)
        self.add_channel(connections)
        self.set_terminator('\r\n\r\n')
        self.connections = connections
        self.mplayer = mplayer
        # hook handle_mplayer_data method to mplayer's stdout
        self.mplayer.stdout.attach(self.handle_mplayer_data)
        self.log = log
        self.buffer = []

    def handle_close(self):
        self.mplayer.stdout.detach(self.handle_mplayer_data)
        del self.connections[self._fileno]
        self.close()
        self.log('Connection closed: %s' % (self.addr, ))

    def collect_incoming_data(self, data):
        self.buffer.append(data)

    def found_terminator(self):
        data = ''.join(self.buffer)
        self.buffer = []
        self.handle_data(data)

    def handle_data(self, data):
        if not data or 'quit'.startswith(data.split()[0].lower()):
            self.handle_close()
        elif data.lower() == 'reload':
            # then restart the MPlayer process;
            self.mplayer.quit()
            self.mplayer.start()
        else:
            self.mplayer.command(data)

    def handle_mplayer_data(self, data):
        if data.startswith('ANS_'):
            self.push(''.join([data, '\r\n']))


class _file_dispatcher(asyncore.file_dispatcher):
    """asyncore.file_dispatcher-like class that doesn't set fd non-blocking"""

    def __init__(self, fd, callback):
        # This is intended. We don't want asyncore.file_dispatcher.__init__()
        # to make fd non-blocking since it causes problems with MPlayer.
        asyncore.dispatcher.__init__(self)
        self.connected = True
        self.set_file(fd)
        self.handle_read = callback


class _file(object):
    """Wrapper for stdout and stderr

    Exposes the fileno() and readline() methods
    Provides methods for management of subscribers (data handlers)
    """

    def __init__(self):
        self._file = None
        self._subscribers = []
        self._query_in_progress = False

    def _bind(self, file):
        self._unbind()
        self._file = file
        _file_dispatcher(file.fileno(), self.publish)

    def _unbind(self):
        if self._file is not None and \
           asyncore.socket_map.has_key(self._file.fileno()):
            del asyncore.socket_map[self._file.fileno()]
        self._file = None

    def fileno(self):
        if self._file is not None:
            return self._file.fileno()

    def readline(self, timeout=0):
        if self._file is not None and \
           any(select([self._file], [], [], timeout)):
            return self._file.readline().rstrip()

    def attach(self, subscriber):
        if not callable(subscriber):
            raise TypeError('subscriber should be callable')
        try:
            self._subscribers.index(subscriber)
        except ValueError:
            self._subscribers.append(subscriber)

    def detach(self, subscriber):
        try:
            self._subscribers.remove(subscriber)
        except ValueError:
            return False
        else:
            return True

    def publish(self, *args):
        """Publish data to subscribers

        This is a callback for use with event loops of other frameworks.
        It is NOT meant to be called manually.

        m.stdout.attach(handle_player_data)
        m.start()

        fd = m.stdout.fileno()
        cb = m.stdout.publish

        gobject.io_add_watch(fd, gobject.IO_IN|gobject.IO_PRI, cb)
        tkinter.createfilehandler(fd, tkinter.READABLE, cb)

        """
        if self._query_in_progress:
            return True
        data = self._file.readline().rstrip()
        if not data:
            return True
        for subscriber in self._subscribers:
            if callable(subscriber):
                subscriber(data)
            else:
                self._subscribers.remove(subscriber)
        return True


if __name__ == '__main__':
    import sys
    import signal

    def handle_data(data):
        print 'mplayer: ', data

    player = MPlayer()
    player.args = sys.argv[1:]
    player.stdout.attach(handle_data)
    player.start()

    signal.signal(signal.SIGTERM, lambda s, f: player.quit())
    signal.signal(signal.SIGINT, lambda s, f: player.quit())
    loop()
