#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch
import hashlib
import os
import shutil
import tempfile

import pyrax.exceptions as exc


class SelfDeletingTempfile(object):
    name = None

    def __enter__(self):
        fd, self.name = tempfile.mkstemp()
        os.close(fd)
        return self.name

    def __exit__(self, type, value, traceback):
        os.unlink(self.name)


class SelfDeletingTempDirectory(object):
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
