# -*- coding: utf-8 -*-
"""
Python library to work with CouchDB and to save python objects, handles conflict resolution on class attribute level.
This source code is property of Active8 BV
Copyright (C)
Erik de Jonge <erik@a8.nl>
Actve8 BV
Rotterdam
www.a8.nl
"""
import os
import redis
import traceback
import uuid
import threading
import math
import time
import types
import urlparse
import tempfile
import glob
import copy
import subprocess
import base64
import cPickle
import logging
import urllib
import itertools
import random
import string
import cStringIO
import cjson
import sys
import inspect
from urlparse import urljoin
import json
import couchdb
import inflection
import requests
import telnetlib
import socket
import multiprocessing
import multiprocessing.dummy
import boto
from redis.exceptions import ResponseError

#noinspection PyUnresolvedReferences
from boto.gs.connection import Location
from boto.exception import GSResponseError, InvalidUriError
import gslib.command
import gslib.util

#noinspection PyUnresolvedReferences
from gslib.third_party.oauth2_plugin import oauth2_client, oauth2_plugin
from gslib.util import MultiprocessingIsAvailable
import googledatastore as datastore
from googledatastore.helper import *
reload(sys)

#noinspection PyUnresolvedReferences
sys.setdefaultencoding("utf-8")


GLOBAL_HOSTNAME = socket.gethostname()
CRYPTODOCFOLDERGOOGLE = "crypto_docs"


gslib.util.InitializeMultiprocessingVariables()


gslib.command.InitializeMultiprocessingVariables()


oauth2_client.InitializeMultiprocessingVariables()


def pretty_print_json(jsondata, tofilename=None):
    """
    @type jsondata: str
    @type tofilename: str, None
    """
    jsonproxy = cjson.decode(jsondata)

    if tofilename is None:
        return json.dumps(jsonproxy, sort_keys=True, indent=4, separators=', ')
    else:
        json.dump(jsonproxy, open(tofilename, "w"), sort_keys=True, indent=4, separators=(',', ': '))
        return tofilename


class FastList(object):
    """
    FastList
    """

    def __init__(self):
        """
        __init__
        """
        self.dictlist = {}

    def add(self, o):
        """
        @type o: object
        """
        self.dictlist[o] = 1

    def delete(self, o):
        """
        @type o: str
        """
        if o in self.dictlist:
            del self.dictlist[o]

    def has(self, o):
        """
        @type o: object
        """
        return o in self.dictlist

    def ilist(self):
        """
        list
        """
        return iter(self.dictlist.keys())

    def list(self):
        """
        list
        """
        return self.dictlist.keys()

    def size(self):
        """
        size
        """
        return len(self.dictlist.keys())


def get_hostname():
    """
    get_hostname
    """
    return str(socket.gethostname())


def get_alphabet():
    """
    get_alphabetget_safe_alphabet
    """
    return tuple(['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', ' ', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])


def get_safe_alphabet():
    """
    get_alphabet
    """
    return tuple(['~', '_', '.', '-', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])


