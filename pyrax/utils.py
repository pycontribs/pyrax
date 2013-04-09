#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import fnmatch
import hashlib
import os
import random
import re
import shutil
import string
import sys
import tempfile
import threading
import time
import types

import prettytable
try:
    import pudb
except ImportError:
    import pdb as pudb
trace = pudb.set_trace

import pyrax
import pyrax.exceptions as exc



class SelfDeletingTempfile(object):
    """
    Convenience class for dealing with temporary files.

    The temp file is created in a secure fashion, and is
    automatically deleted when the context manager exits.

    Usage:

    \code
    with SelfDeletingTempfile() as tmp:
        tmp.write( ... )
        some_func(tmp)
    # More code
    # At this point, the tempfile has been erased.
    \endcode
    """
    name = None

    def __enter__(self):
        fd, self.name = tempfile.mkstemp()
        os.close(fd)
        return self.name

    def __exit__(self, type, value, traceback):
        os.unlink(self.name)


class SelfDeletingTempDirectory(object):
    """
    Convenience class for dealing with temporary folders and the
    files within them.

    The temp folder is created in a secure fashion, and is
    automatically deleted when the context manager exits, along
    with any files that may be contained within. When you
    instantiate this class, you receive the full path to the
    temporary directory.

    Usage:

    \code
    with SelfDeletingTempDirectory() as tmpdir:
        f1 = open(os.path.join(tmpdir, "my_file.txt", "w")
        f1.write("blah...")
        f1.close()
        some_func(tmpdir)
    # More code
    # At this point, the directory 'tmpdir' has been deleted,
    # as well as the file 'f1' within it.
    \endcode
    """
    name = None

    def __enter__(self):
        self.name = tempfile.mkdtemp()
        return self.name

    def __exit__(self, type, value, traceback):
        shutil.rmtree(self.name)


def get_checksum(content, encoding="utf8"):
    """
    Returns the MD5 checksum in hex for the given content. If 'content'
    is a file-like object, the content will be obtained from its read()
    method. If 'content' is a file path, that file is read and its
    contents used. Otherwise, 'content' is assumed to be the string whose
    checksum is desired. If the content is unicode, it will be encoded
    using the specified encoding.
    """
    if hasattr(content, "read"):
        pos = content.tell()
        content.seek(0)
        txt = content.read()
        content.seek(pos)
    elif os.path.isfile(content):
        with open(content, "rb") as ff:
            txt = ff.read()
    else:
        txt = content
    md = hashlib.md5()
    try:
        md.update(txt)
    except UnicodeEncodeError:
        md.update(txt.encode(encoding))
    return md.hexdigest()


def random_name(length=20, ascii_only=False):
    """
    Generates a random name; useful for testing.

    By default it will return an encoded string containing
    unicode values up to code point 1000. If you only
    need or want ASCII values, pass True to the
    ascii_only parameter.
    """
    if ascii_only:
        base_chars = string.ascii_letters
    else:
        def get_char():
            return unichr(random.randint(32, 1000))
        base_chars = u"".join([get_char() for ii in xrange(length)])
    mult = (length / len(base_chars)) + 1
    chars = base_chars * mult
    return "".join(random.sample(chars, length))


def coerce_string_to_list(val):
    """
    For parameters that can take either a single string or a list of strings,
    this function will ensure that the result is a list containing the passed
    values.
    """
    if val:
        if not isinstance(val, (list, tuple)):
            val = [val]
    else:
        val = []
    return val


def folder_size(pth, ignore=None):
    """
    Returns the total bytes for the specified path, optionally ignoring
    any files which match the 'ignore' parameter. 'ignore' can either be
    a single string pattern, or a list of such patterns.
    """
    if not os.path.isdir(pth):
        raise exc.FolderNotFound

    ignore = coerce_string_to_list(ignore)

    def get_size(total, root, names):
        paths = [os.path.realpath(os.path.join(root, nm)) for nm in names]
        for pth in paths[::-1]:
            if not os.path.exists(pth):
                paths.remove(pth)
            if os.path.isdir(pth):
                # Don't count folder stat sizes
                paths.remove(pth)
            if match_pattern(pth, ignore):
                paths.remove(pth)
        total[0] += sum(os.stat(pth).st_size for pth in paths)

    # Need a mutable to pass
    total = [0]
    os.path.walk(pth, get_size, total)
    return total[0]


