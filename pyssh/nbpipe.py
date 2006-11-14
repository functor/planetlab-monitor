"""Implements a non-blocking pipe class."""

# Since it uses thread rather than select, it is portable to at least
# posix and windows environments.

# Author: Rasjid Wilcox, copyright (c) 2002
# Ideas taken from the Python 2.2 telnetlib.py library.
#
# Last modified: 3 August 2002
# Licence: Python 2.2 Style License.  See license.txt.

# TO DO:
#     * Handle excpetions better, particularly Keyboard Interupts.
#     * Possibly do a threadless version for posix environments
#       where we can use select (is probably more efficient).
#     * A test function.

import Queue
import thread
import os
import time
import types

#INT_TYPE = type(1)
MIN_TIMEOUT = 0.01

class nbpipe:
    def __init__(self, readfile, pipesize=0, blocksize=1024):
        """Initialise a non-blocking pipe object, given a real file or file-descriptor.
        pipesize = the size (in blocks) of the queue used to buffer the blocks read
        blocksize = the maximum block size for a raw read."""
        if type(readfile) == types.IntType:
            self.fd = readfile
        else:
            self.fd = readfile.fileno()
        self.pipesize = pipesize
        self.blocksize = blocksize
        self.eof = 0
        self._q = Queue.Queue(self.pipesize)
        self.data = ''
        thread.start_new_thread(self._readtoq, ())
    def _readtoq(self):
        finish = 0
        while (1):
            try:
                item = os.read(self.fd, self.blocksize)
            except (IOError, OSError):
                finish = 1
            if (item == '') or finish:
                # Wait until everything has been read from the queue before
                # setting eof = 1 and exiting.
                while not self._q.empty():
                    time.sleep(MIN_TIMEOUT)
                self.eof = 1
                thread.exit()
            else:
                self._q.put(item)
    def has_data(self):
        return self.data
    def eof(self):
        return self.eof
    def read_lazy(self):
        """Process and return data that's already in the queues (lazy).

        Return '' if no data available. Don't block.

        """
        while not self._q.empty():
            self.data += self._q.get()
        data = self.data
        self.data = ''
        return data
    def read_some(self, until_eof=False):
        """Read at least one byte of cooked data unless EOF is hit.

        Return '' if EOF is hit.  Block if no data is immediately
        available.

        """
        data = ''
        while (until_eof or not data) and not self.eof:
            data += self.read_lazy()
            time.sleep(MIN_TIMEOUT)
        return data
    def read_until(self, match, timeout=None):
        """Read until a given string is encountered or until timeout.

        If no match is found or EOF is hit, return whatever is
        available instead, possibly the empty string.
        """
        if timeout is not None:
            timeout = timeout / MIN_TIMEOUT
        else:
            timeout = 1
        n = len(match)
        data = self.read_lazy()
        i = 0
        while timeout >= 0 and not self.eof:
            i = data.find(match, i)
            if i >= 0:
                i += n
                self.data = data[i:]
                return data[:i]
            time.sleep(MIN_TIMEOUT)
            timeout -= 1
            i = max(0, len(data) - n)
            data += self.read_lazy()
        return data
    def read_all(self):
        """Read until the EOF. May block."""
        return read_some(until_eof=True)
