#! /usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import threading
import traceback

try:
    from queue import Queue, Empty
except ImportError:  # PY2
    from Queue import Queue, Empty


# Copied from: media-dubiety:threads.py

class ThreadPoolThread(threading.Thread):
    def __init__(self, name, queue):
        super(ThreadPoolThread, self).__init__(name=name)
        self.stop_event = threading.Event()
        self.queue = queue

    def run(self):
        while True:
            try:
                f = self.queue.get(True, 1)
            except Empty:
                if self.stop_event.isSet():
                    raise SystemExit
            else:
                try:
                    f()
                except Exception:
                    traceback.print_exc()
                finally:
                    self.queue.task_done()

    def stop(self):
        self.stop_event.set()


class ThreadPool(object):
    def __init__(self, size, name='Pool'):
        self.lock = threading.RLock()
        self.name = name
        self.running = False
        self.threads = []
        self.size = 0
        self.queue = Queue()

        self.incr(size)

    def incr(self, n):
        with self.lock:
            for i in range(n):
                self.size += 1
                thr = ThreadPoolThread(
                    '%s-%d' % (self.name, self.size),
                    self.queue
                )
                self.threads.append(thr)
                if self.running:
                    thr.start()

    def decr(self, n):
        with self.lock:
            for i in range(n):
                self.size -= 1
                thr = self.threads.pop()
                if self.running:
                    thr.stop()

    def start(self):
        with self.lock:
            self.running = True
            for thr in self.threads:
                thr.start()

    def join(self):
        return self.queue.join()

    def stop(self):
        with self.lock:
            self.decr(self.size)
            self.running = False

    def process(self, f):
        # if self.queue.qsize() > self.size:
        #     pywikibot.warning('%s "%s" size exceeded %d. Current: %d' % (
        #         self.__class__.__name__,
        #         self.name,
        #         self.size,
        #         self.queue.qsize()
        #     ))
        self.queue.put(f)

    def isAlive(self):
        return bool(self.size) and self.running


def concurrent_map(function, *argss, **kwargs):
    n_threads = 8  # Due to GIL, too many threads break stuffs
    if kwargs:
        if tuple(kwargs) != ('n_threads'):
            raise ValueError
        n_threads = kwargs['n_threads']

    argss = list(zip(*argss))

    dest = [None] * len(argss)

    pool = ThreadPool(n_threads)
    pool.start()

    def make_job(i, args):
        def job():
            dest[i] = function(*args)
        return job

    for i, args in enumerate(argss):
        pool.process(make_job(i, args))

    pool.join()
    pool.stop()

    return dest
