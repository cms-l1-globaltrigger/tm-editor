# -*- coding: utf-8 -*-
#
# Repository path   : $HeadURL:  $
# Last committed    : $Revision:  $
# Last changed by   : $Author:  $
# Last changed date : $Date: $
#

"""Simple callback queue class executing a chain of callbacks by iteration.

Setup a callbalc queue.

>>> q = Queue()
>>> worker = MyWorker()
>>> q.add_callback(worker.load, "loading data")
>>> q.add_callback(worker.process, "processing data")
>>> q.add_callback(worker.save, "saving data")

Executing th callback queue.

>>> for callback in q:
...     print q.message(), '...', q.progress(), '%'
...     q.callback()
loading data ... 0 %
processing data ... 33 %
saving data ... 66 %
"""

class Callback(object):

    def __init__(self, callback, message=None):
        self.callback = callback
        self.message = message or ""

class Queue(object):

    def __init__(self):
        self.__callbacks = []
        self.__ptr = 0
        self.__message = ""

    def add_callback(self, callback, message=None):
        self.__callbacks.append(Callback(callback, message))

    def progress(self):
        return 100. / len(self.__callbacks) * self.__ptr

    def message(self):
        return self.__message

    def __iter__(self):
        return self

    def __next__(self):
        """Python3 version."""
        if self.__ptr >= len(self.__callbacks):
            raise StopIteration()
        callback = self.__callbacks[self.__ptr]
        self.__message = callback.message
        self.__ptr += 1
        return callback.callback

    def next(self):
        """Python2 fallback."""
        return self.__next__()

    def exec_(self):
        for callback in self:
            callback()
