#!/usr/bin/env python
# -*- coding: utf-8 -*-


class AuthenticationFailed(Exception):
    pass

class NotAuthenticated(Exception):
    pass

class InvalidCredentialFile(Exception):
    pass

class UploadFailed(Exception):
    pass

class InvalidCDNMetada(Exception):
    pass

class NotCDNEnabled(Exception):
    pass

class FileNotFound(Exception):
    pass

class MissingName(Exception):
    pass

class CDNFailed(Exception):
    pass

class NoSuchContainer(Exception):
    pass

class NoSuchObject(Exception):
    pass
