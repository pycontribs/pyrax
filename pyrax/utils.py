#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import os
import tempfile


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


class SelfDeletingTempfile(object):
    name = None

    def __enter__(self):
        fd, self.name = tempfile.mkstemp()
        os.close(fd)
        return self.name

    def __exit__(self, type, value, traceback):
        os.unlink(self.name)
