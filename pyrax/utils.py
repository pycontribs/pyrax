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
import time
import types
import uuid

import prettytable
try:
    import pudb
except ImportError:
    import pdb as pudb
trace = pudb.set_trace

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
        f1 = file(os.path.join(tmpdir, "my_file.txt", "w")
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


def get_checksum(content):
    """
    Returns the MD5 checksum in hex for the given content. If 'content'
    is a file-like object, the content will be obtained from its read()
    method.
    """
    if hasattr(content, "read"):
        pos = content.tell()
        content.seek(0)
        txt = content.read()
        content.seek(pos)
    else:
        txt = content
    md = hashlib.md5()
    md.update(txt)
    return md.hexdigest()


def random_name(length=20):
    """Generates a random name; useful for testing."""
    base_chars = string.ascii_letters
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
    Returns the total bytes for the specified, optionally ignoring
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
            for pattern in ignore:
                if fnmatch.fnmatch(pth, pattern):
                    paths.remove(pth)
                    break
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


def wait_until(obj, att, desired, interval=5, attempts=10, verbose=False):
    """
    When changing the state of an object, it will commonly be in a
    transitional state until the change is complete. This will reload
    the object ever `interval` seconds, and check its `att`
    attribute. If it is equal to `desired`, this will return a value
    of True. If not, it will re-try a maximum of `attempts` times; if
    the attribute has not reached the desired value by then, this will
    return False. If `attempts` is 0, this will loop infinitely until
    the attribute matches. If `verbose` is True, each attempt will print
    out the current value of the watched attribute and the time that has
    elapsed since the original request.

    Note that `desired` can be a list of values; if the attribute becomes
    equal to any of those values, this will return True.
    """
    if not isinstance(desired, (list, tuple)):
        desired = [desired]
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
                obj = obj.manager.get(obj.id)
            except AttributeError:
                # punt
                raise exc.NoReloadError("The 'wait_until' method is not supported for '%s' objects." % obj.__class__)
        attval = getattr(obj, att)
        if verbose:
            elapsed = time.time() - start
            print "Current value of %s: %s (elapsed: %4.1f seconds)" % (att, attval, elapsed)
        if attval in desired:
            return True
        time.sleep(interval)
        attempt += 1
    return False


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
            raise exc.InvalidDateTimeString("The supplied value '%s' does not match either of the formats "
                    "'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD'." % val)
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