def get_alphabet_lower():
    """
    get_alphabet_lower
    """
    return tuple(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'])


def get_alphabet_lower_numbers():
    """
    get_alphabet_lower_numbers
    """
    return tuple(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'])


def get_vowels_lower():
    """
    get_vowels_lower
    """
    return tuple(['a', 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'y', 'z'])


def cb_replace(thestring, listofreplacements, count=None):
    """
    @type thestring: str
    @type listofreplacements: list, str
    @type count: int, None
    """
    if not isinstance(listofreplacements, list):
        listofreplacements = [listofreplacements]

    for r in listofreplacements:
        if isinstance(r, tuple):
            if count:
                thestring = thestring.replace(r[0], r[1], count)
            else:
                while thestring.find(r[0]) >= 0:
                    thestring = thestring.replace(r[0], r[1])

        else:
            if count:
                thestring = thestring.replace(r, "", count)
            else:
                while thestring.find(r) >= 0:
                    thestring = thestring.replace(r, "")

    return thestring.strip()


def get_file_size(filename=None, fpi=None):
    """
    @type filename: str, None
    @type fpi: FileIO, file, None
    """
    if filename:
        f = open(filename)
        f.seek(0, os.SEEK_END)
        return f.tell()
    elif fpi:
        fpi.seek(0)
        fpi.seek(0, os.SEEK_END)
        return fpi.tell()
    else:
        raise Exception("get_file_size: no input")


def make_short_id(amount, short_ids, start_size=3):
    """
    @type amount: int
    @type short_ids: list
    @type start_size: int
    """
    size = start_size
    tries = 0
    new_short_ids = []
    vowels = get_vowels_lower()

    while len(new_short_ids) < amount:
        word = generate_random_string(size, letters=vowels)

        if word not in short_ids:
            size = start_size
            new_short_ids.append(word)
        else:
            tries += 1

        if tries > 10:
            size += 1

    return new_short_ids


def generate_random_string(size, letters=None):
    """
    @type size: int
    @type letters: tuple, None
    """
    cnt = 0

    if not letters:
        letters = get_alphabet()
    strl = []
    end = len(letters) - 1

    while cnt < size:
        i = random.randint(0, end)
        strl.append(letters[i])
        cnt += 1

    return "".join(strl)


def get_path(depth, minl, maxl, letters):
    """
    @type depth: int
    @type minl: int
    @type maxl: int
    @type letters: tuple
    """
    path = "/"

    for i in range(0, depth):
        path = os.path.join(path, generate_random_string(random.randint(minl, maxl), letters).strip())

    return path


def get_test_paths(number, depth, minl, maxl, letters=None):
    """
    @type number: int
    @type depth: int
    @param minl: minum lenght of path component
    @type minl: int
    @param maxl: minum lenght of path component
    @type maxl: int
    @type letters: tuple, None
    """
    paths = set()
    cnt = 0
    current_len = 0
    hangcnt = 0

    if not letters:
        letters = get_alphabet()

    while True:
        paths.add(get_path(depth, minl, maxl, letters))
        cnt += 1
        prevlen = current_len
        current_len = len(paths)

        if prevlen == current_len:
            hangcnt += 1

            if hangcnt > 100000:
                break

        if current_len >= number:
            break
    paths = sorted(paths, key=lambda x: len(x.split("/")))
    paths = sorted(paths, key=lambda x: len(x))
    return paths


def ireplace(old, new, text):
    """
    @type old: str
    @type new: str
    @type text: str
    """
    text_lower = text.lower()

    if old.lower() not in text_lower:
        return text

    index_l = text_lower.index(old.lower())
    return text[:index_l] + new + text[index_l + len(old):]


def start_profile():
    """
    start_profile
    @rtype: Profile
    """
    from cProfile import Profile
    pr = Profile()
    pr.enable()
    return pr


def event_emit(f):
    """
    @type f: str
    """
    print "crypto_data.py:354", f


def end_profile(pr, items=10, printstats=True):
    """
    @type pr: Profile
    @type items: int
    @type printstats: bool
    """
    from pstats import Stats
    p = Stats(pr)
    p.strip_dirs()
    event_emit("foo")
    print "crypto_data.py:367", "hello"
    if printstats:
        print "crypto_data.py:369"
        print "crypto_data.py:370", "total time"
        p.print_stats(items)
        print "crypto_data.py:372", "cumulative time"
        p.sort_stats('cumtime')
        p.print_stats(items)


def format_and_print_large_string(largestring):
    """
    @type largestring: str
    """
    tl = list(largestring)
    tl.reverse()
    s = ""

    while tl:
        for i in range(0, 200):
            if tl:
                c = tl.pop()

                if c:
                    s += c

        s += "\\\n"
    print "crypto_data.py:394", s


def slugify_unicode(value):
    """
    @type value: str
    """
    value = value.lower().replace(" ", "-").replace("/", "__").replace("\\", "")
    slug = ""
    safechars = list(get_safe_alphabet())

    #noinspection PyArgumentEqualDefault
    value = value.decode("utf-8")

    for c in value:
        #d = {1: c}

        if c in safechars:
            slug += c
        else:
            c64 = base64.encodestring(c).strip().rstrip("=")
            #print "crypto_data.py:258", value, d, c, c64
            slug += c64

    return slug.lower()


class FakeQueue(object):
    """
    FakeQueue
    """

    def __init__(self):
        """
        __init__
        """
        self.queuelist = []

    def qsize(self):
        """
        qsize
        """
        return len(self.queuelist)

    def put(self, item):
        """
        @type item: str
        """
        self.queuelist.append(item)

    def get(self):
        """
        get
        """
        if self.qsize() == 0:
            return None

        return self.queuelist.pop(0)


def return_proc_id_test(arg):
    """
    @type arg: str
    """
    return {"arg": arg,
            "pid": os.getpid()}


__cpu_count = None


def get_cpu_count():
    """
    get_cpu_count
    """
    global __cpu_count
    if __cpu_count is not None:
        return __cpu_count
    num_procs = 8
    try:
        num_procs = multiprocessing.cpu_count()
        __cpu_count = num_procs
    except Exception, e:
        console("get_cpu_count", str(e), "defaulting to 8", warning=True)

    return num_procs


class SMPException(Exception):
    """
    SMPException
    """
    pass


def smp_apply(method, items, progress_callback=None, progress_callback_param=None, dummy_pool=False, listener=None, listener_param=None, num_procs_param=None, use_dummy_thread_pool=False, no_smp_from=None):
    """
    @type method: function
    @type items: list, tuple
    @type progress_callback: function
    @type progress_callback_param: list, dict, int, str, unicode, tuple
    @type dummy_pool: bool
    @type listener: function
    @type listener_param: list, tuple
    @type num_procs_param: int
    @type use_dummy_thread_pool: bool
    @type no_smp_from: None, list
    @param no_smp_from: list of strings of files or dirs which are checked against the stack for occurrences, for example in a gevent monkeypatched setup
    @type no_smp_from:
    """
    # this is a hack
    if not no_smp_from:
        no_smp_from = ["www_cryptobox_nl"]
    else:
        no_smp_from.append("www_cryptobox_nl")

    if use_dummy_thread_pool:
        console_warning("smp_apply: use_dummy_thread_pool on")
        results = []
        cnt = 0
        maxi = len(items)
        fq = None

        if listener:
            fq = FakeQueue()

        for param in items:
            if progress_callback:
                perc = (float(cnt) / maxi) * 100
                progress_callback(perc)

            if isinstance(param, tuple):
                param2 = []

                for i in param:
                    param2.append(i)
                param = param2
            else:
                param = [param]

            if fq:
                param.append(fq)
            try:
                results.append(apply(method, param))
            except:
                raise

            cnt += 1

        if fq:
            fq.put("kill")

            if listener_param:
                listener_param = list(listener_param)
                listener_param.append(fq)
            else:
                listener_param = (fq,)
            # equivalent to watcher
            results.append({"retval_listener": apply(listener, listener_param)})

        return results

    last_update = [time.time()]
    results_cnt = [0]

    def progress_callback_wrapper(result_func):
        """
        progress_callback
        @type result_func: object
        """
        if progress_callback:
            now = time.time()
            results_cnt[0] += 1
            try:
                current_percentage = float(results_cnt[0]) / (float(len(items)) / 100)
            except ZeroDivisionError:
                current_percentage = 0

            if results_cnt[0] == 1 and current_percentage == 100:
                pass
            else:
                if now - last_update[0] > 0.1:
                    if current_percentage > 100:
                        current_percentage = 100

                    if progress_callback_param is not None:
                        progress_callback(current_percentage, progress_callback_param)
                    else:
                        progress_callback(current_percentage)
                    last_update[0] = now

        return result_func

    if num_procs_param:
        num_procs = num_procs_param
    else:
        num_procs = get_cpu_count()

    if listener is not None:
        num_procs += 1

    if num_procs > len(items):
        if len(items) != 0:
            num_procs = len(items)

    manager = None

    if dummy_pool:
        pool = multiprocessing.dummy.Pool(processes=num_procs)
    else:
        if num_procs > get_cpu_count() + 1:
            num_procs = get_cpu_count() + 1

        pool = multiprocessing.Pool(processes=num_procs)

        if no_smp_from:
            for astr in no_smp_from:
                if fpath_in_stack(astr):
                    console("real smp_apply", str(astr), warning=True, line_num_only=5)
                    #raise SMPException(warning)

    if listener:
        manager = multiprocessing.Manager()
    calculation_result = []

    if listener and manager:
        if dummy_pool:
            raise Exception("dummy pools don't work with listeners")

        queue = manager.Queue()
    else:
        queue = None
    watcher = None

    if listener:
        if listener_param:
            listener_param = list(listener_param)
            listener_param.append(queue)
        else:
            listener_param = (queue,)

        watcher = pool.apply_async(listener, tuple(listener_param))

    for item in items:
        base_params_list = []

        if isinstance(item, tuple):
            for i in item:
                if hasattr(i, "seek"):
                    i.seek(0)
                    data = i.read()
                    i.close()
                    base_params_list.append(data)
                else:
                    base_params_list.append(i)

        elif isinstance(item, file):
            item.seek(0)
            base_params_list.append(item.read())
        else:
            base_params_list.append(item)

        if queue:
            base_params_list.append(queue)

        params = tuple(base_params_list)
        result = pool.apply_async(method, params, callback=progress_callback_wrapper)
        calculation_result.append(result)

    [result.wait() for result in calculation_result]

    if queue:
        queue.put("kill")
    retval_listener = None

    if watcher:
        retval_listener = watcher.get()

    pool.close()
    pool.join()

    if progress_callback is not None:
        if isinstance(progress_callback, types.FunctionType):
            if progress_callback_param is not None:
                if progress_callback_wrapper:
                    progress_callback(100, progress_callback_param)
            else:
                if progress_callback_wrapper:
                    progress_callback(100)

    results = [x.get() for x in calculation_result]

    if watcher:
        if retval_listener:
            results.append({"retval_listener": retval_listener})

    return results


def run_unit_test(class_name, methodname, myglobals):
    """
    @type class_name: str
    @type methodname: str, None
    @type myglobals: dict
    """
    import unittest
    suite = unittest.TestSuite()
    cls = myglobals[class_name]

    if methodname:
        suite.addTest(cls(methodname))
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(myglobals[class_name])

    unittest.TextTestRunner(failfast=True).run(suite)


class DocNotFoundException(Exception):
    """ exception raised if the document cannot be found """
    pass


def shellquote(s):
    """
    @param s: command to transform
    @type s: string, unicode
    @return: safe shell string
    @rtype: string, unicode
    """
    return "'" + s.replace("'", "'\\''") + "'"


def exist(data):
    """
    @type data: str, int, float, None, dict, list
    """
    data = str(data).strip()

    if not data:
        return False

    elif str(data) == "":
        return False

    elif len(str(data)) == 0:
        return False

    elif str(data) == "False":
        return False

    elif str(data) == "false":
        return False

    elif str(data) == "undefined":
        return False

    elif str(data) == "null":
        return False

    elif str(data) == "none":
        return False

    elif str(data) == "None":
        return False
    return True


class VarNotFoundInDict(Exception):
    """
    VarNotFoundInDict
    """
    pass


def assertvar(adict, key):
    """
    @type adict: dict
    @type key: str
    """
    if key not in adict:
        raise VarNotFoundInDict("cannot find " + str(key))

    val = adict[key]

    if val is None:
        raise VarNotFoundInDict(str(key) + " is None")

    elif val is "":
        raise VarNotFoundInDict(str(key) + " is '' ")

    elif not exist(val):
        raise VarNotFoundInDict(str(key) + "  fails exist")


def get_assertvar(adict, key):
    """
    @type adict: dict
    @type key: str
    """
    assertvar(adict, key)
    return adict[key]


class Const(object):
    """
    Const
    """

    class ConstError(TypeError):
        """
        ConstError
        """
        pass

    def __setattr__(self, name, value):
        """
        @type name: str
        @type value: str
        """
        if name in self.__dict__:
            raise self.ConstError, "Can't rebind const(%s)" % name

        self.__dict__[name] = value


def timestamp_to_string_gmt(ts, short=False):
    """
    @type ts: float
    @type short: bool
    """
    monthname = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    year, month, day, hh, mm, ss, x, y, z = time.localtime(ts)

    if short:
        year -= 2000
        s = "%d-%d-%d %02d:%02d:%02d" % (day, month, year, hh, mm, ss)
    else:
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (day, monthname[month], year, hh, mm, ss)

    return s


def gibberish(wordcount, vowels='aeiou'):
    """
    @type wordcount: int
    @type vowels: str
    """
    initial_consonants = (set(string.ascii_lowercase) - set('aeiou') - set('qxc') | {'bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 'gr', 'pl', 'pr', 'sk', 'sl', 'sm', 'sn', 'sp', 'st', 'str', 'sw', 'tr'})
    final_consonants = (set(string.ascii_lowercase) - set('aeiou') - set('qxcsj') | {'ct', 'ft', 'mp', 'nd', 'ng', 'nk', 'nt', 'pt', 'sk', 'sp', 'ss', 'st'})
    # each syllable is consonant-vowel-consonant "pronounceable"
    syllables = map(''.join, itertools.product(initial_consonants, vowels, final_consonants))
    # you could throw in number combinations, maybe capitalized versions...
    return random.sample(syllables, wordcount)


def makeword(size, vowels='aeiou'):
    """
    @type size: int
    @type vowels: str
    """
    word = gibberish(1)[0]

    while len(word) < size:
        word += gibberish(1, vowels)[0]

    return word[0:size]


def log_date_time_string():
    """
    log_date_time_string
    @return: @rtype:
    """
    ts = "[" + timestamp_to_string_gmt(time.time()) + "]"
    return ts


def fpath_in_stack(fpath):
    """
    @type fpath: str
    """
    stack = cStringIO.StringIO()
    traceback.print_stack(file=stack)
    stack.seek(0)
    stack = stack.read()
    stack = stack.split("\n")
    stack.reverse()

    for i in stack:
        if i.strip().startswith("File"):
            if fpath.lower() in str(i).lower():
                return True

    return False


def stack_trace(line_num_only=0, ret_list=False):
    """
    @param line_num_only:
    @type line_num_only:
    @type ret_list: bool
    @return: @rtype:
    """
    stack = cStringIO.StringIO()
    traceback.print_stack(file=stack)
    stack.seek(0)
    stack = stack.read()

    if ret_list and (line_num_only > 0):
        raise Exception("ret_list or line_num_only both true")

    stackl = []
    stack = stack.split("\n")
    stack.reverse()
    cnt = 0

    for i in stack:
        stackl.append(i)

        if line_num_only > 0:
            if "line" in i and "File" in i:
                if cnt > line_num_only - 1:
                    for j in i.split("line"):
                        for k in j.split(","):
                            #noinspection PyBroadException
                            try:
                                ln = int(k)
                                fs = i.replace('"', "").split(",")[0].split(os.sep)
                                return str("/".join(fs[len(fs) - 2:])) + ":" + str(ln)
                            except:
                                pass

                cnt += 1

    if line_num_only > 0:
        return str("?")

    if ret_list:
        return stackl

    return "\n".join(stackl)


def cron_job_based_check(methodname, exceptions):
    """
    raises an exception if not run from crypto_taskworker.py
    @type methodname: str, unicode
    @type exceptions: list
    """
    stack = stack_trace(ret_list=True)
    stack.reverse()

    if len(stack) < 1:
        raise Exception("cronjob check: could not fetch stack")

    if "crypto_taskworker.py" not in stack[0]:
        no_exceptions = True

        for name in exceptions:
            for i in stack:
                if name in i:
                    no_exceptions = False

        if no_exceptions:
            console_warning(methodname, "called from")

            for i in stack:
                console(i)
            raise Exception("cronjob check: method [" + str(methodname) + "] should be run serialized from the cronjob")


def consoledict(*args):
    """
    @param args:
    @type args:
    @return: @rtype:
    """
    import sys
    dbs = "\033[92m" + log_date_time_string() + "\033[96m "
    dbs += stack_trace(line_num_only=True)

    for s in args:
        if s:
            if isinstance(s, dict):
                dbs += "--- dict ---\n"

                for i in s:
                    dbs += " " + str(i) + " : " + str(s[i]) + "\n"
                dbs += "------------\n"
            else:
                dbs += " " + str(s)

    dbs += "\n\033[0m"
    sys.stdout.write(dbs)
    return


def strcmp(s1, s2):
    """
    @type s1: str or unicode
    @type s2: str or unicode
    @return: @rtype: bool
    """
    #noinspection PyArgumentEqualDefault
    s1 = s1.encode("utf-8")

    #noinspection PyArgumentEqualDefault
    s2 = s2.encode("utf-8")

    if not s1 or not s2:
        return False

    s1 = s1.strip()
    s2 = s2.strip()
    equal = s1 == s2
    return equal


g_start_time = time.time()
CONSOLEHOSTNAME = None


#noinspection PyPep8Naming
def console(*args, **kwargs):
    """
    @param args:
    @type args:
    @param kwargs
    @type kwargs:
    """
    global GLOBAL_HOSTNAME
    #if "lycia" not in GLOBAL_HOSTNAME:
    #    return
    global g_start_time
    import sys
    runtime = "%0.2f" % float(time.time() - g_start_time)
    dbs = "\033[92m" + str(runtime) + "\033[96m"
    toggle = True
    arguments = list(args)

    def sanitize(santize_string):
        """
        @param santize_string:
        @type santize_string:
        @return: @rtype:
        """
        santize_string = str(santize_string)
        santize_string = santize_string.replace("", "")
        return santize_string

    arguments = [sanitize(x) for x in arguments if x is not None]
    line_num_only = 2
    print_stack = False
    warningmsg = False

    if "print_stack" in kwargs:
        print_stack = kwargs["print_stack"]

    if "stack" in kwargs:
        line_num_only += kwargs["stack"]

    if "line_num_only" in kwargs:
        line_num_only = kwargs["line_num_only"]

    if "warning" in kwargs:
        warningmsg = kwargs["warning"]

    if print_stack:
        line_num_counter = 2
        trace = stack_trace(line_num_only=line_num_counter)
        first = True

        while trace != "?":
            if not first:
                dbs += " " * len(runtime)
            dbs += " | " + trace.strip() + "\n"
            trace = stack_trace(line_num_only=line_num_counter)
            line_num_counter += 1
            first = False
        dbs += " " * len(runtime)
    else:
        if line_num_only >= 0:
            arguments.insert(0, sanitize(stack_trace(line_num_only=line_num_only)))

    for s in arguments:
        if toggle:
            dbs += "\033[96m"
        else:
            if warningmsg:
                dbs += "\033[91m"
            else:
                dbs += "\033[92m"

        toggle = not toggle
        dbs += " |"

        if s is not None:
            if s == arguments[len(arguments) - 1]:
                dbs += " " + str(s)[:160].replace("\n", "").strip()
            else:
                dbs += " " + str(s)[:160].replace("\n", "").lstrip()
                #if len(str(s)) < 10:
                #    dbs += " " * (20 - len(str(s).replace("\033[91m", "")))

    dbs += "\n\033[0m"

    if "ret_str" in kwargs:
        if kwargs["ret_str"] is True:
            return dbs

    sys.stdout.write(dbs)
    return


def console_new_line(num=1):
    """
    @type num: int
    """
    global GLOBAL_HOSTNAME
    if "lycia" not in GLOBAL_HOSTNAME:
        return

    for i in range(0, num):
        sys.stdout.write("\n")

    sys.stdout.flush()


#noinspection PyPep8Naming
def console_warning(*args, **kwargs):
    """
    @param args
    @type args:
    @param kwargs
    @type kwargs:
    """
    if "print_stack" in kwargs:
        print_stack = kwargs["print_stack"]
    else:
        print_stack = False
    dbs = ""

    for s in args:
        if s:
            if isinstance(s, dict):
                for i in s:
                    dbs = " " + str(i) + " : " + str(s[i]) + "\n"
                    console(dbs, print_stack=print_stack, warning=True, line_num_only=3)
            else:
                dbs += " " + str(s)

    dbs += " in " + stack_trace(line_num_only=3)
    console(dbs, print_stack=print_stack, warning=True, line_num_only=3)


class Events(object):
    """
    Events
    """

    def reset(self):
        """
        reset
        """
        self.done = "07d4fb33602048ac861e2c6eeec7d0b9"
        self.results = []
        self.logged_events = []
        self.show_events = False
        self.start_timer = time.time()
        self.report_measurements_called = 0

    def __init__(self, show_events=False):
        """
        @type show_events: bool
        """
        self.done = None
        self.results = None
        self.logged_events = None
        self.show_events = None
        self.start_timer = None
        self.report_measurements_called = None
        self.reset()
        self.show_events = show_events

    def add_event(self, event):
        """
        @type event: dict
        """
        if event is None:
            return

        self.logged_events.append(event)

    def event(self, *args, **kwargs):
        """
        @param args:
        @type args:
        @param kwargs:
        @type kwargs:
        """
        name = " ".join([str(x) for x in args])
        to_console = False
        line_num_only = 3

        if "to_console" in kwargs:
            to_console = kwargs["to_console"]

        if "line_num_only" in kwargs:
            line_num_only = kwargs["line_num_only"]

        if to_console or self.show_events:
            console("event", name, line_num_only=line_num_only + 1)

        now = time.time()
        event = {"time": now,
                 "name": name,
                 "line": stack_trace(line_num_only=line_num_only).replace("File ", "").strip(),
                 "uuid": get_guid()}

        self.add_event(event)

    def get_events(self):
        """
        get_events
        """
        self.event(self.done)
        self.logged_events = sorted(self.logged_events, key=lambda k: k['time'])
        return self.logged_events

    @staticmethod
    def new_result_item(result, results):
        """
        @type result: dict
        @type results: list
        """
        add = True

        for current_result in results:
            if current_result["uuid"] == result["uuid"]:
                add = False

        return add

    def add_result(self, result):
        """
        @type result: dict
        """
        add = self.new_result_item(result, self.results)

        if add:
            self.results.append(result)

    def extend(self, events):
        """
        @type events: dict, list
        """
        new_events = []
        event_lists = []

        for event in events:
            if isinstance(event, list):
                event_lists.append(event)
            else:
                new_events.append(event)

        for event_list in event_lists:
            cnt = 0

            for event in event_list:
                result = event
                cnt += 1

                if cnt < len(event_list):
                    result["nextevent"] = event_list[cnt]
                    self.add_result(result)

        for event in new_events:
            self.add_event(event)

    @staticmethod
    def print_result(result, fv_result_duration, total, items=None):
        """
        @type result: dict
        @type fv_result_duration: float
        @type total: str
        @type items: int, None
        """
        duration = "%0.2f" % float(fv_result_duration)
        totals = "%0.2f" % total

        if items is not None:
            if items > 1:
                if items >= 200:
                    items = "\033[91m" + str(items) + " calls"
                else:
                    items = str(items) + " calls"
            else:
                items = None

        if fv_result_duration > 0.35:
            console(result["line"], result["name"], " " + str("\033[91m* " + str(duration)) + " *", totals, items, line_num_only=-1)
        else:
            console(result["line"], result["name"], str(duration), totals, items, line_num_only=-1)

    @staticmethod
    def get_event_index_by_name(name, events):
        """
        @type name: str
        @type events: list
        """
        index = 0

        for event in events:
            if event["name"] == name:
                return index
            index += 1

        return -1

    def measurement_header(self, threshold_reached):
        """
        @type threshold_reached: bool
        """
        if threshold_reached:
            console("==", str(len(self.logged_events) - self.report_measurements_called) + " event measurements", "==", line_num_only=4)

    def report_measurements(self, group=True, show_threshhold=0.0, show_total=True, show_all_if_threshold=True):
        """
        @type group: bool
        @type show_threshhold: float
        @type show_total: bool
        @type show_all_if_threshold: bool
        """
        self.report_measurements_called += 1
        self.event("done")
        total = 0.0
        cnt = 0
        seen_results = {}

        for current_result in self.results:
            seen_results[current_result["uuid"]] = True

        for event in self.logged_events:
            cnt += 1

            if event is None:
                pass

            if cnt < len(self.logged_events):
                event["nextevent"] = self.logged_events[cnt]

                if event["uuid"] in seen_results:
                    seen_results[event["uuid"]] = True
                else:
                    self.results.append(event)

        self.results = sorted(self.results, key=lambda k: k['time'])
        threshold_reached = False

        if group:
            grouped_results = []
            grouped_events_cnt = {}

            for result in self.results:
                if result["name"] != self.done:
                    result["duration"] = result["nextevent"]["time"] - result["time"]
                    index = self.get_event_index_by_name(result["name"], grouped_results)

                    if index >= 0:
                        grouped_results[index]["duration"] += result["duration"]
                        grouped_events_cnt[result["name"]] += 1
                    else:
                        grouped_results.append(result)
                        grouped_events_cnt[result["name"]] = 1

            for result in grouped_results:
                duration = result["duration"]
                fv_result_duration = float(duration)

                if fv_result_duration >= show_threshhold:
                    threshold_reached = True

                    if show_all_if_threshold:
                        show_threshhold = 0

            if show_total:
                self.measurement_header(threshold_reached)

            for result in grouped_results:
                duration = result["duration"]
                total += float(duration)
                fv_result_duration = float(duration)

                if fv_result_duration >= show_threshhold:
                    self.print_result(result, fv_result_duration, total, grouped_events_cnt[result["name"]])

        else:
            for result in self.results:
                if result["name"] != self.done:
                    result["duration"] = result["nextevent"]["time"] - result["time"]
                    duration = result["duration"]
                    fv_result_duration = float(duration)

                    if fv_result_duration >= show_threshhold:
                        threshold_reached = True

                        if show_all_if_threshold:
                            show_threshhold = 0

            if show_total:
                self.measurement_header(threshold_reached)

            for result in self.results:
                if result["name"] != self.done:
                    result["duration"] = result["nextevent"]["time"] - result["time"]
                    duration = result["duration"]
                    total += float(duration)
                    fv_result_duration = float(duration)

                    if fv_result_duration >= show_threshhold:
                        self.print_result(result, fv_result_duration, total)

        totals = "\033[93m%0.1f" % total
        total_runtime = float(time.time() - self.start_timer)

        if total_runtime >= show_threshhold:
            total_runtime = "\033[93m%0.1f" % total_runtime

            if show_total and threshold_reached:
                console("total compute time", totals, line_num_only=4)
                console("total runtime", total_runtime, line_num_only=4)


def resetterminal():
    """
    resetterminal():
    """
    import sys
    sys.stdout.write('\033[0m')
    return


def handle_ex(exc, again=True, give_string=False):
    """
    @type exc: Exception
    @type again: bool
    @type give_string: bool
    """
    #noinspection PyUnresolvedReferences
    import sys
    import traceback
    exc_type, exc_value, exc_traceback = sys.exc_info()
    error_msg = "\n\033[95m" + log_date_time_string() + " ---------------------------\n"
    error_msg += "\033[95m" + log_date_time_string() + "   !!! EXCEPTION !!!\n"
    error_msg += "\033[95m" + log_date_time_string() + " ---------------------------\n"
    items = traceback.extract_tb(exc_traceback)
    #items.reverse()
    leni = 0
    error_msg += "\033[93m" + log_date_time_string() + " " + str(exc_type) + "\n"
    error_msg += "\033[93m" + log_date_time_string() + " " + str(exc_value) + "\n"
    error_msg += "\033[95m" + log_date_time_string() + " ---------------------------\n"
    error_msg += "\033[93m"
    try:
        linenumsize = 0

        for line in items:
            fnamesplit = str(line[0]).split("/")
            fname = "/".join(fnamesplit[len(fnamesplit) - 2:])
            ls = len(fname + ":" + str(line[1]))

            if ls > linenumsize:
                linenumsize = ls

        items.reverse()

        for line in items:
            leni += 1
            tabs = leni * "  "
            fnamesplit = str(line[0]).split("/")
            fname = "/".join(fnamesplit[len(fnamesplit) - 2:])
            fname_number = fname + ":" + str(line[1])
            fname_number += (" " * (linenumsize - len(fname_number)))
            val = ""

            if line[3]:
                val = line[3]
            error_msg += fname_number + " | " + tabs + val + "\n"
    except Exception, e:
        print "\033[93m" + log_date_time_string(), "crypto_data.py:1482", e, '\033[m'
        print "\033[93m" + log_date_time_string(), "crypto_data.py:1483", exc, '\033[m'
    error_msg += "\033[95m" + log_date_time_string() + " ---------------------------\n"

    if give_string:
        return error_msg.replace("\033[95m", "")
    else:
        import sys
        sys.stdout.write(str(error_msg) + '\033[0m')

    if again:
        raise exc

    return "\033[93m" + error_msg


class TaskException(Exception):
    """
    TaskException
    """
    pass


def handle_task_exception(exc):
    """
    @param exc:
    @type exc:
    @raise TaskException:
    """
    raise TaskException(handle_ex(exc, give_string=True))


def error(msg):
    """
    logging error
    @param msg: the error message
    @type msg: string
    """
    logging.error(msg)


def report(msg):
    """
    info log
    @param msg: the error message
    @type msg: string
    """
    logging.warning(msg)


def get_b64_simple():
    """
    get_b64_simple
    """
    return "data:b64:simple,"


def b64_encode_simple(s):
    """
    @type s: str
    """
    if not isinstance(s, str) and not isinstance(s, unicode):
        return s

    b64simple = get_b64_simple()

    if s.find(b64simple) != -1:
        return s

    s = base64.encodestring(s)
    s = b64simple + s
    return s


def b64_decode_simple(s):
    """
    @type s: str
    """
    if not isinstance(s, str) and not isinstance(s, unicode):
        return s

    b64simple = get_b64_simple()

    if s.find(b64simple) != 0:
        return s

    s = s.replace(b64simple, "")
    s = base64.decodestring(s)
    return s


def get_b64safe():
    """
    get_b64safe
    @return: @rtype:
    """
    return "data:b64:safe,"


def key_ascii(s):
    """
    @type s: str
    """
    if not isinstance(s, str) and not isinstance(s, unicode):
        return s
    s2 = ""

    for c in s:
        if c in "_012345678909ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
            s2 += c

    return s2.encode("ascii")


def b64_decode_safe(s):
    """
    @type s: str
    """
    if not isinstance(s, str) and not isinstance(s, unicode):
        return s

    b64safe = get_b64safe()

    if s.find(b64safe) != 0:
        return s

    s = s.replace(b64safe, "")
    s = base64.decodestring(s.replace("-", "="))
    s = urllib.unquote(s)
    return s


def b64_encode_safe(s):
    """
    @type s: str
    """
    if not isinstance(s, str) and not isinstance(s, unicode):
        return s

    b64safe = get_b64safe()

    if s.find(b64safe) != -1:
        return s
    try:
        s = urllib.quote(s, safe='~()*!.\'')
    except KeyError:
        console("b64_encode_safe: using key_ascii", s, warning=True, line_num_only=4)
        s = key_ascii(s)

    s = base64.encodestring(s).replace("=", "-").replace("\n", "")
    s = b64safe + s
    return s


def b64_object_safe(d):
    """
    @type d: str
    """
    if isinstance(d, dict):
        for k in d:
            d[k] = b64_object_safe(d[k])

        return d

    if isinstance(d, list):
        cnt = 0

        for k in d:
            d[cnt] = b64_object_safe(k)
            cnt += 1

        return d

    d = b64_decode_safe(d)
    return d


def object_b64_safe(d):
    """
    @type d: dict, list, tuple, object, int, float, str, unicode
    """
    if isinstance(d, dict):
        for k in d:
            d[k] = object_b64_safe(d[k])

        return d

    if isinstance(d, list):
        cnt = 0

        for k in d:
            d[cnt] = object_b64_safe(k)
            cnt += 1

        return d

    d = b64_encode_safe(d)
    return d


def get_b64pstyle():
    """
    get_b64pstyle
    """
    return "data:b64:pickle,"


def object_to_pickled_base64(obj):
    """
    @type obj: dict, list, tuple, object, int, float, str, unicode
    """
    b64pstyle = get_b64pstyle()

    if isinstance(obj, str):
        if b64pstyle in obj:
            return obj

    pickle_string = cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL)
    return b64pstyle + base64.b64encode(pickle_string)


def is_pickled_base64_object(p64):
    """
    @type p64: str
    """
    return get_b64pstyle() in p64


def pickled_base64_to_object(p64):
    """
    base64 pickled string to python object
    @param p64:b64 encoded object
    @type p64:str
    @return:a python object
    """
    if isinstance(p64, int):
        return p64

    if isinstance(p64, list):
        return p64

    if isinstance(p64, dict):
        return p64

    if isinstance(p64, bool):
        return p64

    if isinstance(p64, float):
        return p64

    b64pstyle = get_b64pstyle()

    if p64:
        if str(p64).startswith(b64pstyle):
            p64 = p64.replace(b64pstyle, "")

            if p64.strip() == "":
                return ""

            return cPickle.loads(base64.b64decode(p64))
    return p64


def save_object_p64_dict_to_dict(object_dict_str):
    """
    @type object_dict_str: unicode, str
    @rtype: dict
    """
    adict = pickled_base64_to_object(object_dict_str)

    for key in adict.keys():
        adict[key] = pickled_base64_to_object(adict[key])

    return adict


def get_keys_slap(item, host, port):
    """
    @type item: str
    @type host: str
    @type port: int
    """
    keys = []
    t = telnetlib.Telnet(host, port)
    parts = item.split(':')

    if len(parts) >= 3:
        slab = parts[1]
        t.write('stats cachedump {} 200000 ITEM views.decorators.cache.cache_header..cc7d9 [6 b; 1256056128 s] END\n'.format(slab))
        cachelines = t.read_until('END').split('\r\n')

        for line in cachelines:
            parts = line.split(' ')

            if len(parts) >= 3:
                keys.append(parts[1])

    t.close()
    return keys


class RedisException(Exception):
    """
    RedisException
    """
    pass


spinlock_memcache_thread_lock = threading.Lock()


redis_pool = redis.ConnectionPool(host='localhost', port=6379, db=0)


class RedisServer(object):
    """
    RedisServer
    """

    def __init__(self, db_key, verbose=False):
        """
        @type db_key: str
        @type verbose: bool
        """
        global redis_pool
        self.pool = redis_pool
        self.db_key = db_key
        self._verbose = verbose
        self.rediscon = redis.Redis(connection_pool=self.pool)

    @property
    def verbose(self):
        """
        verbose
        """
        return self._verbose

    def verbose_on(self):
        """
        verbose
        """
        self._verbose = True

    def verbose_off(self):
        """
        verbose_off
        """
        self._verbose = False

    def get_stats(self):
        """
        get_stats
        """
        return self.rediscon.info()

    def flush_all(self):
        """
        flush all keys in the redis servers
        """
        self.rediscon.flushall()

        for i in range(0, 5):
            try:
                self.rediscon.set("test", "ok")
                self.rediscon.delete("test")
                return
            except ResponseError:
                console("flush_all: sleeping")
                time.sleep(float("0." + str(i)))

    def delete_prefix(self, prefix):
        """
        @type prefix: str
        """
        prefix = self.make_safe_key(prefix)
        delete_keys = self.rediscon.keys(prefix + "*")

        for key in delete_keys:
            self.delete(key)

        return delete_keys

    def flush_namespace(self):
        """
        flush_namespace
        """
        delete_keys = self.rediscon.keys(self.db_key + "*")

        for key in delete_keys:
            self.delete(key)

        return delete_keys

    def get(self, key, raw=False):
        """
        @type key: str
        @type raw : bool
        """
        if not key:
            return None

        key = self.make_safe_key(key)
        # console("get", key)
        val = self.rediscon.get(str(key))

        if val is None:
            return None
        else:
            if raw:
                return val
            else:
                try:
                    return cPickle.loads(val)
                except cPickle.UnpicklingError:
                    console_warning("unpickling error: key was ->", key)
                    return val

    def set(self, key, data, time_to_live=None, raw=False):
        """
        @type key: str
        @type data: object
        @type time_to_live: str, None
        @type raw: bool
        """
        if time_to_live is None:
            time_to_live = 0

        key = self.make_safe_key(key)

        if not raw:
            data = cPickle.dumps(data)
        try:
            return self.rediscon.set(str(key), data, ex=time_to_live)
        except ResponseError, ex:
            console_warning("set:", str(ex))
            self.flush_all()

    def make_safe_key(self, key):
        """
        @type key: str
        """
        if not key:
            raise RedisException("key is required")

        if not key.startswith(self.db_key + "_"):
            key = self.db_key + "_" + key

        safe_version = key.replace(" ", "_")

        if not strcmp(safe_version, key):
            raise RedisException("spaces are not allowed, use " + safe_version.replace(self.db_key + "_", "") + " instead of " + key.replace(self.db_key + "_", ""))

        return key

    def delete(self, key):
        """
        @param key:
        @type key:
        """
        key = self.make_safe_key(key)

        if self._verbose:
            console("delete", key, line_num_only=4)

        return self.rediscon.delete(str(key))

    def event_subscribe(self, event, callback, *args):
        """
        @type event: str
        @type callback: function
        """
        event = self.make_safe_key(event)

        def subscriber_wrapper(wevent, wcallback, args):
            """
            @type wevent: str
            @type wcallback: function
            @type args: str
            """
            redisevents = self.rediscon.pubsub()
            redisevents.psubscribe(wevent)
            try:
                for cevent in redisevents.listen():
                    if not cevent["type"] == "psubscribe":
                        if self._verbose:
                            if not strcmp(wcallback.__name__, "wrapped_callback"):
                                console("event received", cevent["channel"], wcallback.__name__)

                        data = cPickle.loads(cevent["data"])

                        if data is None:
                            result = wcallback()
                        else:
                            if len(args) > 0:
                                result = wcallback(data, *args)
                            else:
                                result = wcallback(data)

                        if result is None or result is False:
                            if self._verbose:
                                console("unsubscribe:", cevent["channel"])

                            return
                    else:
                        self.event_emit("crypto_data.py:1988", "subscribed_on_event", cevent["channel"])
                        self.set("event_" + str(cevent["channel"]), True)

            except Exception, e:
                console(event, str(e))
                raise

        self.set("event_" + str(event), False)
        events_subscriber = threading.Thread(target=subscriber_wrapper, args=(event, callback, args))
        events_subscriber.setDaemon(True)
        events_subscriber.start()

        while self.get("event_" + str(event)) is False:
            time.sleep(0.1)

        self.delete("event_" + str(event))
        return events_subscriber

    def event_subscribe_wait(self, event, callback=None, wait_time=None):
        """
        @type event: str
        @type callback: function, none
        @type wait_time: int, None
        """
        start = time.time()

        def wrapped_callback(*args):
            """
            @type data: str
            """
            if self._verbose:
                console("event received wait", event)

            if callback:
                if len(args) > 0:
                    callback(*args)
                else:
                    callback()
            # always return False, a wait is a one time block
            return False

        listener = self.event_subscribe(event, wrapped_callback)

        if wait_time is None:
            listener.join()
        else:
            while True:
                runtime = time.time() - start
                timeleft = (wait_time - runtime)

                if not listener.is_alive():
                    return

                if timeleft > 5:
                    time.sleep(1)
                elif timeleft > 2:
                    time.sleep(0.5)
                elif timeleft > 0.2:
                    time.sleep(0.1)
                else:
                    time.sleep(0.05)

                    if self._verbose:
                        console("event_subscribe_wait: timeleft, ", timeleft)

                if timeleft <= -0.05:
                    if self._verbose:
                        raise RedisException("event_subscribe_wait:wait_time exceeded:" + str(timeleft)[:6] + " [" + event + "]")
                    raise RedisException("event_subscribe_wait:wait_time exceeded")

    def event_emit(self, event, data=None):
        """
        @type event: str
        @type data: object
        """
        event = self.make_safe_key(event)

        if self._verbose:
            if data is None:
                console("event_emit", event)
            else:
                console("event_emit", event, str(data)[0:50])

        return self.rediscon.publish(event, cPickle.dumps(data))

    def list_push(self, key, data, raw=False):
        """
        @type key: str
        @type data: object
        @type raw: bool
        """
        key = self.make_safe_key(key)

        if not raw:
            data = cPickle.dumps(data)

        return self.rediscon.lpush(key, data)

    def list_pop(self, key, raw=False):
        """
        @type key: str
        @type raw: bool
        """
        key = self.make_safe_key(key)
        data = self.rediscon.lpop(key)

        if data is None:
            return None

        if raw:
            return data
        else:
            return cPickle.loads(data)

    def list_len(self, key):
        """
        @type key: str
        """
        key = self.make_safe_key(key)
        return self.rediscon.llen(key)

    def list_iter(self, key):
        """
        @type key: str
        """
        key = self.make_safe_key(key)

        def get():
            """
            get
            """
            cnt = self.rediscon.llen(key)
            cnt -= 1
            item = self.rediscon.lindex(key, cnt)

            while cnt >= 0 and item:
                item = cPickle.loads(item)
                yield item
                cnt -= 1
                item = self.rediscon.lindex(key, cnt)

        return iter(get())

    def list_get(self, key):
        """
        @type key: str
        """
        key = self.make_safe_key(key)
        l = self.rediscon.lrange(key, 0, -1)

        if l is not None:
            l = [cPickle.loads(i) for i in l]
            l.reverse()
            return l


class MCDict(dict):
    """
    MCDict
    """

    def __init__(self, name, init_data=None):
        """
        @type name: str
        @type init_data: str, None
        """
        self.rsc = RedisServer(name)
        super(MCDict, self).__init__(self)

        if init_data:
            for k in init_data:
                self[k] = init_data[k]

    def clear(self):
        """
        clear all keys
        """
        for k in self.keys():
            del self[k]

    def get(self, key, default=None):
        """
        @type key: str
        @type default: str, None
        """
        val = super(MCDict, self).get(key, default)

        if val is default:
            val = self.rsc.get(key)

            if val is None:
                val = default

        return val

    def __getitem__(self, key):
        """
        @type key: str
        """
        try:
            val = super(MCDict, self).__getitem__(key)
        except KeyError:
            val = self.rsc.get(key)

            if not val:
                return None
            else:
                super(MCDict, self).__setitem__(key, val)

        return val

    def __delitem__(self, key):
        """
        @type key: str
        """
        self.rsc.delete(key)
        try:
            super(MCDict, self).__delitem__(key)
        except KeyError:
            pass

    def __setitem__(self, key, value):
        """
        @type key: str
        @type value: str
        """
        self.rsc.set(key, value)
        super(MCDict, self).__setitem__(key, value)

    def __contains__(self, key):
        """
        @type key: str, dict
        """
        contains = super(MCDict, self).__contains__(key)

        if not contains:
            contains = self.__getitem__(key)

            if contains is None:
                contains = False
            else:
                contains = True

        return contains


def get_named_temporary_file(auto_delete):
    """
    @type auto_delete: bool
    """
    ntf = tempfile.NamedTemporaryFile(delete=auto_delete)

    if not auto_delete:
        fname = "tempfile_" + str(uuid.uuid4().hex) + ".cba"
        fpath = os.path.join("/tmp", fname)
        logf = open(fpath, "w")
        logf.write(ntf.name)
        logf.write("\n\n")
        logf.write(stack_trace())
        logf.close()

    return ntf


def cleanup_tempfiles(max_age_in_seconds=300):
    """
    @type max_age_in_seconds: int
    """
    for fp in glob.glob("/tmp/tempfile_*.cba"):
        fp = os.path.basename(fp)

        if str(fp).startswith("tempfile_") and str(fp).endswith(".cba"):
            if os.path.exists(os.path.join("/tmp", fp)):
                try:
                    data = open(os.path.join("/tmp", fp)).readline().strip()

                    if os.path.exists(data):
                        file_age = time.time() - os.stat(data).st_mtime

                        if file_age > max_age_in_seconds:
                            if os.path.exists(data):
                                os.remove(data)

                            if os.path.exists(os.path.join("/tmp", fp)):
                                os.remove(os.path.join("/tmp", fp))

                    else:
                        if os.path.exists(os.path.join("/tmp", fp)):
                            os.remove(os.path.join("/tmp", fp))

                except IOError, e:
                    console("cleanup_tempfiles: " + str(e))
                except OSError, e:
                    console("cleanup_tempfiles: " + str(e))


class GCSBucketDoesNotExsist(Exception):
    """
    GCSBucketDoesNotExsist
    """
    pass


def gcs_bucket_headers(bucket_name):
    """
    @type bucket_name: unicode, str, unicode
    """
    header_values = {"x-goog-api-version": "2",
                     "x-goog-project-id": "cryptobox2013"}

    uri = boto.storage_uri(bucket_name, "gs")
    return header_values, uri


def gcs_get_bucket(bucket_name, cloud):
    """
    @type bucket_name: str
    @type cloud: bool
    """
    if not cloud:
        if not os.path.exists("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name):
            raise GCSBucketDoesNotExsist(bucket_name)
        else:
            return bucket_name, "/Users/rabshakeh/workspace/cloudfiles/" + bucket_name
    try:
        header_values, uri = gcs_bucket_headers(bucket_name)
        bucket = uri.get_bucket(headers=header_values, validate=True)
        return bucket, uri
    except GSResponseError:
        raise GCSBucketDoesNotExsist(bucket_name)


def gcs_all_buckets(cloud):
    """
    @type cloud: bool
    """
    if not cloud:
        cloud_path_dummy = "/Users/rabshakeh/workspace/cloudfiles/"
        return [os.path.join(cloud_path_dummy, x) for x in os.listdir(cloud_path_dummy) if os.path.isdir(os.path.join(cloud_path_dummy, x))]

    header_values, uri = gcs_bucket_headers("")
    return uri.get_all_buckets(headers=header_values)


def gcs_get_list_bucket(bucket_name, cloud):
    """
    @type bucket_name: str
    @type cloud: bool
    """
    if not cloud:
        if not os.path.exists("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name):
            raise GCSBucketDoesNotExsist(bucket_name)
        else:
            l = []

            for i in os.listdir("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name):
                l.append(os.path.join("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name, i))

            return l

    items = []
    b = gcs_get_bucket(bucket_name, cloud)[0]

    for i in b.list():
        items.append("gs://" + b.name + "/" + i.name)

    return items


def gcs_get_create_bucket(bucket_name, cloud, loc=Location.DEFAULT):
    """
    @type bucket_name: str
    @type cloud: bool
    @type loc: str
    """
    try:
        if not cloud:
            if not os.path.exists("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name):
                try:
                    mtx = Mutex(bucket_name, "make_local_bucket")
                    try:
                        mtx.acquire_lock()

                        if not os.path.exists("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name):
                            os.makedirs("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name)
                    finally:
                        mtx.release_lock()
                except Exception, e:
                    console("gcs_get_create_bucket", str(e))

            return [os.listdir("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name)]
        else:
            try:
                bucket = gcs_get_bucket(bucket_name, cloud)
                return bucket
            except GCSBucketDoesNotExsist:
                header_values, uri = gcs_bucket_headers(bucket_name)
                try:
                    return uri.create_bucket(headers=header_values, location=loc)
                except Exception, ex:
                    if hasattr(ex, "status"):
                        if int(ex.status) == 409:
                            pass
                        else:
                            raise
                    else:
                        raise

    except Exception, exc:
        handle_ex(exc)


def gcs_delete_bucket(bucket_name, cloud):
    """
    @type bucket_name: str
    @type cloud: bool
    """
    if not cloud:
        p = "/Users/rabshakeh/workspace/cloudfiles/" + bucket_name

        if os.path.exists(p):
            os.rmdir(p)

        return

    uri = boto.storage_uri(bucket_name, "gs")
    bucket = uri.get_bucket()
    try:
        bucket.delete()
        return True
    except GSResponseError, ex:
        if ex.status != 404:
            raise ex

        return False


class GCSGoogleCloudWriteFailure(Exception):
    """
    GCSGoogleCloudWriteFailure
    """
    pass


def gcs_write_to_gcloud(bucket_name, name, fpath, cloud):
    """
    @type bucket_name: str
    @type name: str
    @type fpath: str
    @type cloud: bool
    """
    fp = open(fpath)

    if not cloud:
        gcs_get_create_bucket(bucket_name, cloud)
        foutpath = "/Users/rabshakeh/workspace/cloudfiles/" + bucket_name + "/" + name + ".crap"
        open(foutpath, "w").write(fp.read())
        return

    dst_uri = boto.storage_uri(bucket_name + "/" + name, "gs")
    k = dst_uri.new_key()
    try:
        k.set_contents_from_file(fp)
    except GSResponseError, ex:
        if ex.status == 404:
            gcs_get_create_bucket(bucket_name, cloud)
            fp.seek(0)
            k.set_contents_from_file(fp)
        else:
            raise ex

    k2 = dst_uri.get_key()
    k2 = k2.etag.replace('"', "")

    if not strcmp(k.md5, k2):
        raise GCSGoogleCloudWriteFailure("could not write " + str(name) + " to bucket " + str(bucket_name))


class GCSStorageObjectDoesNotExsist(Exception):
    """
    GCSStorageObjectDoesNotExsist
    """
    pass


def gcs_have_file_in_cloud(bucket_name, name, cloud):
    """
    @type bucket_name: str
    @type name: str
    @type cloud: bool
    """
    if not cloud:
        return os.path.exists("/Users/rabshakeh/workspace/cloudfiles/" + bucket_name + "/" + name + ".crap")
    try:
        dst_uri = boto.storage_uri(bucket_name + "/" + name, "gs")
        k = dst_uri.get_key()

        if k:
            return True
        else:
            return False
    except InvalidUriError:
        return False


def gcs_read_from_cloud_uri(file_uri, cloud):
    """
    @type file_uri: str, unicode
    @type cloud: bool
    """
    if not cloud:
        if os.path.exists(file_uri):
            tfp = get_named_temporary_file(auto_delete=False)
            tfp.write(open(file_uri).read())
            tfp.seek(0)
            return tfp.name
        else:
            raise Exception("file does not exist")
    else:
        dst_uri = boto.storage_uri(file_uri, "gs")
        k = dst_uri.get_key()
        tfp = get_named_temporary_file(auto_delete=False)
        try:
            k.get_file(tfp)
        except:
            os.remove(tfp.name)
            raise

        tfp.seek(0)
        return tfp.name


def gcs_read_from_gcloud(bucket_name, name, cloud):
    """
    @type bucket_name: str
    @type name: str
    @type cloud: bool
    """
    if not cloud:
        file_uri = "/Users/rabshakeh/workspace/cloudfiles/" + bucket_name + "/" + name + ".crap"

        if gcs_have_file_in_cloud(bucket_name, name, cloud):
            try:
                return gcs_read_from_cloud_uri(file_uri, cloud)
            except Exception, ex:
                raise GCSStorageObjectDoesNotExsist(str(ex) + ": " + bucket_name + "/" + name)
        raise GCSStorageObjectDoesNotExsist("not found: " + bucket_name + "/" + name)

    try:
        file_uri = bucket_name + "/" + name
        return gcs_read_from_cloud_uri(file_uri, cloud)
    except InvalidUriError, ex:
        raise GCSStorageObjectDoesNotExsist(str(ex) + ": " + bucket_name + "/" + name)


def gcs_delete_uri_from_gcloud(uri, cloud):
    """
    @type uri: str, unicode
    @type cloud: bool
    """
    if not cloud:
        if os.path.exists(uri):
            os.remove(uri)
    else:
        dst_uri = boto.storage_uri(uri)
        k = dst_uri.get_key()
        k.delete()


def gcs_delete_from_gcloud(bucket_name, name, cloud):
    """
    @type bucket_name: str
    @type name: str
    @type cloud: bool
    """
    if not cloud:
        fpath = "/Users/rabshakeh/workspace/cloudfiles/" + bucket_name + "/" + name + ".crap"
        gcs_delete_uri_from_gcloud(fpath, cloud)
        return

    dst_uri = boto.storage_uri(bucket_name + "/" + name, "gs")
    gcs_delete_uri_from_gcloud(dst_uri.uri, cloud)


def gds_get_namespaces(keys=False):
    """
    @type keys: bool
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    query = req.query
    # Namespace pseudo-kind.
    query.kind.add().name = '__namespace__'
    # Keys-only query.
    query.projection.add().property.name = '__key__'
    resp = datastore.run_query(req)
    namespaces = {}

    for entity_result in resp.batch.entity_result:
        path_element = entity_result.entity.key.path_element[0]

        if path_element.name:
            namespaces[path_element.name] = entity_result.entity.key

    if keys:
        return namespaces
    else:
        return namespaces.keys()


def standard_progress(p=0):
    """
    @type p: int
    """
    sys.stdout.write(" -> " + str(int(p)) + " %\r")
    sys.stdout.flush()


def gds_delete_namespace(serverconfig, prefixes=None, flush_all=True, force_consistency=False, cloud_storage=False):
    """
    @type serverconfig: ServerConfig
    @type prefixes: list
    @type flush_all: bool
    @type force_consistency: bool
    @type cloud_storage: bool
    """
    namespace = serverconfig.get_namespace()
    gcs_delete_bucket(namespace, cloud_storage)

    if flush_all:
        serverconfig.rs_flush_all()
    else:
        serverconfig.rs_flush_prefix("")

    keys = gds_get_scalar_list(namespace, member="keyval")

    while len(keys) > 0:
        keytypes = {}

        for key in keys:
            name = gds_get_key_name(key)
            kind = gds_get_key_kind(key)
            delete = False

            if prefixes is None:
                delete = True
            else:
                for prefix in prefixes:
                    if str(name).startswith(prefix):
                        delete = True

            if delete:
                if kind not in keytypes:
                    keytypes[kind] = []

                keytypes[kind].append(key)

        for k in keytypes:
            keys = [keyid for keyid in keytypes[k]]
            serverconfig.event("deleting", namespace, k, len(keys))

            if len(keys) < 100:
                smp_apply(gds_delete_item_on_key, [(serverconfig.get_namespace(), keyid, None, force_consistency) for keyid in keys], num_procs_param=32, dummy_pool=True)
            else:
                smp_apply(gds_delete_item_on_key, [(serverconfig.get_namespace(), keyid, None, force_consistency) for keyid in keys], num_procs_param=32, progress_callback=standard_progress, dummy_pool=True)

        keys = gds_get_scalar_list(namespace, member="keyval")


def gds_get_ids(serverconfig):
    """
    @type serverconfig: ServerConfig
    """
    namespace = serverconfig.get_namespace()
    keys = gds_get_scalar_list(namespace, member="keyval")
    object_ids = []

    for key in keys:
        object_ids.append(gds_get_key_name(key))

    return object_ids


def gds_commit_transaction():
    """
    gds_commit_transaction
    """
    req = datastore.BeginTransactionRequest()
    resp = datastore.begin_transaction(req)
    tx = resp.transaction
    req = datastore.CommitRequest()
    req.transaction = tx
    return req


def gds_rollback(commit):
    """
    @type commit: datastore.CommitRequest
    """
    datastore.rollback(commit)


def gds_commit(commit):
    """
    @type commit: datastore.CommitRequest
    """
    datastore.commit(commit)


def gds_add_saveobject(namespace, otype, object_id, datadict, indexed_keys=None, commit=None, rsc=None):
    """
    @type namespace: unicode, str
    @type otype: str
    @type object_id: str
    @type datadict: dict
    @type indexed_keys: list
    @type commit: object
    @type rsc: RedisServer(
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.CommitRequest()

    #noinspection PyUnresolvedReferences
    if commit is None:
        #noinspection PyUnresolvedReferences
        req.mode = datastore.CommitRequest.NON_TRANSACTIONAL
    else:
        req = commit

    #noinspection PyUnresolvedReferences
    entity = req.mutation.upsert.add()
    entity.key.partition_id.namespace = namespace
    # this can be used for grouping, in order to have larger transactions
    # ___add_key_path(entity.key, str(otype).lower(), 1, otype, object_id)
    add_key_path(entity.key, otype, object_id)

    if indexed_keys:
        datadict["indexed_keys"] = ",".join(indexed_keys)

    for name, value in datadict.iteritems():
        indexed = False

        if indexed_keys:
            if name in indexed_keys:
                indexed = True
                #console("indexed", otype, name)

        set_property(entity.property.add(), name, value, indexed)

    if commit is None:
        datastore.commit(req)

    if rsc:
        rsc.set("gds_key_" + object_id, entity.key)

    return entity.key


def gds_get_key_name(key):
    """
    @type key: Key
    get the last element, most significant
    /user/User
    """
    #noinspection PyUnresolvedReferences
    retval = None

    for pe in key.path_element:
        if hasattr(pe, "name"):
            retval = pe.name

    if retval:
        return retval
    raise Exception("no name found in key")


def gds_get_key_kind(key):
    """
    @type key: unicode, str(
    """
    for pe in key.path_element:
        if hasattr(pe, "kind"):
            return pe.kind
    raise Exception("no kind found in key")


def gds_result_to_dict_list(resp):
    """
    @type resp: googledatastore.Response
    """
    result = []

    for r in resp.batch.entity_result:
        d = {"keyval": r.entity.key,
             "kindval": gds_get_key_kind(r.entity.key),
             "nameval": gds_get_key_name(r.entity.key)}

        for x in [{"name": p.name, "value": get_value(p.value)} for p in r.entity.property]:
            d[x["name"]] = x["value"]

        if not d["kindval"].startswith("__Stat"):
            result.append(d)

    return result


class GoogleDatastoreException(Exception):
    """
    GoogleDatastoreException
    """
    pass


def gds_get_dict_list(namespace, kind=None, member=None, filterfield=None, filterfieldval=None):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type member: unicode, str
    @type filterfield: unicode, str
    @type filterfieldval: unicode, str
    """
    if kind is None and member is None:
        raise GoogleDatastoreException("kind and member cannot be both None")

    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    q = req.query

    if filterfield and filterfieldval:
        if isinstance(filterfieldval, str):
            filterfieldval = unicode(filterfieldval)

        #noinspection PyUnresolvedReferences
        set_property_filter(q.filter, unicode(filterfield), datastore.PropertyFilter.EQUAL, filterfieldval)

    if kind is not None:
        set_kind(q, kind=kind)

    if member and member != "keyval":
        q.projection.add().property.name = member

    if member == "keyval":
        q.projection.add().property.name = "__key__"

    resp = datastore.run_query(req)
    return gds_result_to_dict_list(resp)


def gds_get_scalar_list(namespace, kind=None, member=None, filterfield=None, filterfieldval=None):
    """
    @type namespace: unicode, str, str
    @type kind: unicode, str, str
    @type member: unicode, str, str
    @type filterfield: unicode, str, str
    @type filterfieldval: unicode, str, str
    """
    result = gds_get_dict_list(namespace, kind, member, filterfield, filterfieldval)

    if member:
        result = [x[member] for x in result if x[member]]
    else:
        result = [x for x in result]
    return result


def gds_get_object_by_key(namespace, keyid):
    """
    @type namespace: unicode, str
    @type keyid: object
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    if namespace:
        #noinspection PyUnresolvedReferences
        req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    q = req.query

    #noinspection PyUnresolvedReferences
    set_property_filter(q.filter, "__key__", datastore.PropertyFilter.EQUAL, keyid)
    resp = datastore.run_query(req)
    dl = gds_result_to_dict_list(resp)

    for d in dl:
        return d


def gds_get_objects_by_fieldsvalues(namespace, kind, filterfields_filterfieldvals, member=None, members=None):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type filterfields_filterfieldvals: list
    @type member: unicode, str, None
    @type members: list
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    q = req.query

    if kind is not None:
        set_kind(q, kind=kind)

    if member or members:
        if not members:
            members = [member]

        for member in members:
            if member and member != "keyval":
                q.projection.add().property.name = member

            if member == "keyval":
                q.projection.add().property.name = "__key__"

    #noinspection PyUnresolvedReferences
    q.filter.Clear()
    cf = q.filter.composite_filter

    #noinspection PyUnresolvedReferences
    cf.operator = datastore.CompositeFilter.AND

    for filterfield, filterfieldval in filterfields_filterfieldvals:
        if isinstance(filterfieldval, str):
            filterfieldval = unicode(filterfieldval)

        #noinspection PyUnresolvedReferences
        cf.filter.add().CopyFrom(set_property_filter(datastore.Filter(), unicode(filterfield), datastore.PropertyFilter.EQUAL, filterfieldval))

    resp = datastore.run_query(req)
    dl = gds_result_to_dict_list(resp)
    return dl


def gds_get_objects_by_fieldvalue(namespace, kind, filterfield, filterfieldval, member=None):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type filterfield: unicode, str
    @type filterfieldval: unicode, str
    @type member: unicode, str, None
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    q = req.query

    if kind is not None:
        set_kind(q, kind=kind)

    if member:
        if member and member != "keyval":
            q.projection.add().property.name = member

        if member == "keyval":
            q.projection.add().property.name = "__key__"

    if isinstance(filterfieldval, str):
        filterfieldval = unicode(filterfieldval)

    #noinspection PyUnresolvedReferences
    set_property_filter(q.filter, unicode(filterfield), datastore.PropertyFilter.EQUAL, filterfieldval)
    resp = datastore.run_query(req)
    dl = gds_result_to_dict_list(resp)
    return dl


def gds_get_object_by_fieldvalue(namespace, kind, filterfield, filterfieldval):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type filterfield: unicode, str
    @type filterfieldval: unicode, str
    """
    for obj in gds_get_objects_by_fieldvalue(namespace, kind, filterfield, filterfieldval):
        return obj
    return None


def gds_get_scalar_value(namespace, kind, filterfield, filterfieldval, member):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type filterfield: unicode, str
    @type filterfieldval: unicode, str
    @type member: str
    """
    dlist = gds_get_objects_by_fieldvalue(namespace, kind, filterfield, filterfieldval)

    for d in dlist:
        if member in d:
            return d[member]


def gds_get_object_by_id(namespace, object_id):
    """
    @type namespace: unicode, str
    @type object_id: str
    """
    keyid = None

    for i in range(0, 15):
        if i > 10:
            time.sleep(0.2)

        if keyid:
            break

        objlist = gds_get_scalar_list(namespace, member=unicode("keyval"))

        for obj in objlist:
            if gds_get_key_name(obj) == object_id:
                keyid = obj

    if not keyid:
        raise GoogleDatastoreException("object_id not found")

    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    q = req.query

    #noinspection PyUnresolvedReferences
    set_property_filter(q.filter, "__key__", datastore.PropertyFilter.EQUAL, keyid)
    resp = datastore.run_query(req)
    dl = gds_result_to_dict_list(resp)

    for d in dl:
        return d


def gds_read_query(namespace, query):
    """
    @type namespace: str
    @type query: str
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    if namespace:
        #noinspection PyUnresolvedReferences
        req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    gql_query = req.gql_query
    gql_query.query_string = query
    resp = datastore.run_query(req)
    return gds_result_to_dict_list(resp)


def gds_delete_item_on_key(namespace, key, transaction=None, force_consistency=True):
    """
    @type namespace: unicode, str
    @type key: object
    @type transaction: googledatastore.Transaction
    @type force_consistency: bool
    """
    if gds_get_key_kind(key).startswith("__Stat_Ns_"):
        console("kind.startswith(__Stat_Ns_)")
        return

    if transaction is None:
        datastore.set_options(dataset="cryptobox2013")
        req = datastore.CommitRequest()

        #noinspection PyUnresolvedReferences
        req.mode = datastore.CommitRequest.NON_TRANSACTIONAL

        #noinspection PyUnresolvedReferences
        req.mutation.delete.extend([key])
        datastore.commit(req)

        if force_consistency:
            for i in range(0, 50):
                if i > 5:
                    time.sleep(0.2)

                if not gds_get_object_by_key(namespace, key):
                    break

    else:
        req = transaction
        req.mutation.delete.extend([key])


def gds_delete_items_on_fieldvalue(namespace, kind, filterfield, filterfieldval, commit=None, force_consistency=True):
    """
    @type namespace: unicode, str
    @type kind: unicode, str
    @type filterfield: unicode, str
    @type filterfieldval: unicode, str
    @type commit: object
    @type force_consistency: bool
    """
    objs = gds_get_objects_by_fieldvalue(namespace, kind, filterfield, filterfieldval, member="keyval")

    keys = [x["keyval"] for x in objs if "keyval" in x]
    num = 0

    for key in keys:
        gds_get_key_name(key)
        gds_delete_item_on_key(namespace, key, commit, force_consistency=force_consistency)
        num += 1

    return num


def gds_run_gql(namespace, query):
    """
    @type namespace: str, unicode
    @type query: str
    """
    datastore.set_options(dataset="cryptobox2013")
    req = datastore.RunQueryRequest()

    #noinspection PyUnresolvedReferences
    req.partition_id.namespace = namespace

    #noinspection PyUnresolvedReferences
    gql_query = req.gql_query
    gql_query.query_string = unicode(query)
    resp = datastore.run_query(req)
    return gds_result_to_dict_list(resp)


def type_from_object_id(oid):
    """
    @type oid: str
    """
    kind = oid.split("_")
    kind = "_".join(kind[:len(kind) - 1])
    kind = inflection.camelize(kind)
    return kind


def get_server(servers):
    """
    try all couch servers and get the first one which is up
    @param servers:list of servers to try
    @type servers:list
    @return:the couchdb server
    @rtype:couchdb.Server
    """
    if len(servers) == 1:
        return couchdb.Server(servers[0]), servers[0]
    else:
        index = random.randint(0, len(servers) - 1)
        return couchdb.Server(servers[index]), servers[index]


def _replicate(database, servers):
    """
    replicate between all servers, replication is done both ways
    @param database:database name
    @type database:string
    @param servers:list of servers
    @type servers:list
    @return:replication succesfull
    @rtype:bool
    """
    couch, couch_ip = get_server(servers)

    for server1 in servers:
        for server2 in servers:
            if server1 != server2:
                server1db = urlparse.urljoin(server1, database)
                server2db = urlparse.urljoin(server2, database)
                report(server1db + " --> " + server2db)
                couch.replicate(server1db, server2db)

    return True


def replicate(database, servers):
    """
    replicate between all servers, replication is done both ways
    @param database:database name
    @type database:string
    @param servers:list of servers
    @type servers:list
    @return:replication succesfull
    @rtype:bool
    """
    return _replicate(database, servers)


class DBNotFound(Exception):
    """
    error thrown if db not found
    """
    pass


class NamespaceNotFound(Exception):
    """
    error thrown if db not found
    """
    pass


def _get_db(name, servers):
    """
    get a database from a couch server
    @param name:name of server
    @type name:string
    @param servers:list of server ips
    @type servers:list
    @return: the coucdhb db
    @rtype: couchdb.client.Database
    """
    couch, server_ip = get_server(servers)
    try:
        dbase = couch[name]
        return dbase, server_ip
    except couchdb.ResourceNotFound:
        raise DBNotFound("database " + name + " not found")
    except ValueError, e:
        raise DBNotFound("database " + name + " " + str(e))


def get_guid():
    """
    generate a unique guid
    @return: guid
    @rtype: string
    """
    return uuid.uuid4().hex


class MemoryNoKey(Exception):
    """
    MemoryNoKey
    """
    pass


class MemoryExpired(Exception):
    """
    MemoryExpired
    """
    pass


class Memory(object):
    #noinspection PyUnresolvedReferences
    """
    @param cls:
    @type cls:
    @param args:
    @type args:
    @param kwargs:
    @type kwargs:
    @return:
    @rtype:
    """
    _instance = None
    data = {}
    timestamps = {}

    def __new__(cls, *args, **kwargs):
        """
        @param args:
        @type args:
        @param kwargs:
        @type kwargs:
        """
        #noinspection PyProtectedMember,PyUnresolvedReferences
        if not cls._instance:
            #noinspection PyAttributeOutsideInit,PyArgumentList
            cls._instance = super(Memory, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def set(self, key, value, timeout_seconds=None, timeout_minute=None):
        """
        @type key: str
        @type value: str
        @type timeout_seconds: int, None
        @type timeout_minute: int, None
        """
        self.data[key] = value

        if timeout_minute:
            timeout_seconds = timeout_minute * 60

        if timeout_seconds:
            self.timestamps[key] = (time.time(), timeout_seconds)

    def has(self, key):
        """
        @param key:
        @type key:
        @return: @rtype: @raise MemoryExpired:
        """
        if key in self.timestamps:
            if int(time.time() - self.timestamps[key][0]) > self.timestamps[key][1]:
                del self.data[key]
                if key in self.timestamps:
                    del self.timestamps[key]
                raise MemoryExpired(key)

        return key in self.data

    def has_get_no_ts(self, key):
        """
        @type key: str
        """
        if key in self.data:
            return self.data[key]
        return None

    def ttl(self, key, show_seconds=False):
        """
        @param key:
        @type key:
        @param show_seconds:
        @type show_seconds:
        @return: @rtype:
        """
        if key in self.timestamps:
            timestamp = self.timestamps[key][0]
            timeout = self.timestamps[key][1]
            seconds = timeout - int(time.time() - timestamp)

            if show_seconds:
                return seconds
            else:
                return int(math.ceil(float(seconds) / 60))
        return None

    def get(self, key):
        """
        @param key:
        @type key:
        @return: @rtype: @raise MemoryNoKey:
        """
        if self.has(key):
            if key in self.timestamps:
                self.timestamps[key] = (time.time(), self.timestamps[key][1])

            return self.data[key]
        else:
            raise MemoryNoKey(str(key))

    def delete(self, key):
        """
        @param key:
        @type key:
        @raise MemoryNoKey:
        """
        if self.has(key):
            del self.data[key]
            if key in self.timestamps:
                del self.timestamps[key]
            return True
        else:
            raise MemoryNoKey(str(key))

    def size(self):
        """
        size
        @return: @rtype:
        """
        return len(self.data)


class CouchViewError(Exception):
    """
    CouchViewError
    """
    pass


class CouchView(object):
    """
    CouchView
    """

    def __init__(self, dbase, mapf, reducef):
        """
        @param dbase: database object
        @type dbase: CouchDBServer
        @param mapf: map function
        @type mapf: string, unicode
        @param reducef: reducefunction
        @type reducef: string, unicode
        """
        self.dbase = dbase

        if not map:
            raise CouchViewError("need at least a map function")

        self.map = str(mapf)

        if not reducef:
            self.reduce = ""
        else:
            self.reduce = str(reducef)

    def sync(self):
        """
        sync
        """
        insert = False
        try:
            view_doc = self.dbase.get_document("_design/crypto_data")
        except DocNotFoundException:
            view_doc = None
        except Exception, ex:
            view_doc = None

            if not "DocNotFoundException" in str(type(ex)):
                console_warning("strange error in view sync", type(ex))

        mapf = ""

        for l in self.map.split("\n"):
            if "return" in l:
                mapf += "  "
            mapf += l.strip() + "\n"
        self.map = mapf
        reducef = ""

        for l in self.reduce.split("\n"):
            if "return" in l:
                reducef += "  "
            reducef += l.strip() + "\n"
        self.reduce = reducef

        if view_doc:
            if "views" in view_doc:
                if self.__class__.__name__ in view_doc["views"]:
                    if self.map.strip() != view_doc["views"][self.__class__.__name__]["map"]:
                        insert = True

                    if "reduce" in view_doc["views"][self.__class__.__name__]:
                        if self.reduce.strip() != view_doc["views"][self.__class__.__name__]["reduce"]:
                            insert = True

                else:
                    insert = True

        else:
            insert = True

        if not view_doc:
            view_doc = {"_id": "_design/crypto_data", "views": {self.__class__.__name__: {"map": self.map.strip(), }},
                        "language": "javascript"}

            if len(self.reduce.strip()) > 0:
                view_doc["views"][self.__class__.__name__]["reduce"] = self.reduce.strip()
        else:
            view_doc["views"][self.__class__.__name__] = {"map": self.map.strip()}

            if len(self.reduce.strip()) > 0:
                view_doc["views"][self.__class__.__name__]["reduce"] = self.reduce.strip()

        if insert:
            sync_mutex = Mutex("view_sync", self.dbase.dbname)
            try:
                sync_mutex.acquire_lock()
                self.dbase.add_document(view_doc)
            except couchdb.ResourceConflict:
                console_warning("conflict updating design doc!")
            finally:
                sync_mutex.release_lock()

        return insert


class AllCouchIDSAndRevs(CouchView):
    """
    AllCouchIDS
    """

    def __init__(self, dbase):
        """
        __init__
        """
        map_func = """
    var map_func;
    map_func = function(doc) {
        return emit(doc._id, doc._rev);
    };
    """
        super(AllCouchIDSAndRevs, self).__init__(dbase, map_func, None)


class CountTypes(CouchView):
    """ Count the number of documents available, per type. """

    def __init__(self, dbase):
        """
        __init__
        """
        map_func = """
        var map_func;
        map_func = function(doc) {
          if (doc.doctype != null) {
            return emit(doc.object_type, 1);
          }
        };
        """
        reduce_func = """
        var reduce_func;
        reduce_func = function(keys, values, rereduce) {
          return sum(values);
        };
        """
        super(CountTypes, self).__init__(dbase, map_func, reduce_func)


class SaveObjectCreated(CouchView):
    """ Count the number of documents available, per type. """

    def __init__(self, dbase):
        """
        __init__
        """
        map_func = """
        var map_func;
        map_func = function(doc) {
          if (doc.doctype != null) {
            return emit(-doc.m_created, {"m_created":doc.m_created, "object_id": doc.object_id});
          }
        };
        """
        super(SaveObjectCreated, self).__init__(dbase, map_func, None)


class SaveObjectMutationCounter(CouchView):
    """ Count the number of documents available, per type. """

    def __init__(self, dbase):
        """
        __init__
        """
        map_func = """
        var map_func;
        map_func = function(doc) {
          if (doc.doctype != null) {
            return emit(doc._id, doc.mutation_counter);
          }
        };
        """
        super(SaveObjectMutationCounter, self).__init__(dbase, map_func, None)


class SaveObjectSeq(CouchView):
    """ Count the number of documents available, per type. """

    def __init__(self, dbase):
        """
        __init__
        """
        map_func = """
        var map_func;
        map_func = function(doc) {
          if (doc.doctype != null) {
            return emit(doc._id, [doc.seq, doc._rev]);
          }
        };
        """
        super(SaveObjectSeq, self).__init__(dbase, map_func, None)


class TreeNodeData(CouchView):
    """ get all the doc hashes """

    def __init__(self, dbase):
        map_func = """
    var map_func;
    map_func = function(doc) {
      if (doc.object_type === "SaveNodeData") {
        return emit(doc.m_tree_object_id, doc);
      }
    };
    """
        super(TreeNodeData, self).__init__(dbase, map_func, None)


class TreeNodeShortId(CouchView):
    """ get all the doc hashes """

    def __init__(self, dbase):
        map_func = """
    var map_func;
    map_func = function(doc) {
      if (doc.object_type === "SaveNodeData") {
        return emit(doc.m_tree_object_id, doc.m_short_id);
      }
    };
    """
        super(TreeNodeShortId, self).__init__(dbase, map_func, None)


def get_class(class_string):
    """
    return a class based on the module.class string (class_string)
    @type class_string: str, unicode
    """
    parts = class_string.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)

    for comp in parts[1:]:
        m = getattr(m, comp)

    return m


def sync_all_views(dbase, list_mod_names):
    """
    Instantiate all the classes which inherit from CouchView in the modules and call the sync method
    @type dbase: CouchDBServer
    @param list_mod_names: list of module names
    @type list_mod_names: list
    """
    mtx = Mutex("sync_all_views", dbase.get_db_name())
    mtx.acquire_lock()
    try:
        view_classes = []

        for mod_name in list_mod_names:
            if mod_name in sys.modules:
                for name, obj in inspect.getmembers(sys.modules[mod_name]):
                    if inspect.isclass(obj):
                        for bc in inspect.getmro(obj):
                            if "CouchView" in str(bc) and "CouchView" not in name:
                                view_classes.append(mod_name + "." + name)

        for class_string in view_classes:
            view_class = get_class(class_string)
            view_obj = view_class(dbase)

            if view_obj.sync():
                pass
                #console("Viewclass sync", class_string)

    finally:
        mtx.release_lock()
LOCKHOST = "10.240.26.61:8001"


g_hostname = subprocess.check_output("hostname")

if "node1" not in g_hostname and "node2" not in g_hostname and "worker1" not in g_hostname:
    LOCKHOST = "localhost:8001"


g_locks = {}
g_lock_times = {}


def local_lock_acquire(key):
    """
    @param key:
    @type key:
    @return: @rtype:
    """
    global g_locks
    global g_lock_times
    if key in g_locks:
        res = g_locks[key].acquire(False)

        if res:
            g_lock_times[key] = time.time()

        return res
    else:
        g_locks[key] = threading.Lock()
        res = g_locks[key].acquire(False)

        if res:
            g_lock_times[key] = time.time()

        return res


def local_lock_release(key):
    """
    @param key:
    @type key:
    @return: @rtype:
    """
    try:
        global g_locks
        if key in g_locks:
            g_locks[key].release()
            return True
        return False
    except threading.ThreadError, e:
        console(e.message, key)
        return False


def local_lock_exists(key):
    """
    @param key:
    @type key:
    @return: @rtype:
    """
    global g_locks
    if key in g_locks:
        return not g_locks[key].acquire(False)
    return False


class LockNoTime(Exception):
    """
    LockNoTime
    """
    pass


def local_lock_starttime(key):
    """
    @param key:
    @type key:
    @return: @rtype: @raise:
    """
    global g_lock_times
    if key in g_lock_times:
        return g_lock_times[key]
    raise LockNoTime(key)


class MutexNoKey(Exception):
    """
    MutexNoKey
    """
    pass


def memcache_lock_acquire(key, local):
    """
    @type key: str
    @type local: bool
    """
    if local:
        if not local_lock_acquire(key):
            return False
        else:
            return True


def memcache_lock_release(key, local):
    """
    @type key: str
    @type local: bool
    """
    if local:
        local_lock_release(key)
        return True


def memcache_lock_exists(key, local):
    """
    @type key: str
    @type local: bool
    """
    if local:
        if local_lock_exists(key):
            return True
        else:
            return False


class NoMemcacheServerMutex(Exception):
    """
    NoMemcacheServerMutex
    """
    pass


class Mutex(object):
    """
    @param slug:
    @type slug:
    @param name:
    @type name:
    """

    def __init__(self, slug, name, ttl=60):
        """
        @param name: name of the mutex
        @type name: string
        """
        self.local = True
        self.m_start = time.time()
        self.m_ttl = ttl
        name = name.lower()
        self.m_mutex_name = slug + "_" + name
        self.m_mutex_name = key_ascii(self.m_mutex_name)
        global redis_pool
        self.pool = redis_pool

    def acquire_lock_no_wait(self):
        """
        acquire_lock_no_wait
        @return: @rtype:
        """
        if not memcache_lock_acquire(self.m_mutex_name, self.local):
            return False
        else:
            console(self.m_mutex_name, "lock acquired")
            return True

    def acquire_lock(self):
        """
        acquire_lock
        @return: @rtype:
        """
        cnt = 0

        while True:
            if (time.time() - self.m_start) > self.m_ttl:
                #console_warning("mutex reached ttl", self.m_mutex_name, self.m_ttl)
                self.release_lock()

            if memcache_lock_acquire(self.m_mutex_name, self.local):
                #console("lock", self.m_mutex_name)
                self.m_start = time.time()
                return True

            if cnt > 100:
                time.sleep(random.random() * 1)

            if cnt > 50:
                time.sleep(0.01)
            cnt += 1

    def exists_lock(self):
        """
        exists_lock
        @return: @rtype:
        """
        return memcache_lock_exists(self.m_mutex_name, self.local)

    def release_lock(self):
        """
        release_lock
        @return: @rtype:
        """
        while True:
            released = memcache_lock_release(self.m_mutex_name, self.local)

            if released:
                #console("release", self.m_mutex_name)
                return True

            time.sleep(0.05)


class Compacter(threading.Thread):
    """
    @param serverurl:
    @type serverurl:
    @param name:
    @type name:
    """

    def __init__(self, serverurl, name):
        """
        @type serverurl: str
        @type name: str
        """
        super(Compacter, self).__init__()
        self.serverurl = serverurl
        self.name = name

    def run(self):
        """
        run(self):
        """
        console("compacting", self.serverurl, self.name)
        bserver = couchdb.Server(self.serverurl)

        for shard in bserver:
            if self.name + "." in str(shard):
                dbase = bserver[shard]
                dbase.compact()
                dbase.compact("crypto_data")


class ScalarResultContainsMultipleItems(Exception):
    """
    ScalarResultContainsMultipleItems
    """
    pass


class NoResultsFromView(Exception):
    """
    NoResultsFromView
    """
    pass


class ServerConfig(object):
    """
    ServerConfig
    """

    def __init__(self, dbname):
        """
        __init__
        """
        self.events = Events()
        self.pid = os.getppid()
        self.server_ip = None

        if dbname is None:
            raise Exception("dataname not set")

        self.namespace = dbname
        self.pid = os.getppid()

    def report_measurements(self, group=True, show_threshhold=0.0, show_total=True, show_all_if_threshold=False):
        """
        @type group: bool
        @type show_threshhold: float
        @type show_total: bool
        @type show_all_if_threshold: bool
        """
        self.events.report_measurements(group=group, show_threshhold=show_threshhold, show_total=show_total, show_all_if_threshold=show_all_if_threshold)

    def event(self, *args, **kwargs):
        """
        @param args:
        @type args:
        @param kwargs:
        @type kwargs:
        """
        kwargs["line_num_only"] = 4
        self.events.event(*args, **kwargs)

    def identifcation(self):
        """
        identifcation
        """
        return self.get_namespace().replace(".", "-").replace(":", "-").rstrip("/")

    def get_namespace(self):
        """
        get the name of the database
        @return: name of database
        @rtype: string
        """
        return self.namespace

    def get_redis_server(self):
        """
        get_redis_server
        @rtype:RedisServer
        """
        return RedisServer(self.get_namespace())

    def rs_get(self, key):
        """
        @type key: str
        """
        return RedisServer(self.get_namespace()).get(key)

    def rs_flush_all(self):
        """
        rs_flush
        """
        return RedisServer(self.get_namespace()).flush_all()

    def rs_flush_namespace(self):
        """
        rs_flush
        """
        return RedisServer(self.get_namespace()).flush_namespace()

    def rs_flush_prefix(self, prefix):
        """
        @type prefix: str
        """
        return RedisServer(self.get_namespace()).flush_prefix(prefix)

    def rs_set(self, key, value, ttl=None):
        """
        @type key: str
        @type value: str, float, dict, list, int
        @type ttl: float
        """
        return RedisServer(self.get_namespace()).set(key, value, ttl)

    def rs_del(self, key):
        """
        @type key: str
        """
        return RedisServer(self.get_namespace()).delete(key)

    def gds_run_view(self, kind, filterfield, filterfieldval, member=None):
        """
        @type kind: str, unicode
        @type filterfield: str, unicode
        @type filterfieldval: str, unicode
        @type member: str, None
        """
        if member is None:
            console_warning("gds_run_view: no member given")

        kind = unicode(kind)
        filterfield = unicode(filterfield)
        filterfieldval = unicode(filterfieldval)
        try:
            result = gds_get_objects_by_fieldvalue(self.get_namespace(), kind, filterfield, filterfieldval, member)
        except datastore.RPCError, ex:
            if strcmp(ex.reason, "no matching index found."):
                console(ex.reason, warning=True)
                result = []
            else:
                raise

        return result

    def gds_run_view_fields_values(self, kind, filterfield_filterfieldvals, member=None):
        """
        @type kind: str, unicode
        @type filterfield_filterfieldvals: list
        @type member: str, None
        """
        if member is None:
            console_warning("gds_run_view_fields_values: no member given")

        kind = unicode(kind)
        return gds_get_objects_by_fieldsvalues(self.get_namespace(), kind, filterfield_filterfieldvals, member)

    def info(self):
        """
        @return: info about this database
        @rtype: dict
        """
        return {"disk_size": 1024 * 1024 * 1024 * 3,
                "doc_count": 1}


class CouchDBServer(ServerConfig):
    """ CouchDB functionality wrapped in a class """
    dbase = None
    replicate_change = True

    def __init__(self, dbname, couchdb_server_list, replicate_change=False, throw_dbnotfound=False, make_couchb_connection=False):
        """
        @type dbname: str, unicode
        @type couchdb_server_list: list
        @type: list
        @type replicate_change: bool
        """
        super(CouchDBServer, self).__init__(dbname, )
        self.replicate_change = replicate_change
        self.couchdb_server_list = couchdb_server_list
        self.dbname = dbname
        servers = self.couchdb_server_list

        if make_couchb_connection:
            try:
                self.dbase, self.server_ip = _get_db(dbname, servers)
            except DBNotFound, ex:
                if throw_dbnotfound:
                    raise ex
                else:
                    console(dbname, "not found, creating it")
                    self.create(dbname)

            if self.dbase is None:
                raise Exception("database does not exist")

    def info(self):
        """
        @return: info about this database
        @rtype: dict
        """
        if self.dbase is None:
            raise Exception("database not set")

        return self.dbase.info()

    def get_db_name(self):
        """
        get the name of the database
        @return: name of database
        @rtype: string
        """
        return self.dbname

    def get_db_servers(self):
        """
        get the cluster
        """
        return self.couchdb_server_list

    def identifcation(self):
        """
        @return:
        @rtype:
        """
        return "couchdb_" + self.get_db_name().replace(".", "-").replace(":", "-").rstrip("/")

    def create(self, dbname):
        """
        create all the database on the cluster
        @type dbname: str, unicode
        @return: succes
        @rtype: bool
        """
        for server in self.get_db_servers():
            if not dbname in list(couchdb.Server(server)):
                couchdb.Server(server).create(dbname)

        self.dbname = dbname
        self.dbase, server_ip = _get_db(self.dbname, self.couchdb_server_list)

        if self.dbase is None:
            raise Exception("database does not exist")

        return True

    def ensure_dbs_on_servers(self):
        """ make sure the db is on all our couchdb servers """
        for server in self.couchdb_server_list:
            couch = couchdb.Server(server)

            if self.dbname not in couch:
                couch.create(self.dbname)

        self.replicate_changes()

    def compact_database(self):
        """ remove old revisions, keep database small """
        if self.dbase is None:
            raise Exception("database not set")

        self.dbase.compact()
        self.dbase.compact("crypto_data")

    def get_couchdbdbase(self):
        """
        get database
        @return: the coucdhb db
        @rtype: couchdb.Database
        """
        if self.dbase is None:
            raise Exception("database not set")

        return self.dbase

    def changes_long_poll(self, since=0, timeout=60000):
        """
        ask couch for the list of changes compared to 'since'
        @param timeout:
        @type timeout:
        @param since: the sequence number of couchdb
        @type since: int
        @return: changes and docs
        @rtype: dict
        """
        if self.dbase is None:
            raise Exception("database not set")

        return self.dbase.changes(since=since, feed="longpoll", style="main_only", timeout=timeout, descending="true", include_docs='false')

    def add_document(self, document, doc_id=None):
        """
        @type document: dict, None
        @type doc_id: str, None
        """
        if self.dbase is None:
            raise Exception("database not set")

        if not isinstance(document, dict):
            raise Exception("documents should be of type dictionary")

        if not doc_id:
            if "_id" in document:
                doc_id = unicode(document["_id"])
            else:
                doc_id = get_guid()

        if self.replicate_change:
            replicate(self.dbname, self.couchdb_server_list)
        document["_id"] = doc_id
        doc_id, doc_rev = self.dbase.save(document)

        if self.replicate_change:
            replicate(self.dbname, self.couchdb_server_list)

        return doc_id, doc_rev

    def get_document(self, doc_id, allow_none=False):
        """
        get doc from couchdb
        @param doc_id: id of the document
        @type doc_id: string
        @type allow_none: bool
        @return: document
        @rtype: dict
        """
        if self.dbase is None:
            raise Exception("database not set")

        doc = self.dbase.get(doc_id)

        if doc is None:
            if not allow_none:
                raise DocNotFoundException("doc not found")

        return doc

    def delete_document(self, doc_id):
        """
        delete
        @param doc_id: the id of the doc
        @type doc_id: string
        """
        if self.dbase is None:
            raise Exception("database not set")

        try:
            doc = self.get_document(doc_id)

            if not doc:
                return False
        except couchdb.ResourceNotFound:
            return False
        except DocNotFoundException:
            return False

        self.dbase.delete(doc)
        return True

    def get_all_document_ids(self):
        """
        get the whole database
        @return: list of doc ids
        @rtype: list
        """
        if self.dbase is None:
            raise Exception("database not set")

        (resp, msg, result) = self.dbase.resource.get("_all_docs", params={"include_docs": "false"})
        ids = []

        if resp == 200:
            result = cjson.decode(result.read())

            for row in result["rows"]:
                rowid = row["id"]

                if "_design/" not in rowid:
                    ids.append(rowid)

        else:
            raise msg

        return ids

    def replicate_changes(self):
        """
        replicate couchdb instances
        @return:
        @rtype:
        """
        replicate(self.dbname, self.couchdb_server_list)

        #noinspection PyUnreachableCode
    def call_view(self, key, keys, methodname, use_group):
        """
        @param key:
        @type key:
        @param keys:
        @type keys:
        @param methodname:
        @type methodname:
        @param use_group:
        @type use_group:
        @return: @rtype:
        """
        if key:
            if use_group:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname, keys=[key], group=True)
            else:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname, keys=[key])
        elif keys:
            if use_group:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname, keys=keys, group=True)
            else:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname, keys=keys)
        else:
            if use_group:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname, group=True)
            else:
                results = self.dbase.view("_design/crypto_data/_view/" + methodname)

        return results

    def run_view(self, methodname, key=None, keys=None, view_object=None, scalar=False):
        """
        run a view in couch, if a doc should be unique use scalar
        @param methodname: name of the method to run
        @type methodname: string
        @param key: key of the data
        @type key:
        @param keys: list of keys of the data
        @type keys: list
        @param view_object: the view object
        @type view_object: class
        @param scalar: return a single value instead of a list with one item
        @type scalar: bool
        """
        if view_object:
            methodobject = view_object(self)
        else:
            methodobject = globals()[methodname](self)
        use_group = False

        if methodobject.reduce:
            if len(methodobject.reduce.strip()) > 0:
                use_group = True

        results = self.call_view(key, keys, methodname, use_group)
        try:
            results = list(results)
        except Exception, e:
            err = handle_ex(e, False, True)
            console_warning("run_view is calling sync", methodname, "use sync_all_views", err)
            methodobject.sync()
            results = self.call_view(key, keys, methodname, use_group)
            try:
                results = list(results)
            except Exception, ex:
                handle_ex(ex)

        if scalar:
            if len(results) == 0:
                results = None
            elif len(results) == 1:
                results = results[0]["value"]
            else:
                raise ScalarResultContainsMultipleItems(methodname + " returned multple items")

        return results


class ObjectSaveException(Exception):
    """ exception raised if the object cannot be saved """

    def __init__(self, exc, obj):
        """
        @type exc: str
        @type obj: SaveObjectGoogle, SaveObjectCouch
        """
        objstr = str(obj.object_type) + ":" + str(obj.object_id)
        super(ObjectSaveException, self).__init__(exc + " -> " + objstr)


class ObjectDeleteException(Exception):
    """ exception raised if the object cannot be deleted """

    def __init__(self, exc, obj):
        """
        @type exc: str, Exception
        @type obj: SaveObjectGoogle, SaveObjectCouch
        """
        objstr = str(obj.object_type) + ":" + str(obj.object_id)
        super(ObjectDeleteException, self).__init__(exc + " -> " + objstr)


class ObjectLoadException(Exception):
    """ exception raised if the object cannot be loaded """

    def __init__(self, exc, obj):
        """
        @type exc: str, Exception
        @type obj: SaveObjectGoogle, SaveObjectCouch
        """
        objstr = str(obj.object_type) + ":" + str(obj.object_id)
        super(ObjectLoadException, self).__init__(exc + " -> " + objstr)


class MemberAddedToObjectException(Exception):
    """ exception raised if a member has been added """

    def __init__(self, exc, obj):
        """
        @type exc: str, Exception
        @type obj: SaveObjectGoogle, SaveObjectCouch
        """
        objstr = str(obj.object_type) + ":" + str(obj.object_id)
        super(MemberAddedToObjectException, self).__init__(exc + " -> " + objstr)


class CollectionTooBig(Exception):
    """ exception raised when there are more then 100 items fetched in a collection """

    def __init__(self, exc, obj):
        """
        @type exc: str, Exception
        @type obj: SaveObjectGoogle, SaveObjectCouch
        """
        objstr = str(obj.object_type) + ":" + str(obj.object_id)
        super(CollectionTooBig, self).__init__(exc + " -> " + objstr)


class ObjectIDAlreadyDeleted(Exception):
    """
    ObjectIDAlreadyDeleted
    """
    pass


class ObjectDoesNotExist(Exception):
    """
    ObjectDoesNotExist
    """
    pass


class ObjectIdInvalid(Exception):
    """
    ObjectIdInvalid. The specified object id is not a valid id
    """
    pass


class SaveObjectAttachmentNotFound(Exception):
    """
    SaveObjectAttachmentNotFound
    """
    pass


def make_object_id_string(object_type, guid=None):
    """
    @param object_type: the class name
    @type object_type: string, unicode
    @param guid: if you want you can provide your own guid
    @type guid: string, unicode
    """
    if not guid:
        guid = uuid.uuid4().hex

    if set('_').issubset(set(guid)):
        raise ObjectIdInvalid("It is not allowed to use '_' in a guid, it is reserved. Guid: %s" % (guid, ))

    if "." in object_type:
        split = object_type.split(".")
        object_type = split[len(split) - 1]

    if " " in object_type:
        object_type = object_type.split(" ")[0]
        object_type = object_type.strip()

    type_string = inflection.underscore(object_type) + "_" + str(guid)
    lot = len(object_type)
    cnt = 0
    caps = range(ord("A"), ord("Z"))

    while type_from_object_id(type_string) != object_type:
        ot = object_type
        ot = ot[:cnt] + "_" + ot[cnt:]
        type_string = inflection.underscore(ot) + "_" + str(guid)
        cnt += 1

        if cnt > lot:
            break

    if type_from_object_id(type_string) != object_type:
        ot = ""
        prev_caps = False

        for c in object_type:
            if ord(c) in caps:
                if prev_caps:
                    ot += "_"
                prev_caps = True
            else:
                prev_caps = False
            ot += c

        type_string = inflection.underscore(ot) + "_" + str(guid)

    if type_from_object_id(type_string) != object_type:
        raise Exception(object_type, "not id stringable")

    return type_string


class GenericException(Exception):
    """
    GenericException
    """
    pass


#noinspection PyTypeChecker
class SaveObjectCouch(object):

    """ Base class for saving python objects """

    def get_db(self):
        """
        get_db
        @return: @rtype: @raise Exception:
        """
        if self.dbase is None:
            raise Exception()

        return self.dbase

    def __init__(self, dbase=None, object_id=None, comment="a save object"):
        """
        @param dbase: database
        @type dbase: CouchDBServer
        @param object_id: id of object
        @type object_id: string or None
        @param comment: a comment
        @type comment: string
        """
        self.try_counter = 0
        self.debug = False
        self.raw = False
        self.dataloaded = False
        self.object_dict = None
        self.object_id = None
        self.object_type = None
        self.comment = None
        self.seq = "0"
        self._rev = ""
        self._id = None
        self._attachments = {}
        self._data_changed = False
        self.att_timestamps = {}
        self.comment = comment
        self.dbase = dbase
        self.couchdb_document = {"doctype": "cb_object"}

        if not self.object_type:
            self.object_type = self.get_object_type()
        self.object_id = object_id
        self.m_created = time.time()
        self.m_last_changed = time.time()

        if not hasattr(self, "required"):
            self.required = []
        self.changed_without_property = []
        self.user_editable_order = 0
        self.user_editable = {}
        self.mutation_counter = 0
        # remove dynamically added members

        def decode_b64(v):
            """
            decode_b64
            @param v:
            @type v:
            """
            #noinspection PyBroadException
            try:
                v2 = pickled_base64_to_object(v)
            except:
                v2 = v

            return v2

        for member in dir(self):
            if member.startswith("m_"):
                self.add_property(member)

        for member in dir(self):
            if member.endswith("_p64s"):
                setattr(self, member, decode_b64(getattr(self, member)))

        self._data_changed = False

        if not hasattr(self, "object_id"):
            self.object_id = None

        if self.object_id and not self.__is_valid_object_id(self.object_id):
            raise ObjectIdInvalid("Invalid object-id: %s" % (self.object_id, ))

        if not self.object_id:
            self.object_id = make_object_id_string(self.object_type)
            self._data_changed = True

    @staticmethod
    def __is_valid_object_id(object_id):
        """
        __is_valid_object_id
        @param object_id:
        @type object_id:
        """
        if not isinstance(object_id, str) and not isinstance(object_id, unicode):
            return False
        return True

    def add_user_editable(self, name, obj_type, required, label=None):
        """
        @param name:
        @type name:
        @param obj_type:
        @type obj_type:
        @param required:
        @type required:
        @param label:
        @type label:
        """
        if name in self.required:
            required = True

        if not label:
            label = name.replace("m_", "", 1).replace("_", " ").capitalize()
        d = {"member": name,
             "type": obj_type,
             "required": required,
             "label": label,
             "order": self.user_editable_order}

        if obj_type == "password":
            d["member_again"] = name + "_again"

        if obj_type == "bool":
            d["required"] = False
        self.user_editable_order += 1

        #noinspection PyUnresolvedReferences
        self.user_editable[name] = d

    def get_sequence_number(self):
        """
        get_sequence_number
        @return: @rtype:
        """
        return self.mutation_counter

    def get_user_editable(self):
        """
        get_user_editable
        @return: @rtype: dict
        """
        return self.user_editable

    def set_required(self, required_member_list):
        """
        @param required_member_list: "m_" class attributes which are required for save
        @type required_member_list: list
        @return: nothing
        @rtype: None
        """
        self.required = required_member_list

    def lifetime(self):
        """
        lifetime
        @return: @rtype:
        """
        return time.time() - self.m_created

    def lifetime_last_update(self):
        """
        lifetime_last_update
        @return: @rtype:
        """
        return time.time() - self.m_last_changed

    def update_timestamp(self, attribute):
        """
        update a timestamp for a member attribute
        @param attribute: attribute to stamp
        @type attribute: string
        """
        if not hasattr(self, "att_timestamps"):
            self.att_timestamps = {}
        self.att_timestamps[attribute] = time.time()

    def add_property(self, name):
        """
        generate a property with a timestamp entry
        @param name: name of the property
        @type name: string
        """
        if not hasattr(self, name):
            raise Exception("cannot add property for " + str(name))

        if name.startswith("_"):
            return

        setattr(self, "_" + name, getattr(self, name))

        #noinspection PyShadowingNames
        def getf(self):
            """
            getf
            """
            obj = self.getattrc("_" + name)

            if isinstance(obj, dict):
                self._data_changed = True
            elif isinstance(obj, list):
                self._data_changed = True
            elif isinstance(obj, tuple):
                self._data_changed = True

            return obj

        #noinspection PyShadowingNames
        def setf(self, value):
            """
            @param self:
            @type self:
            @param value:
            @type value:
            """
            if hasattr(self, "_" + name):
                old_value = self.getattrc("_" + name)

                if old_value == value:
                    return

            self.setattrc("_" + name, value)

        setattr(self.__class__, name, property(getf, setf))

    def getattrc(self, name):
        """
        get an attribute by name
        @param name: name of the prop
        @type name: string
        """
        if not hasattr(self, name):
            setattr(self, name, None)

        return getattr(self, name)

    def setattrc(self, name, value):
        """ set an attribute by name and update timestamp
        @param name:
        @type name:
        @param value:
        @type value:
        """
        self._data_changed = True

        if not hasattr(self, name):
            setattr(self, name, None)

        self.update_timestamp(name)
        setattr(self, name, value)

    def get_object_type(self):
        """ get the object type in a string format """
        object_type = str(repr(self))

        if "." in object_type:
            split = object_type.split(".")
            object_type = split[len(split) - 1]

        if " " in object_type:
            object_type = object_type.split(" ")[0]
            object_type = object_type.strip()
            return object_type
        else:
            return None

    def get_member(self, key):
        """
        @param key: key -> m_key
        @type key: str
        """
        retval = getattr(self, key)
        return retval

    def _remove_member(self, key):
        """
        remove a member from class an initial value
        @param key:
        @type key:
        """
        key = key.strip()

        if "_" + key in self.att_timestamps:
            del self.att_timestamps["_" + key]

        if hasattr(self, key):
            delattr(self, key)
            self._data_changed = True

    def count_members(self):
        """
        count all the database members
        """
        cnt = 0

        for member in dir(self):
            if member.startswith("m_"):
                cnt += 1

        return cnt

    def get_list_of_members(self, prefix):
        """
        get a list of members
        @param prefix:
        @type prefix:
        """
        ml = []

        for member in dir(self):
            if member.startswith(prefix):
                ml.append(member)

        return ml

    def count(self, dbase=None):
        """
        count the number of docs
        @param dbase: database
        @type dbase: CouchDBServer, None
        """
        if dbase:
            self.dbase = dbase

        if self.dbase is None:
            raise ObjectLoadException("Database variable not set (dbase)", self)

        val = self.dbase.run_view("CountTypes", key=self.object_type, scalar=True)

        if not val:
            return 0
        return val

    def debug_timestamp(self, debug, key, mymember_timestamp, newermember_timestamp, newest_doc):
        """
        @param debug:
        @type debug: bool
        @param key:
        @type key: string
        @param mymember_timestamp:
        @type mymember_timestamp: float
        @param newermember_timestamp:
        @type newermember_timestamp: float
        @param newest_doc:
        @type newest_doc: dict
        """
        if debug:
            print "crypto_data.py:4855", "---------------------------------------------------------------------------"
            print "crypto_data.py:4856", key
            print "crypto_data.py:4857", newest_doc[key]
            print "crypto_data.py:4858", getattr(self, key)
            print "crypto_data.py:4859", newermember_timestamp
            print "crypto_data.py:4860", "mymember_timestamp", mymember_timestamp
            nwt = newermember_timestamp >= mymember_timestamp
            print "crypto_data.py:4862", "newermember_timestamp >= mymember_timestamp", nwt
            print "crypto_data.py:4863", "---------------------------------------------------------------------------"

    def handleconflict(self, newest_doc):
        """
        conflict resolution by comparing the timestamps of the member attributes
        @param newest_doc: document
        @type newest_doc: dict
        """
        localmembers = dir(self)
        missing_attachments = False

        if "mutation_counter" not in newest_doc:
            self.mutation_counter = 0
        else:
            self.mutation_counter = newest_doc["mutation_counter"]

        if "_attachments" in newest_doc:
            for k in newest_doc["_attachments"]:
                if k not in self._attachments:
                    missing_attachments = True
                else:
                    for k2 in newest_doc["_attachments"][k]:
                        for k3 in self._attachments[k]:
                            if newest_doc["_attachments"][k][k2] != self._attachments[k][k3]:
                                missing_attachments = True

        if missing_attachments:
            stored_members = {}
            stored_stamps = self.att_timestamps.copy()

            for mymember in localmembers:
                if mymember.startswith("m_"):
                    val = getattr(self, mymember)

                    if isinstance(val, dict):
                        stored_members[mymember] = val.copy()
                    else:
                        stored_members[mymember] = val

            self.load(self.object_id)

            for member in dir(self):
                if member.startswith("m_"):
                    if member not in stored_members.keys():
                        self._remove_member(member)

            for member in stored_members:
                if isinstance(stored_members[member], dict):
                    setattr(self, member, stored_members[member].copy())
                else:
                    setattr(self, member, stored_members[member])

            self.att_timestamps = stored_stamps.copy()

        for mymember in localmembers:
            if mymember.startswith("m_"):
                key = mymember
                mymember_timestamp = None
                newermember_timestamp = None

                if "_" + key in self.att_timestamps:
                    mymember_timestamp = self.att_timestamps["_" + key]

                if "_" + key in newest_doc["att_timestamps"]:
                    newermember_timestamp = newest_doc["att_timestamps"]["_" + key]
                    #self.debug_timestamp(debug, key, mymember_timestamp, newermember_timestamp, newest_doc)
                overwrite = True

                if mymember_timestamp:
                    if newermember_timestamp <= mymember_timestamp:
                        overwrite = False

                if overwrite:
                    if "_" + key not in newest_doc["att_timestamps"]:
                        newest_doc["att_timestamps"]["_" + key] = time.time()
                    self.att_timestamps["_" + key] = newest_doc["att_timestamps"]["_" + key]

                    if key.endswith("_p64s"):
                        #if key == "m_aes_encrypted_rsa_private_key_p64s":
                        #    pass
                        if key in newest_doc:
                            if isinstance(newest_doc[key], dict):
                                adict = newest_doc[key]

                                for key2 in adict.keys():
                                    adict[key2] = pickled_base64_to_object(adict[key2])

                                setattr(self, "_" + key, adict)
                            else:
                                newest_doc[key] = pickled_base64_to_object(newest_doc[key])
                                setattr(self, "_" + key, newest_doc[key])
                        else:
                            setattr(self, "_" + key, None)
                    else:
                        if key in newest_doc:
                            setattr(self, "_" + key, newest_doc[key])
                        else:
                            setattr(self, "_" + key, None)

    def checkforconflicts(self, latest_rev):
        """
        compare revision with latest revision in couch
        @param latest_rev: latest revision
        @type latest_rev:
        """
        newest_doc = None

        if "_rev" in self.couchdb_document:
            if latest_rev != self.couchdb_document["_rev"]:
                newest_doc = self.dbase.get_document(self.object_id)
        else:
            if latest_rev:
                newest_doc = self.dbase.get_document(self.object_id)

                if newest_doc:
                    self.couchdb_document["_rev"] = latest_rev

        if newest_doc:
            self.handleconflict(newest_doc)
            self.couchdb_document["_rev"] = latest_rev
            return True
        else:
            return False

    def save(self, object_id=None, dbase=None, debug=False, force_save=False, store_in_redis=True):
        """
        save the object, check for conflicsts and resolve them
        @param force_save:
        @type force_save:
        @param object_id: id of object
        @type object_id: string
        @param dbase: database
        @type dbase: CouchDBServer
        @param debug: debug?
        @type debug: bool
        @type store_in_redis: bool
        @return: success
        @rtype: bool
        """
        if store_in_redis:
            rsc = RedisServer(self.get_db().get_namespace())
            rsc.delete(self.object_id)
        self.try_counter += 1
        # something is really wrong, old indexes perhaps? try to delete them
        if self.try_counter > 1000:
            sync_mutex = Mutex(self.dbase, "view_sync", self.dbase.dbname)
            try:
                sync_mutex.acquire_lock()
                self.dbase.delete_document("_design/crypto_data")
            finally:
                sync_mutex.release_lock()

        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if not force_save:
            if not self._data_changed:
                if self.dataloaded:
                    if self.debug:
                        console("SaveObjectCouch:save skip", self.object_id)

                    return True

        if dbase:
            self.dbase = dbase

        if object_id:
            self.object_id = object_id

        if self.dbase is None:
            raise ObjectSaveException("Database variable not set (dbase)", self)

        if not self.__is_valid_object_id(self.object_id):
            raise ObjectIdInvalid("Invalid object-id: %s" % (self.object_id, ))

        for req_item in self.required:
            item = getattr(self, req_item)

            if not item:
                raise ObjectSaveException("required item missing -> " + str(req_item), self)

            if item == "":
                raise ObjectSaveException("required item missing -> " + str(req_item), self)

        self.m_last_changed = time.time()
        latest_rev = None
        seq_rev = self.dbase.run_view("SaveObjectSeq", key=self.object_id, scalar=True)

        if seq_rev is not None:
            if (seq_rev[0] != self.seq) or int(seq_rev[0]) == 0:
                latest_rev = seq_rev[1]
                self.checkforconflicts(latest_rev)
                self.seq = int(seq_rev[0])

        for member in dir(self):
            if member.startswith("m_"):
                if member.endswith("_p64s"):
                    if isinstance(getattr(self, member), dict):
                        adict = getattr(self, member).copy()

                        for key in adict.keys():
                            adict[key] = object_to_pickled_base64(adict[key])

                        self.couchdb_document[member] = adict.copy()
                    else:
                        self.couchdb_document[member] = object_to_pickled_base64(getattr(self, member))
                else:
                    self.couchdb_document[member] = getattr(self, member)

                if "_" + member not in self.att_timestamps:
                    self.update_timestamp("_" + member)

        del_keys = []

        for key in self.couchdb_document:
            if key.startswith("m_"):
                keep = False

                for member in dir(self):
                    if member.startswith("m_"):
                        if key in member:
                            keep = True

                if not keep:
                    del_keys.append(key)

        for key in del_keys:
            del self.couchdb_document[key]
        self.mutation_counter += 1
        self.couchdb_document["att_timestamps"] = self.att_timestamps.copy()
        self.couchdb_document["required"] = self.required
        self.couchdb_document["object_id"] = self.object_id
        self.couchdb_document["object_type"] = self.object_type
        self.couchdb_document["mutation_counter"] = self.mutation_counter
        self.couchdb_document["comment"] = self.comment
        self.couchdb_document["seq"] = self.seq
        self.couchdb_document["_attachments"] = self._attachments

        #noinspection PyUnresolvedReferences
        self.couchdb_document["user_editable"] = self.user_editable.copy()
        try:
            if "_rev" in self.couchdb_document:
                if not self.couchdb_document["_rev"]:
                    del self.couchdb_document["_rev"]

            if latest_rev:
                self._rev = latest_rev
                self.couchdb_document["_rev"] = latest_rev

            mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)

            if mutation_counter:
                if mutation_counter > self.mutation_counter:
                    raise couchdb.ResourceConflict("higher mutation on server")

            doc_id, doc_rev = self.dbase.add_document(self.couchdb_document, doc_id=self.object_id)
            self.couchdb_document["_rev"] = doc_rev
            self._rev = doc_rev
            self._id = self.object_id
        except couchdb.ResourceConflict, ex:
            if ex:
                message = str(ex)

                if len(message) > 0:
                    if not "Document update conflict." in message and not "higher mutation on server" in message:
                        handle_ex(ex, False)

            self.mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)
            # does it still exist?
            object_dicts = self.dbase.get_document(self.object_id, allow_none=True)

            if not object_dicts:
                return False
            self.seq = 0
            self.save(debug=debug)
        self._data_changed = False
        return True

    def put_attachment(self, fp, name=None, mime=None):
        """
        @param fp:
        @type fp:
        @param name:
        @type name:
        @param mime:
        @type mime:
        @raise ObjectSaveException:
        """
        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if self.dbase is None:
            raise ObjectSaveException("Database variable not set (dbase)", self)

        if not self.dataloaded:
            if not self.exists():
                self.save()
            else:
                self.load()
        else:
            mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)

            if mutation_counter:
                if mutation_counter > self.mutation_counter:
                    self.load()
                    # rewind the file

        fp.seek(0)

        if not "_id" in self.couchdb_document:
            self.couchdb_document["_id"] = self.object_id

        if not "_rev" in self.couchdb_document:
            if self._rev:
                self.couchdb_document["_rev"] = self._rev
            else:
                self.save(force_save=True)
                self.couchdb_document["_rev"] = self._rev
        self.dbase.dbase.put_attachment(self.couchdb_document, fp, name, mime)

        rsc = RedisServer(self.get_db().get_namespace())
        rsc.delete(self.object_id)
        self.load()
        #self.set_from_dict(new_doc)
        self.dataloaded = True
        self._data_changed = False
        return True

    def count_attachments(self):
        """
        count_attachments
        """
        if hasattr(self, "_attachments"):
            return len(self._attachments)
        return 0

    def has_attachement(self, name):
        """
        @param name:
        @type name:
        @return: @rtype: @raise ObjectSaveException:
        """
        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if self.dbase is None:
            raise ObjectSaveException("Database variable not set (dbase)", self)

        if name in self._attachments:
            return True
        return False

    def get_attachment(self, name):
        """
        @param name:
        @type name:
        @return: @rtype: @raise ObjectSaveException:
        """
        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if self.dbase is None:
            raise ObjectSaveException("Database variable not set (dbase)", self)

        if not self.dataloaded:
            self.load()
        else:
            mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)

            if mutation_counter:
                if mutation_counter > self.mutation_counter:
                    self.load()

        try:
            att = self.dbase.dbase.get_attachment(self.couchdb_document, name)

            if not att:
                raise SaveObjectAttachmentNotFound("Document is missing attachment")

            return att.read()
        except couchdb.ResourceNotFound, ex:
            raise SaveObjectAttachmentNotFound(ex.message)

    def delete_attachment(self, name):
        """
        @param name:
        @type name:
        @raise ObjectSaveException:
        """
        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if self.dbase is None:
            raise ObjectSaveException("Database variable not set (dbase)", self)

        if not self.dataloaded:
            if not self.load():
                raise ObjectLoadException("cannot load object to delete doc", self)
        else:
            mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)

            if mutation_counter:
                if mutation_counter > self.mutation_counter:
                    self.load()

        self.dbase.dbase.delete_attachment(self.couchdb_document, name)

        rsc = RedisServer(self.get_db().get_namespace())
        rsc.delete(self.object_id)
        self.load()
        return True

    def exists(self, object_id=None, dbase=None):
        """
        does the record exist
        @param object_id: id of object
        @type object_id: string
        @param dbase: database
        @type dbase: CouchDBServer
        """
        if dbase:
            self.dbase = dbase

        if self.dbase is None:
            raise ObjectLoadException("Database variable not set (dbase)", self)

        org_object_id = None

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            org_object_id = self.object_id
            self.object_id = object_id

        if not self.object_id:
            exists = True
        else:
            try:
                if self.object_id in self.get_db().dbase:
                    exists = True
                else:
                    exists = False
            except DocNotFoundException:
                exists = False

        if org_object_id:
            self.object_id = org_object_id

        return exists

    def load(self, object_id=None, dbase=None):
        """
        load the object
        @param object_id: id of object
        @type object_id: string
        @param dbase: database
        @type dbase: CouchDBServer
        @return: success
        @rtype: bool
        """
        self.dataloaded = True

        if dbase:
            self.dbase = dbase

        if self.dbase is None:
            raise ObjectLoadException("Database variable not set (dbase)", self)

        org_object_id = None

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            if self.object_id:
                org_object_id = self.object_id
            self.object_id = object_id

        if not self.object_id:
            raise ObjectLoadException("object_id is not set", self)

        _rev = None
        rsc = RedisServer(self.get_db().get_namespace())
        results_couchdb = rsc.get(self.object_id)

        if not results_couchdb:
            try:
                seq_rev = self.dbase.run_view("SaveObjectSeq", key=self.object_id, scalar=True)
            except Exception, ex:
                console_warning("view", "SaveObjectSeq", str(ex))
                seq_rev = self.dbase.run_view("SaveObjectSeq", key=self.object_id, scalar=True)

            if seq_rev:
                seq = seq_rev[0]
                _rev = seq_rev[1]
                self.seq = seq

        if not results_couchdb and _rev:
            try:
                results_couchdb = self.dbase.get_document(self.object_id)

                rsc = RedisServer(self.get_db().get_namespace())
                rsc.set(self.object_id, results_couchdb)
            except DocNotFoundException:
                results_couchdb = None

        if not results_couchdb:
            if org_object_id:
                self.object_id = org_object_id

            if "_rev" in self.couchdb_document:
                try:
                    seq_rev = self.dbase.run_view("SaveObjectSeq", key=self.object_id, scalar=True)
                except Exception, ex:
                    console_warning("view", "SaveObjectSeq", str(ex))
                    seq_rev = self.dbase.run_view("SaveObjectSeq", key=self.object_id, scalar=True)

                if not seq_rev:
                    seq = 0
                    _rev = None
                else:
                    seq = seq_rev[0]
                    _rev = seq_rev[1]
                self.couchdb_document["_rev"] = _rev
                self._rev = self.couchdb_document["_rev"]
                self.seq = seq
                self._data_changed = False
                return False
            else:
                self._data_changed = False

                if org_object_id:
                    self.object_id = org_object_id

                return False

        if not results_couchdb:
            raise Exception("no results_couchdb")

        self.object_dict = results_couchdb

        if "_rev" in results_couchdb:
            self._rev = results_couchdb["_rev"]

        #noinspection PyUnresolvedReferences
        att_timestamps = copy.deepcopy(self.object_dict["att_timestamps"])
        del self.object_dict["att_timestamps"]
        self.required = self.object_dict["required"]
        del self.object_dict["required"]
        self.object_id = self.object_dict["object_id"]
        self._id = self.object_id
        del self.object_dict["object_id"]
        self.object_type = self.object_dict["object_type"]
        del self.object_dict["object_type"]
        if "mutation_counter" in self.object_dict:
            self.mutation_counter = self.object_dict["mutation_counter"]
            del self.object_dict["mutation_counter"]
        self.comment = self.object_dict["comment"]
        del self.object_dict["comment"]
        if "_attachments" in self.object_dict:
            self._attachments = self.object_dict["_attachments"]
        del self.object_dict["seq"]
        if "user_editable" in self.object_dict:
            self.user_editable = self.object_dict["user_editable"]
            self.user_editable_order = len(self.user_editable)
            del self.object_dict["user_editable"]
        self.set_from_dict(self.object_dict)
        self.att_timestamps = att_timestamps
        self._data_changed = False
        return True

    def collection_ids(self, dbase=None, max_items=-1):
        """
        return all the ids of this type as a list
        @param dbase: database
        @type dbase: CouchDBServer
        @param max_items: number of items, newes first
        @type max_items: int
        """
        if dbase:
            self.dbase = dbase

        if self.dbase is None:
            raise ObjectLoadException("Database variable not set (dbase)", self)

        id_list = []
        lvalue = self.object_id[:self.object_id.rfind("_")]

        if max_items > 0:
            cnt = 0
            id_collection = self.dbase.run_view("SaveObjectCreated")

            for oc in id_collection:
                if "object_id" in oc["value"]:
                    k = oc["value"]["object_id"]

                    if self.object_id:
                        rvalue = k[:k.rfind("_")]

                        if lvalue == rvalue:
                            id_list.append(k)
                            cnt += 1

                if max_items > 0:
                    if cnt >= max_items:
                        break

        else:
            id_collection = self.get_db().get_all_document_ids()

            for k in id_collection:
                if self.object_id:
                    rvalue = k[:k.rfind("_")]

                    if lvalue == rvalue:
                        id_list.append(k)

        return set(id_list)

    def collection(self, dbase=None, warning=True, max_items=-1):
        """
        return all the objects of this type as a list
        @param warning:
        @type warning:
        @param max_items: number of items, newes first
        @type max_items: int
        @param dbase: database
        @type dbase: CouchDBServer
        """
        if dbase:
            self.dbase = dbase
        objs = []

        if warning:
            if max_items > 200:
                if self.count() > 200:
                    try:
                        GenericException("more then 1000 items in collection fetch")
                    except GenericException, ex:
                        console_warning(ex)

        id_collection = self.collection_ids(max_items=max_items)

        for obj_id in id_collection:
            obj = self.__class__(dbase=self.dbase)

            #noinspection PyExceptClausesOrder
            try:
                obj.load(object_id=obj_id)
                objs.append(obj)
            except Exception, e:
                console(str(e))
        objs = sorted(objs, key=lambda k: k.m_created)
        return objs

    def collection_dict_list(self, dbase=None, warning=True, max_items=-1):
        """
        return all the objects of this type as a list
        @param warning:
        @type warning:
        @param max_items:
        @type max_items:
        @param dbase: database
        @type dbase: CouchDBServer
        """
        if dbase:
            self.dbase = dbase
        objs = []

        if warning:
            if max_items > 200:
                if self.count() > 200:
                    console_warning("more then 1000 items in collection fetch")

        for obj_id in self.collection_ids(max_items=max_items):
            obj = self.__class__(dbase=self.dbase)
            try:
                obj.load(object_id=obj_id)
                objs.append(obj.as_dict())
            except DocNotFoundException:
                pass

        objs = sorted(objs, key=lambda k: k["m_created"])
        return objs

    @staticmethod
    def _member_value_match(doc, mv_list, obj):
        """
        @type doc: dict
        @type mv_list: list
        @type obj: SaveObjectCouch, SaveObjectGoogle
        """
        obj.set_from_dict(doc)

        #noinspection PyUnusedLocal
        found_list = [False for i in mv_list]
        cnt = 0

        for member, value in mv_list:
            if obj.get_member(member) == value:
                found_list[cnt] = True
            else:
                found_list[cnt] = False
            cnt += 1
        found = True

        for i in found_list:
            if found:
                found = i

        return found

    def collection_on_member_value(self, mv_list):
        """
        @param mv_list: list with member values in tuple form [("m_name", "John"), ("m_age", 16)]
        @type mv_list: list
        """
        if self.dbase is None:
            raise Exception("database not set")

        objs = []

        for obj_id in self.collection_ids():
            obj = self.__class__(dbase=self.dbase)
            doc = self.dbase.get_document(obj_id)

            if doc:
                found = self._member_value_match(doc, mv_list, obj)

                if found:
                    objs.append(obj)

        return objs

    def exist_on_member_value(self, mv_list):
        """
        @param mv_list: list with member values in tuple form [("m_name", "John"), ("m_age", 16)]
        @type mv_list: list
        @return: bool, str
        """
        if self.dbase is None:
            raise Exception("database not set")

        for obj_id in self.collection_ids():
            obj = self.__class__(dbase=self.dbase)
            doc = self.dbase.get_document(obj_id)

            if doc:
                found = self._member_value_match(doc, mv_list, obj)

                if found:
                    return True, obj.object_id

        return False, ""

    def set_members(self, key, object_dict):
        """
        @param key:
        @type key:
        @param object_dict:
        @type object_dict:
        """
        if key.endswith("_p64s") and not self.raw:
            #if key == "m_aes_encrypted_rsa_private_key_p64s":
            #    pass
            if isinstance(object_dict[key], dict):
                adict = object_dict[key]

                for key2 in adict.keys():
                    adict[key2] = pickled_base64_to_object(adict[key2])

                setattr(self, key, adict)
            else:
                object_dict[key] = pickled_base64_to_object(object_dict[key])
                setattr(self, key, object_dict[key])
        else:
            setattr(self, key, object_dict[key])

    def set_from_dict(self, object_dict):
        """
        set the attributes from a dictionary
        @param object_dict:
        @type object_dict: dict
        """
        for key in object_dict:
            self.set_members(key, object_dict)
            self.couchdb_document[key] = getattr(self, key)
        self._data_changed = False

    def delete(self, dbase=None, object_id=None, force=False):
        """
        delete the object
        @param object_id:
        @type object_id:
        @param force:
        @type force:
        @param dbase: database
        @type dbase: CouchDBServer
        """
        if dbase:
            self.dbase = dbase

        if self.dbase is None:
            raise ObjectDeleteException("Database variable not set (dbase)", self)

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            self.object_id = object_id

        if self.object_type:
            if self.object_type != "SaveObjectCouch":
                if inflection.underscore(self.object_type) not in str(self.object_id):
                    if not force:
                        console("delete other type", self.object_type, self.object_id)

        if not self.dataloaded:
            if not self.load():
                raise ObjectDoesNotExist("can't load this object to delete")

        if not self.object_id:
            raise ObjectIdInvalid("no id given")
        else:
            mutation_counter = self.dbase.run_view("SaveObjectMutationCounter", key=self.object_id, scalar=True)

            if mutation_counter:
                if mutation_counter > self.mutation_counter:
                    self.load()

        if not self._rev:
            raise ObjectDoesNotExist("this object was never there")

        rsc = RedisServer(self.get_db().get_namespace())
        rsc.delete(self.object_id)
        try:
            self.couchdb_document["_id"] = self.object_id
            self.dbase.dbase.delete(self.couchdb_document)
        except couchdb.ResourceConflict:
            self.load()
            try:
                self.dbase.dbase.delete(self.couchdb_document)
            except Exception, e:
                if strcmp(e.message[0], "not_found"):
                    raise ObjectDoesNotExist(self.object_id)

        except Exception, e:
            if strcmp(e.message[0], "not_found"):
                raise ObjectDoesNotExist(self.object_id)

        self.object_id = None
        return True

    def serialize_b64(self):
        """
        @return: base64 representation of object
        @rtype: string
        """
        sdict = self.__dict__
        del sdict["dbase"]
        return object_to_pickled_base64(sdict)

    def as_dict(self):
        """
        as_dict
        """
        instantiating = False

        if not self.object_dict:
            instantiating = True
            self.object_dict = {}

            for m in self.get_list_of_members("m_"):
                self.object_dict[m] = self.get_member(m)

        d = {}

        for k in self.object_dict.keys():
            #if not k.endswith("_p64s"):
            d[k] = self.object_dict[k]

        if "_id" in d:
            d["object_id"] = d["_id"]

        if instantiating:
            self.object_dict = None

        d["fields"] = self.get_user_editable()
        return d


def delete_saveobjects(serverconfig, object_ids, transaction=None):
    """
    @type serverconfig: ServerConfig
    @type object_ids: list, tuple
    @type transaction: googledatastore.Transaction
    """
    rsc = RedisServer(serverconfig.get_namespace())

    for oid in object_ids:
        try:
            obj = rsc.get("gds_key_" + oid)

            if not obj:
                try:
                    obj = gds_get_object_by_id(serverconfig.get_namespace(), oid)
                    obj = obj["keyval"]
                except GoogleDatastoreException, ex:
                    if str("object_id not found") in str(ex.message):
                        pass
                    else:
                        raise ex

            if obj:
                gds_delete_item_on_key(serverconfig.get_namespace(), obj, transaction)
        except ObjectDoesNotExist:
            console("can't delete", oid)


class FillCacheCouch(threading.Thread):
    """
    @param server_ip:
    @type server_ip:
    @param rs_server_list:
    @type rs_server_list:
    """

    def __init__(self, server_ip, rs_server_list, db_name):
        """
        @type server_ip: str
        @type rs_server_list: list
        @type db_name: str
        """
        threading.Thread.__init__(self)
        self.server_ip = server_ip
        self.rs_server_list = rs_server_list
        self.m_db_name = db_name

    def fill_cache(self, db_name):
        """
        @param db_name:
        @type db_name:
        """
        dburl = urljoin(self.server_ip, db_name + "/")
        resource = urljoin(dburl, "_all_docs?include_docs=true")
        data = requests.get(resource).json()
        console("FillCacheCouch", resource)
        rsc = RedisServer(db_name)

        for doc in data["rows"]:
            if "object_id" in doc["doc"]:
                rsc.set(doc["doc"]["object_id"], doc["doc"])

    def run(self):
        """
        run
        """
        if self.m_db_name:
            self.fill_cache(self.m_db_name)
        else:
            for db_name in list(couchdb.Server(self.server_ip)):
                self.fill_cache(db_name)


class OneTimeFunctions(object):
    """
    OneTimeFunctions
    """
    _instance = None
    data = {}

    def __new__(cls, *args, **kwargs):
        """
        @param cls:
        @type cls:
        @param args:
        @type args:
        @param kwargs:
        @type kwargs:
        @return:
        @rtype:
        """
        #noinspection PyProtectedMember
        if not cls._instance:
            #noinspection PyAttributeOutsideInit,PyArgumentList
            cls._instance = super(OneTimeFunctions, cls).__new__(cls, *args, **kwargs)

        return cls._instance

    def fill_redis_couchdb(self, server_ip, rs_server_list, db_name):
        """
        @param db_name:
        @type db_name:
        @param server_ip:
        @type server_ip:
        @param rs_server_list:
        @type rs_server_list:
        """
        if "fill_redis_" + db_name not in self.data:
            fc = FillCacheCouch(server_ip, rs_server_list, db_name)
            fc.start()
            self.data["fill_redis_" + db_name] = True
            #else:
            #    console_warning("fill_redis_" + db_name + " already called")

    def sync_views(self, dbase, rs_server_list):
        """
        @param dbase:
        @type dbase:
        @param rs_server_list:
        @type rs_server_list:
        """
        if "sync_views" not in self.data:
            sync_all_views(dbase, rs_server_list)
            self.data["sync_views"] = True
            #else:
            #    console_warning("sync_views already called")


def load_save_object_by_id(obj_id, cls, serverconfig, cls_params):
    """
    @type obj_id: unicode, str
    @type cls: class
    @type serverconfig: ServerConfig
    @type cls_params: None, list
    """
    params = [serverconfig]

    if isinstance(cls_params, list):
        for param in cls_params:
            params.append(param)

    obj = apply(cls, tuple(params))

    #noinspection PyExceptClausesOrder
    try:
        obj.load(object_id=obj_id)
        return obj
    except Exception, e:
        console(str(e))


class SaveObjectGoogle(object):

    """ Base class for saving python objects to googles datastore """

    def get_serverconfig(self):
        """
        get_serverconfig
        @return: @rtype: @raise Exception:
        """
        if self.serverconfig is None:
            raise Exception()

        return self.serverconfig

    def event(self, *args, **kwargs):
        """
        @param args:
        @type args:
        @param kwargs:
        @type kwargs:
        """
        kwargs["line_num_only"] = 3
        self.serverconfig.events.event(*args, **kwargs)

    def get_namespace(self):
        """
        get_namespace
        """
        if self.serverconfig is None:
            raise Exception("no serverconfig")

        return self.serverconfig.namespace

    def __init__(self, serverconfig=None, object_id=None, comment="a save object", transaction=None):
        """
        @param serverconfig: database
        @type serverconfig: ServerConfig
        @param object_id: id of object
        @type object_id: string or None
        @param comment: a comment
        @type comment: string
        """
        self.debug = False
        self.raw = False
        self.dataloaded = False
        self.object_dict = None
        self.object_id = None
        self.object_type = None
        self.comment = None
        self._rev = ""
        self._id = None
        self._data_changed = False
        self.comment = comment
        self.serverconfig = serverconfig
        self.couchdb_document = {"doctype": "cb_object"}
        self.entity_key = None

        if not self.object_type:
            self.object_type = self.get_object_type()
        self.object_id = object_id
        self.m_created = time.time()
        self.m_last_changed = time.time()

        if not hasattr(self, "required"):
            self.required = []
        self.changed_without_property = []
        self.mutation_counter = 0
        self.att_timestamps = {}
        self.user_editable_order = 0
        self.user_editable = {}

        if not hasattr(self, "m_extra_indexed_keys"):
            self.m_extra_indexed_keys = []
        self.transaction = transaction

        def decode_b64(v):
            """
            decode_b64
            @param v:
            @type v:
            """
            #noinspection PyBroadException
            try:
                v2 = pickled_base64_to_object(v)
            except:
                v2 = v

            return v2

        for member in dir(self):
            if member.startswith("m_"):
                self.add_property(member)

        for member in dir(self):
            if member.endswith("_p64s"):
                setattr(self, member, decode_b64(getattr(self, member)))

        self._data_changed = False

        if not hasattr(self, "object_id"):
            self.object_id = None

        if self.object_id and not self.__is_valid_object_id(self.object_id):
            raise ObjectIdInvalid("Invalid object-id: %s" % (self.object_id, ))

        if not self.object_id:
            self.object_id = make_object_id_string(self.object_type)
            self._data_changed = True

    @staticmethod
    def __is_valid_object_id(object_id):
        """
        __is_valid_object_id
        @param object_id:
        @type object_id:
        """
        if not isinstance(object_id, str) and not isinstance(object_id, unicode):
            return False
        return True

    def lifetime(self):
        """
        lifetime
        @return: @rtype:
        """
        return time.time() - self.m_created

    def lifetime_last_update(self):
        """
        lifetime_last_update
        @return: @rtype:
        """
        return time.time() - self.m_last_changed

    def add_user_editable(self, name, obj_type, required, label=None):
        """
        @param name:
        @type name:
        @param obj_type:
        @type obj_type:
        @param required:
        @type required:
        @param label:
        @type label:
        """
        if name in self.required:
            required = True

        if not label:
            label = name.replace("m_", "", 1).replace("_", " ").capitalize()
        d = {"member": name,
             "type": obj_type,
             "required": required,
             "label": label,
             "order": self.user_editable_order}

        if obj_type == "password":
            d["member_again"] = name + "_again"

        if obj_type == "bool":
            d["required"] = False
        self.user_editable_order += 1

        #noinspection PyUnresolvedReferences
        self.user_editable[name] = d

    def get_user_editable(self):
        """
        get_user_editable
        @return: @rtype: dict
        """
        return self.user_editable

    def set_required(self, required_member_list):
        """
        @param required_member_list: "m_" class attributes which are required for save
        @type required_member_list: list
        @return: nothing
        @rtype: None
        """
        self.required = required_member_list

    def update_timestamp(self, attribute):
        """
        update a timestamp for a member attribute
        @param attribute: attribute to stamp
        @type attribute: string
        """
        if not hasattr(self, "att_timestamps"):
            self.att_timestamps = {}
        self.att_timestamps[attribute] = time.time()

    def add_property(self, name):
        """
        generate a property with a timestamp entry
        @param name: name of the property
        @type name: string
        """
        if not hasattr(self, name):
            raise Exception("cannot add property for " + str(name))

        if name.startswith("_"):
            return

        setattr(self, "_" + name, getattr(self, name))

        #noinspection PyShadowingNames
        def getf(self):
            """
            getf
            """
            obj = self.getattrc("_" + name)

            if isinstance(obj, dict):
                self._data_changed = True
            elif isinstance(obj, list):
                self._data_changed = True
            elif isinstance(obj, tuple):
                self._data_changed = True

            return obj

        #noinspection PyShadowingNames
        def setf(self, value):
            """
            @param self:
            @type self:
            @param value:
            @type value:
            """
            if hasattr(self, "_" + name):
                old_value = self.getattrc("_" + name)

                if old_value == value:
                    return

            self.setattrc("_" + name, value)

        setattr(self.__class__, name, property(getf, setf))

    def getattrc(self, name):
        """
        get an attribute by name
        @param name: name of the prop
        @type name: string
        """
        if not hasattr(self, name):
            setattr(self, name, None)

        return getattr(self, name)

    def setattrc(self, name, value):
        """ set an attribute by name and update timestamp
        @param name:
        @type name:
        @param value:
        @type value:
        """
        self._data_changed = True

        if not hasattr(self, name):
            setattr(self, name, None)

        self.update_timestamp(name)
        setattr(self, name, value)

    def get_object_type(self):
        """ get the object type in a string format """
        object_type = str(repr(self))

        if "." in object_type:
            split = object_type.split(".")
            object_type = split[len(split) - 1]

        if " " in object_type:
            object_type = object_type.split(" ")[0]
            object_type = object_type.strip()
            return object_type
        else:
            return None

    def get_member(self, key):
        """
        @param key: key -> m_key
        @type key: str
        """
        retval = getattr(self, key)
        return retval

    def _remove_member(self, key):
        """
        remove a member from class an initial value
        @param key:
        @type key:
        """
        key = key.strip()

        if "_" + key in self.att_timestamps:
            del self.att_timestamps["_" + key]

        if hasattr(self, key):
            delattr(self, key)
            self._data_changed = True

    def count_members(self):
        """
        count all the database members
        """
        cnt = 0

        for member in dir(self):
            if member.startswith("m_"):
                cnt += 1

        return cnt

    def get_list_of_members(self, prefix):
        """
        get a list of members
        @param prefix:
        @type prefix:
        """
        ml = []

        for member in dir(self):
            if member.startswith(prefix):
                ml.append(member)

        return ml

    def handleconflict(self, newest_doc):
        """
        conflict resolution by comparing the timestamps of the member attributes
        @param newest_doc: document
        @type newest_doc: dict
        """
        localmembers = dir(self)

        if "mutation_counter" not in newest_doc:
            self.mutation_counter = 0
        else:
            self.mutation_counter = newest_doc["mutation_counter"]

        for mymember in localmembers:
            if mymember.startswith("m_"):
                key = mymember
                mymember_timestamp = None
                newermember_timestamp = None

                if "_" + key in self.att_timestamps:
                    mymember_timestamp = self.att_timestamps["_" + key]

                if "_" + key in newest_doc["att_timestamps"]:
                    newermember_timestamp = newest_doc["att_timestamps"]["_" + key]
                    #self.debug_timestamp(debug, key, mymember_timestamp, newermember_timestamp, newest_doc)
                overwrite = True

                if mymember_timestamp:
                    if newermember_timestamp <= mymember_timestamp:
                        overwrite = False

                if overwrite:
                    if "_" + key not in newest_doc["att_timestamps"]:
                        newest_doc["att_timestamps"]["_" + key] = time.time()
                    self.att_timestamps["_" + key] = newest_doc["att_timestamps"]["_" + key]

                    if key.endswith("_p64s"):
                        #if key == "m_aes_encrypted_rsa_private_key_p64s":
                        #    pass
                        if key in newest_doc:
                            if isinstance(newest_doc[key], dict):
                                adict = newest_doc[key]

                                for key2 in adict.keys():
                                    adict[key2] = pickled_base64_to_object(adict[key2])

                                setattr(self, "_" + key, adict)
                            else:
                                newest_doc[key] = pickled_base64_to_object(newest_doc[key])
                                setattr(self, "_" + key, newest_doc[key])
                        else:
                            setattr(self, "_" + key, None)
                    else:
                        if key in newest_doc:
                            setattr(self, "_" + key, newest_doc[key])
                        else:
                            setattr(self, "_" + key, None)

    def save(self, object_id=None, serverconfig=None, force_consistency=False, store_in_redis=True, force_save=True, transaction=None, use_datastore=True):
        """
        @type object_id: str
        @type serverconfig: ServerConfig
        @type force_consistency: bool
        @type store_in_redis: bool
        @type force_save: bool
        @type transaction: googledatastore.Transaction
        @type use_datastore: bool
        """
        if transaction is not None:
            self.transaction = transaction

        if store_in_redis:
            rsc = RedisServer(self.get_serverconfig().get_namespace())
            rsc.delete(self.object_id)

        if not self.object_id:
            raise ObjectSaveException("Object id not set (self.object_id)", self)

        if not force_save:
            if not self._data_changed:
                if self.dataloaded:
                    if self.debug:
                        console("SaveObjectCouch:save skip", self.object_id)

                    return True

        if serverconfig:
            self.serverconfig = serverconfig

        if object_id:
            self.object_id = object_id

        if self.serverconfig is None:
            raise ObjectSaveException("Database variable not set (serverconfig)", self)

        if not self.__is_valid_object_id(self.object_id):
            raise ObjectIdInvalid("Invalid object-id: %s" % (self.object_id, ))

        for req_item in self.required:
            item = getattr(self, req_item)

            if not item:
                raise ObjectSaveException("required item missing -> " + str(req_item), self)

            if item == "":
                raise ObjectSaveException("required item missing -> " + str(req_item), self)

        if use_datastore:
            current_mutation_counter = gds_get_scalar_value(self.get_serverconfig().get_namespace(), unicode(self.object_type), unicode("object_id"), unicode(self.object_id), "mutation_counter")

            if current_mutation_counter > self.mutation_counter:
                newest_doc = gds_get_object_by_fieldvalue(self.get_serverconfig().get_namespace(), unicode(self.object_type), unicode("object_id"), unicode(self.object_id))
                newest_doc = self.record_cleaned(newest_doc)

                if newest_doc:
                    self.handleconflict(newest_doc)
                    #current_mutation_counter = gds_get_scalar_value(self.object_type, "object_id", self.object_id, "mutation_counter")

        self.m_last_changed = time.time()

        for member in dir(self):
            if member.startswith("m_"):
                if member.endswith("_p64s"):
                    if isinstance(getattr(self, member), dict):
                        adict = getattr(self, member).copy()

                        for key in adict.keys():
                            adict[key] = object_to_pickled_base64(adict[key])

                        self.couchdb_document[member] = adict.copy()
                    else:
                        self.couchdb_document[member] = object_to_pickled_base64(getattr(self, member))
                else:
                    self.couchdb_document[member] = getattr(self, member)

        del_keys = []

        for key in self.couchdb_document:
            if key.startswith("m_"):
                keep = False

                for member in dir(self):
                    if member.startswith("m_"):
                        if key in member:
                            keep = True

                if not keep:
                    del_keys.append(key)

        for key in del_keys:
            del self.couchdb_document[key]
        self.mutation_counter += 1
        self.couchdb_document["object_id"] = self.object_id
        self.couchdb_document["object_type"] = self.object_type
        self.couchdb_document["mutation_counter"] = self.mutation_counter
        self.couchdb_document["comment"] = self.comment
        self.couchdb_document["att_timestamps"] = self.att_timestamps
        rsc = RedisServer(self.get_serverconfig().get_namespace())
        rsc.set(self.object_id, self.couchdb_document)

        if not use_datastore:
            sync_mutex = Mutex("store_id_saveobject", self.serverconfig.get_namespace())
            try:
                sync_mutex.acquire_lock()
                ids_ot = self.get_serverconfig().rs_get("saveobject_ids_" + self.object_type)

                if not ids_ot:
                    ids_ot = FastList()
                    ids_ot.add(self.object_id)
                else:
                    ids_ot.add(self.object_id)

                self.get_serverconfig().rs_set("saveobject_ids_" + self.object_type, ids_ot)
            finally:
                sync_mutex.release_lock()

        if "keyval" in self.couchdb_document:
            del self.couchdb_document["keyval"]
        indexed_keys = ["object_id", "object_type", "doctype", "mutation_counter", "m_created", "m_last_changed"]

        for k in self.couchdb_document:
            if self.couchdb_document[k] is None:
                self.couchdb_document[k] = ""
            elif isinstance(self.couchdb_document[k], str):
                self.couchdb_document[k] = unicode(self.couchdb_document[k])
            elif isinstance(self.couchdb_document[k], long):
                self.couchdb_document[k] = int(self.couchdb_document[k])
            elif isinstance(self.couchdb_document[k], dict):
                self.couchdb_document[k] = unicode(object_to_pickled_base64(self.couchdb_document[k]))
            elif isinstance(self.couchdb_document[k], float):
                pass
            elif isinstance(self.couchdb_document[k], tuple):
                pass
            elif isinstance(self.couchdb_document[k], list):
                pass
            elif isinstance(self.couchdb_document[k], int):
                pass
            elif isinstance(self.couchdb_document[k], unicode):
                pass
            else:
                raise TypeError(str(type(self.couchdb_document[k])) + " is not JSON serializable")

            if isinstance(self.couchdb_document[k], unicode):
                if len(self.couchdb_document[k]) > 500:
                    if k in indexed_keys:
                        self.couchdb_document[k] = self.couchdb_document[k].encode("utf8")

        if self.m_extra_indexed_keys:
            indexed_keys.extend(self.m_extra_indexed_keys)

        for k in indexed_keys:
            if len(str(self.couchdb_document[k])) > 500:
                console_warning("indexed key bigger then 500", k, len(str(self.couchdb_document[k])))

        if use_datastore:
            self.entity_key = gds_add_saveobject(self.serverconfig.get_namespace(), self.object_type, self.object_id, self.couchdb_document, indexed_keys=indexed_keys, commit=self.transaction, rsc=rsc)

            if force_consistency:
                cnt = 0
                saved = False

                if self.transaction:
                    saved = True

                while not saved:
                    newdict = gds_get_object_by_key(self.get_serverconfig().get_namespace(), self.entity_key)

                    if newdict:
                        if newdict["mutation_counter"] >= self.mutation_counter:
                            saved = True

                    if cnt > 10:
                        time.sleep(0.2)
                    cnt += 1

                    if cnt > 20:
                        raise GoogleDatastoreException("save force_consistency error")

        self.dataloaded = True
        self._data_changed = False
        return True

    def exists(self, object_id=None, serverconfig=None, use_datastore=True):
        """
        @type object_id: str, None
        @type serverconfig: ServerConfig, None
        @type use_datastore: bool
        """
        if serverconfig:
            self.serverconfig = serverconfig

        if self.serverconfig is None:
            raise ObjectLoadException("Database variable not set (serverconfig)", self)

        org_object_id = None

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            org_object_id = self.object_id
            self.object_id = object_id
        exists = False
        rsc = RedisServer(self.get_serverconfig().get_namespace())

        if rsc.get(self.object_id):
            exists = True

        if use_datastore:
            try:
                kind = self.object_type
                filterfield = "object_id"
                filterfieldval = self.object_id
                results_couchdb = gds_get_object_by_fieldvalue(self.get_serverconfig().get_namespace(), unicode(kind), unicode(filterfield), unicode(filterfieldval))

                if results_couchdb:
                    exists = True
                else:
                    exists = False
            except DocNotFoundException:
                exists = False

        if org_object_id:
            self.object_id = org_object_id

        return exists

    @staticmethod
    def record_cleaned(results_couchdb):
        """
        @type results_couchdb: dict
        """
        bstyle = get_b64pstyle()

        for k in results_couchdb:
            if isinstance(results_couchdb[k], str) or isinstance(results_couchdb[k], unicode):
                if bstyle in results_couchdb[k]:
                    results_couchdb[k] = pickled_base64_to_object(results_couchdb[k])

        return results_couchdb

    def load(self, object_id=None, serverconfig=None, force_load=False, use_datastore=True):
        """
        @type object_id: str, None
        @type serverconfig: ServerConfig, None
        @type force_load: bool
        @type use_datastore: bool
        """
        self.dataloaded = True

        if serverconfig:
            self.serverconfig = serverconfig

        if self.serverconfig is None:
            raise ObjectLoadException("Database variable not set (serverconfig)", self)

        org_object_id = None

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            if self.object_id:
                org_object_id = self.object_id
            self.object_id = object_id

        if not self.object_id:
            raise ObjectLoadException("object_id is not set", self)

        rsc = RedisServer(self.get_serverconfig().get_namespace())
        results_couchdb = rsc.get(self.object_id)

        if not results_couchdb:
            if use_datastore:
                kind = self.object_type
                filterfield = "object_id"
                filterfieldval = self.object_id

                for i in range(0, 20):
                    if i > 15:
                        time.sleep(0.1)

                    results_couchdb = gds_get_object_by_fieldvalue(self.get_serverconfig().get_namespace(), unicode(kind), unicode(filterfield), unicode(filterfieldval))

                    if results_couchdb:
                        break

                    if not force_load:
                        break

                if not results_couchdb:
                    if org_object_id:
                        self.object_id = org_object_id

                    return False

                results_couchdb = self.record_cleaned(results_couchdb)
                rsc = RedisServer(self.get_serverconfig().get_namespace())
                rsc.set(self.object_id, results_couchdb)
            else:
                if not results_couchdb:
                    return False

        self.object_dict = results_couchdb

        #noinspection PyUnresolvedReferences
        #noinspection PyTypeChecker
        self.object_id = results_couchdb["object_id"]
        self._id = self.object_id
        del self.object_dict["object_id"]
        #noinspection PyTypeChecker
        self.object_type = results_couchdb["object_type"]
        del self.object_dict["object_type"]
        if "mutation_counter" in self.object_dict:
            #noinspection PyTypeChecker
            self.mutation_counter = results_couchdb["mutation_counter"]
            del self.object_dict["mutation_counter"]
            #noinspection PyTypeChecker
        #noinspection PyTypeChecker
        self.comment = results_couchdb["comment"]
        del self.object_dict["comment"]
        if "user_editable" in results_couchdb:
            #noinspection PyTypeChecker
            self.user_editable = results_couchdb["user_editable"]
            self.user_editable_order = len(self.user_editable)
            del self.object_dict["user_editable"]
        self.set_from_dict(self.object_dict)
        self._data_changed = False
        return True

    def collection_ids(self, serverconfig=None, max_items=-1):
        """
        @type serverconfig: ServerConfig
        @type max_items: int
        """
        if serverconfig:
            self.serverconfig = serverconfig

        if self.serverconfig is None:
            raise ObjectLoadException("Database variable not set (serverconfig)", self)

        kind = self.object_type
        l = gds_get_scalar_list(self.get_serverconfig().get_namespace(), kind=unicode(kind), member=unicode("keyval"))

        id_list = set([gds_get_key_name(x) for x in l])

        if max_items > 0:
            return set(list(id_list)[:max_items])
        return id_list

    def collection(self, serverconfig=None, warning=True, max_items=-1, cls_params=None, use_datastore=True):
        """
        @type serverconfig: ServerConfig, None
        @type warning: bool
        @type max_items: int
        @type cls_params: None, list
        @type use_datastore: bool
        """
        if serverconfig:
            self.serverconfig = serverconfig

        if warning:
            if max_items > 200:
                if self.count() > 200:
                    try:
                        GenericException("more then 1000 items in collection fetch")
                    except GenericException, ex:
                        console_warning(ex)

        rsc = RedisServer(self.get_serverconfig().get_namespace())
        id_collection = []

        if not use_datastore and rsc:
            ids_ot = self.get_serverconfig().rs_get("saveobject_ids_" + self.object_type)

            if ids_ot:
                id_collection = ids_ot.list()
        else:
            id_collection = self.collection_ids(max_items=max_items)
        objs = []

        if rsc:
            id_collection_mem = list(id_collection)

            for oid in id_collection_mem:
                results_couchdb = rsc.get(oid)

                if results_couchdb:
                    id_collection.remove(oid)
                    params = [self.get_serverconfig()]

                    if isinstance(cls_params, list):
                        for param in cls_params:
                            params.append(param)

                    obj = apply(self.__class__, tuple(params))

                    #noinspection PyTypeChecker
                    obj.set_from_dict(results_couchdb)
                    objs.append(obj)

        if len(id_collection) > 0:
            objs_id_params = [(obj_id, self.__class__, self.serverconfig, cls_params) for obj_id in id_collection]
            ids = smp_apply(load_save_object_by_id, objs_id_params, dummy_pool=True)
            objs.extend(ids)
        objs = sorted(objs, key=lambda k: k.m_created)
        return objs

    def collection_dict_list(self, serverconfig=None, warning=True, max_items=-1, cls_params=None):
        """
        @type serverconfig: ServerConfig, None
        @type warning: bool
        @type max_items: int
        @type cls_params: None, list
        """
        if serverconfig:
            self.serverconfig = serverconfig
        objs = []

        if warning:
            if max_items > 200:
                if self.count() > 200:
                    console_warning("more then 1000 items in collection fetch")

        id_collection = self.collection_ids(max_items=max_items)

        objs_id_params = [(obj_id, self.__class__, self.serverconfig, cls_params) for obj_id in id_collection]
        objso = smp_apply(load_save_object_by_id, objs_id_params, dummy_pool=True)

        for obj in objso:
            objs.append(obj.as_dict())
        objs = sorted(objs, key=lambda k: k["m_created"])
        return objs

    @staticmethod
    def _member_value_match(doc, mv_list, obj):
        """
        @type doc: dict
        @type mv_list: list
        @type obj: SaveObjectGoogle
        """
        obj.set_from_dict(doc)

        #noinspection PyUnusedLocal
        found_list = [False for i in mv_list]
        cnt = 0

        for member, value in mv_list:
            if obj.get_member(member) == value:
                found_list[cnt] = True
            else:
                found_list[cnt] = False
            cnt += 1
        found = True

        for i in found_list:
            if found:
                found = i

        return found

    def collection_on_member_value(self, mv_list):
        """
        @param mv_list: list with member values in tuple form [("m_name", "John"), ("m_age", 16)]
        @type mv_list: list
        """
        if self.serverconfig is None:
            raise Exception("database not set")

        objs = []

        for obj_id in self.collection_ids():
            obj = self.__class__(serverconfig=self.serverconfig)
            doc = gds_get_object_by_fieldvalue(self.get_serverconfig().get_namespace(), unicode(obj.object_type), unicode("object_id"), unicode(obj_id))

            if doc:
                found = self._member_value_match(doc, mv_list, obj)

                if found:
                    objs.append(obj)

        return objs

    def set_members(self, key, object_dict):
        """
        @param key:
        @type key:
        @param object_dict:
        @type object_dict:
        """
        if key.endswith("_p64s") and not self.raw:
            #if key == "m_aes_encrypted_rsa_private_key_p64s":
            #    pass
            if isinstance(object_dict[key], dict):
                adict = object_dict[key]

                for key2 in adict.keys():
                    adict[key2] = pickled_base64_to_object(adict[key2])

                setattr(self, key, adict)
            else:
                object_dict[key] = pickled_base64_to_object(object_dict[key])
                setattr(self, key, object_dict[key])
        else:
            if isinstance(object_dict[key], str) or isinstance(object_dict[key], unicode):
                if get_b64pstyle() in object_dict[key]:
                    object_dict[key] = pickled_base64_to_object(object_dict[key])

            setattr(self, key, object_dict[key])

    def set_from_dict(self, object_dict):
        """
        set the attributes from a dictionary
        @param object_dict:
        @type object_dict: dict
        """
        for key in object_dict:
            if not strcmp(key, "keyval"):
                self.set_members(key, object_dict)
                self.couchdb_document[key] = getattr(self, key)

        self._data_changed = False

    def delete(self, serverconfig=None, object_id=None, force_consistency=False, force=False, transaction=None, delete_from_datastore=True):
        """
        @type serverconfig: ServerConfig
        @type object_id: str
        @type force_consistency: bool
        @type force: bool
        @type transaction: googledatastore.Transaction
        @type delete_from_datastore: bool
        """
        if transaction is not None:
            self.transaction = transaction

        if serverconfig:
            self.serverconfig = serverconfig

        if self.serverconfig is None:
            raise ObjectDeleteException("Database variable not set (serverconfig)", self)

        if object_id:
            if not self.__is_valid_object_id(object_id):
                raise ObjectIdInvalid("Invalid object-id: %s" % (object_id, ))

            self.object_id = object_id

        if not self.dataloaded:
            if not self.load():
                raise ObjectDoesNotExist("can't load this object to delete")

        if self.object_type:
            if self.object_type != "SaveObjectGoogle":
                if inflection.underscore(self.object_type) not in str(self.object_id):
                    if not force:
                        console("delete other type", self.object_type, self.object_id)

        if not self.object_id:
            raise ObjectIdInvalid("no id given")

        rsc = RedisServer(self.get_serverconfig().get_namespace())
        rsc.delete(self.object_id)
        self.couchdb_document["_id"] = self.object_id
        kind = self.object_type
        filterfield = "object_id"
        filterfieldval = self.object_id

        if delete_from_datastore:
            if self.entity_key is None:
                gds_delete_items_on_fieldvalue(self.get_serverconfig().get_namespace(), unicode(kind), unicode(filterfield), unicode(filterfieldval), commit=self.transaction)
            else:
                gds_delete_item_on_key(self.get_serverconfig().get_namespace(), self.entity_key, transaction, force_consistency)

            if force_consistency:
                if self.transaction is None:
                    for i in range(0, 20):
                        if self.exists():
                            if i > 10:
                                time.sleep(0.1)
                        else:
                            break

        else:
            sync_mutex = Mutex("store_id_saveobject", self.serverconfig.get_namespace())
            try:
                sync_mutex.acquire_lock()
                ids_ot = self.get_serverconfig().rs_get("saveobject_ids_" + self.object_type)
                ids_ot.delete(self.object_id)
                self.get_serverconfig().rs_set("saveobject_ids_" + self.object_type, ids_ot)
            finally:
                sync_mutex.release_lock()

        self.object_id = None
        return True

    def serialize_b64(self):
        """
        @return: base64 representation of object
        @rtype: string
        """
        sdict = self.__dict__
        del sdict["serverconfig"]
        return object_to_pickled_base64(sdict)

    def as_dict(self):
        """
        as_dict
        """
        instantiating = False

        if not self.object_dict:
            instantiating = True
            self.object_dict = {}

            for m in self.get_list_of_members("m_"):
                self.object_dict[m] = self.get_member(m)

        d = {}

        for k in self.object_dict.keys():
            if self.object_dict[k] is None:
                self.object_dict[k] = ""
            elif isinstance(self.object_dict[k], str):
                pass
            elif isinstance(self.object_dict[k], long):
                self.object_dict[k] = int(self.object_dict[k])
            elif isinstance(self.object_dict[k], dict):
                self.object_dict[k] = unicode(object_to_pickled_base64(self.object_dict[k]))
            elif isinstance(self.object_dict[k], float):
                pass
            elif isinstance(self.object_dict[k], tuple):
                pass
            elif isinstance(self.object_dict[k], list):
                pass
            elif isinstance(self.object_dict[k], int):
                pass
            elif isinstance(self.object_dict[k], unicode):
                pass
            elif isinstance(self.object_dict[k], datastore.Key):
                self.object_dict[k] = unicode(object_to_pickled_base64(self.object_dict[k]))
            else:
                raise TypeError(str(type(self.object_dict[k])) + " is not JSON serializable")

            d[k] = self.object_dict[k]

        if "_id" in d:
            d["object_id"] = d["_id"]

        if instantiating:
            self.object_dict = None

        d["fields"] = self.get_user_editable()

        if "object_id" not in d:
            d["object_id"] = self.object_id

        return d

    def count(self, serverconfig=None):
        """
        count the number of docs
        @param serverconfig: database
        @type serverconfig: ServerConfig, None
        """
        if serverconfig:
            self.serverconfig = serverconfig

        if self.serverconfig is None:
            raise ObjectLoadException("Database variable not set (serverconfig)", self)

        items = gds_get_scalar_list(self.get_serverconfig().get_namespace(), kind=unicode(self.object_type), member=unicode("object_id"))
        val = len(items)

        if val == 0:
            id_collection = self.get_serverconfig().rs_get("saveobject_ids_" + self.object_type)

            if id_collection:
                val = id_collection.size()

        if not val:
            return 0
        return val

    def get_sequence_number(self):
        """
        get_sequence_number
        @return: @rtype:
        """
        return self.mutation_counter

    def start_transaction(self):
        """
        start_transaction
        """
        self.transaction = gds_commit_transaction()
        return self.transaction

    def commit(self):
        """
        commit
        """
        gds_commit(self.transaction)
        self.transaction = None
        cnt = 0
        saved = False

        if self.entity_key:
            while not saved:
                newdict = gds_get_object_by_key(self.get_serverconfig().get_namespace(), self.entity_key)

                if newdict:
                    if newdict["mutation_counter"] >= self.mutation_counter:
                        saved = True

                if cnt > 10:
                    time.sleep(0.2)
                cnt += 1

                if cnt > 20:
                    raise GoogleDatastoreException("save force_consistency error")

    def rollback(self):
        """
        rollback
        """
        gds_rollback(self.transaction)
        self.transaction = None


class SaveEvent(SaveObjectGoogle):
    """
    SaveEvent
    """

    def __init__(self, serverconfig, userid="", operation="", dataid="", extra_data=""):
        """
        @type serverconfig: ServerConfig
        @type userid: str
        @type operation: str
        @type dataid: str
        @type extra_data: str
        """
        self.m_userid = userid
        self.m_operation = operation
        self.m_on_dataid = dataid
        self.m_extra_data = extra_data
        super(SaveEvent, self).__init__(serverconfig=serverconfig, comment="user does something to a dataobject")
        self.object_id += ":" + inflection.underscore(self.m_operation).replace("_", "-")
