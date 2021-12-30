# A simple generator wrapper, not sure if it's good for anything at all.
# With basic python threading
from threading import Thread
import traceback

try:
    from queue import Queue

except ImportError:
    from Queue import Queue


class ThreadedGenerator(object):
    """
    Generator that runs on a separate thread, returning values to calling
    thread. Care must be taken that the iterator does not mutate any shared
    variables referenced in the calling thread.
    """

    def __init__(self, iterator,
                 sentinel=object(),
                 queue_maxsize=0,
                 daemon=False,
                 Thread=Thread,
                 Queue=Queue):
        self._daemon = daemon
        self._iterator = iterator
        self._sentinel = sentinel
        self._queue = Queue(maxsize=queue_maxsize)
        self._thread_class = Thread

    def __repr__(self):
        return 'ThreadedGenerator({!r})'.format(self._iterator)

    def _start_threads(self, count):
        threads = []
        for i in range(count):
            t = self._make_thread(repr(self._iterator)+str(i))
            t.start()
            threads.append(t)
        return threads

    def _join_threads(self, threads):
        for t in threads:
            t.join()

    def _make_thread(self, name):
        t = self._thread_class(
            name=name,
            target=self._run
        )
        t.daemon = self._daemon
        return t

    def _run(self):
        while True:
            try:
                value = next(self._iterator)
                self._queue.put(value)

            finally:
                self._queue.put(self._sentinel)
                break

    def __iter__(self):
        self._threads = self._start_threads(3)

        for value in iter(self._queue.get, self._sentinel):
            yield value

        self._join_threads(self._threads)