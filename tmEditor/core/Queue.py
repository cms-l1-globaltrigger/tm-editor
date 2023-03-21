"""Simple callback queue class executing a chain of callbacks by iteration.

Setup a callbalc queue.

>>> q = Queue()
>>> worker = MyWorker()
>>> q.add_callback(worker.load, "loading data")
>>> q.add_callback(worker.process, "processing data")
>>> q.add_callback(worker.save, "saving data")

Executing th callback queue.

>>> for callback in q:
...     print(q.message(), "...", q.progress(), "%")
...     q.callback()
loading data ... 0 %
processing data ... 33 %
saving data ... 66 %
"""

from typing import Callable, List


class Callback:

    def __init__(self, callback: Callable, message: str):
        self.callback: Callable = callback
        self.message: str = message or ""


class Queue:

    def __init__(self) -> None:
        self.__callbacks: List[Callback] = []
        self.__count: int = 0
        self.__message: str = ""

    def add_callback(self, callback: Callable, message: str) -> None:
        self.__callbacks.append(Callback(callback, message))

    def progress(self) -> int:
        return int(round(100. / len(self.__callbacks) * self.__count))

    def message(self) -> str:
        return self.__message

    def __iter__(self):
        return self

    def __next__(self):
        """Python3 version."""
        if self.__count >= len(self.__callbacks):
            raise StopIteration()
        callback = self.__callbacks[self.__count]
        self.__message = callback.message
        self.__count += 1
        return callback.callback

    def exec_(self) -> None:
        for callback in self:
            callback()