def add_method(obj, func, name=None):
    """Adds an instance method to an object."""
    if name is None:
        name = func.func_name
    method = types.MethodType(func, obj, obj.__class__)
    setattr(obj, name, method)


class _WaitThread(threading.Thread):
    """
    Threading class to wait for object status in the background. Note that
    verbose will always be False for a background thread.
    """
    def __init__(self, obj, att, desired, callback, interval, attempts,
            verbose, verbose_atts):
        self.obj = obj
        self.att = att
        self.desired = desired
        self.callback = callback
        self.interval = interval
        self.attempts = attempts
        self.verbose = verbose
        threading.Thread.__init__(self)

    def run(self):
        """Starts the thread."""
        resp = _wait_until(obj=self.obj, att=self.att,
                desired=self.desired, callback=None,
                interval=self.interval, attempts=self.attempts,
                verbose=False, verbose_atts=None)
        self.callback(resp)


def wait_until(obj, att, desired, callback=None, interval=5, attempts=10,
        verbose=False, verbose_atts=None):
    """
    When changing the state of an object, it will commonly be in a transitional
    state until the change is complete. This will reload the object ever
    `interval` seconds, and check its `att` attribute. If the desired value of
    the attribute is reached, the updated object is returned. If not, it will
    re-try a maximum of `attempts` times; if the attribute has not reached the
    desired value by then, this method will exit and return None. If `attempts`
    is 0, this will loop forever until the attribute matches. If `verbose` is
    True, each attempt will print out the current value of the watched
    attribute and the time that has elapsed since the original request. Also,
    if `verbose_atts` is specified, the values of those attributes will also
    be output. If `verbose` is False, then `verbose_atts` has no effect.

    Note that `desired` can be a list of values; if the attribute becomes equal
    to any of those values, this will succeed. For example, when creating a new
    cloud server, it will initially have a status of 'BUILD', and you can't
    work with it until its status is 'ACTIVE'. However, there might be a
    problem with the build process, and the server will change to a status of
    'ERROR'. So for this case you need to set the `desired` parameter to
    `['ACTIVE', 'ERROR']`. If you simply pass 'ACTIVE' as the desired state,
    this will loop indefinitely if a build fails, as the server will never
    reach a status of 'ACTIVE'.

    Since this process of waiting can take a potentially long time, and will
    block your program's execution until the desired state of the object is
    reached, you may specify a callback function. The callback can be any
    callable that accepts a single parameter; the parameter it receives will be
    either the updated object (success), or None (failure). If a callback is
    specified, the program will return immediately after spawning the wait
    process in a separate thread.
    """
    if callback:
        waiter = _WaitThread(obj=obj, att=att, desired=desired, callback=callback,
                interval=interval, attempts=attempts, verbose=verbose,
                verbose_atts=verbose_atts)
        waiter.start()
        return waiter
    else:
        return _wait_until(obj=obj, att=att, desired=desired, callback=None,
                interval=interval, attempts=attempts, verbose=verbose,
                verbose_atts=verbose_atts)


def _wait_until(obj, att, desired, callback, interval, attempts, verbose,
        verbose_atts):
    """
    Loops until either the desired value of the attribute is reached, or the
    number of attempts is exceeded.
    """
    if not isinstance(desired, (list, tuple)):
        desired = [desired]
    if verbose_atts is None:
        verbose_atts = []
    if not isinstance(verbose_atts, (list, tuple)):
        verbose_atts = [verbose_atts]
    infinite = (attempts == 0)
    attempt = 0
    start = time.time()
    while infinite or (attempt < attempts):
        try:
            obj.reload()
        except AttributeError:
            # This will happen with cloudservers and cloudfiles, which
            # use different client/resource classes.
            try:
                # For servers:
                obj.get()
            except AttributeError:
                try:
                    # For other objects that don't support .get() or .reload()
                    obj = obj.manager.get(obj.id)
                except AttributeError:
                    # punt
                    raise exc.NoReloadError("The 'wait_until' method is not"
                                            " supported for '%s' objects."
                                            % obj.__class__)
        attval = getattr(obj, att)
        if verbose:
            elapsed = time.time() - start
            msgs = ["Current value of %s: %s (elapsed: %4.1f seconds)" % (
                    att, attval, elapsed)]
            for vatt in verbose_atts:
                vattval = getattr(obj, vatt, None)
                msgs.append("%s=%s" % (vatt, vattval))
            print " ".join(msgs)
        if attval in desired:
            return obj
        time.sleep(interval)
        attempt += 1
    return None


def iso_time_string(val, show_tzinfo=False):
    """
    Takes either a date, datetime or a string, and returns the standard ISO
    formatted string for that date/time, with any fractional second portion
    removed.
    """
    if not val:
        return ""
    if isinstance(val, basestring):
        dt = None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.datetime.strptime(val, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise exc.InvalidDateTimeString("The supplied value '%s' does not "
              "match either of the formats 'YYYY-MM-DD HH:MM:SS' or "
              "'YYYY-MM-DD'." % val)
    else:
        dt = val
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.fromordinal(dt.toordinal())
    has_tz = (dt.tzinfo is not None)
    if show_tzinfo and has_tz:
        # Need to remove the colon in the TZ portion
        ret = "".join(dt.isoformat().rsplit(":", 1))
    elif show_tzinfo and not has_tz:
        ret = "%s+0000" % dt.isoformat().split(".")[0]
    elif not show_tzinfo and has_tz:
        ret = dt.isoformat()[:-6]
    elif not show_tzinfo and not has_tz:
        ret = dt.isoformat().split(".")[0]
    return ret


def get_id(id_or_obj):
    """
    Returns the 'id' attribute of 'id_or_obj' if present; if not,
    returns 'id_or_obj'.
    """
    if isinstance(id_or_obj, (basestring, int)):
        # It's an ID
        return id_or_obj
    try:
        return id_or_obj.id
    except AttributeError:
        return id_or_obj


def match_pattern(nm, patterns):
    """
    Compares `nm` with the supplied patterns, and returns True if it matches
    at least one.

    Patterns are standard file-name wildcard strings, as defined in the
    `fnmatch` module. For example, the pattern "*.py" will match the names
    of all Python scripts.
    """
    patterns = coerce_string_to_list(patterns)
    for pat in patterns:
        if fnmatch.fnmatch(nm, pat):
            return True
    return False


def env(*args, **kwargs):
    """
    Returns the first environment variable set
    if none are non-empty, defaults to "" or keyword arg default
    """
    for arg in args:
        value = os.environ.get(arg, None)
        if value:
            return value
    return kwargs.get("default", "")


def unauthenticated(fnc):
    """
    Adds 'unauthenticated' attribute to decorated function.
    Usage:
        @unauthenticated
        def mymethod(fnc):
            ...
    """
    fnc.unauthenticated = True
    return fnc


def isunauthenticated(fnc):
    """
    Checks to see if the function is marked as not requiring authentication
    with the @unauthenticated decorator. Returns True if decorator is
    set to True, False otherwise.
    """
    return getattr(fnc, "unauthenticated", False)


def safe_issubclass(*args):
    """Like issubclass, but will just return False if not a class."""
    try:
        if issubclass(*args):
            return True
    except TypeError:
        pass
    return False


def import_class(import_str):
    """Returns a class from a string including module and class."""
    mod_str, _sep, class_str = import_str.rpartition(".")
    __import__(mod_str)
    return getattr(sys.modules[mod_str], class_str)


# http://code.activestate.com/recipes/
#   577257-slugify-make-a-string-usable-in-a-url-or-filename/
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.

    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    _slugify_strip_re = re.compile(r"[^\w\s-]")
    _slugify_hyphenate_re = re.compile(r"[-\s]+")
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore")
    value = unicode(_slugify_strip_re.sub("", value).strip().lower())
    return _slugify_hyphenate_re.sub("-", value)
