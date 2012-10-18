#!/usr/bin/env python
# -*- coding: utf-8 -*-


class AmbiguousEndpoints(Exception):
     pass

class AuthenticationFailed(Exception):
     pass

class AuthorizationFailure(Exception):
     pass

class AuthSystemNotFound(Exception):
     pass

class CDNFailed(Exception):
     pass

class EndpointNotFound(Exception):
     pass

class FileNotFound(Exception):
     pass

class FolderNotFound(Exception):
     pass

class InvalidCDNMetada(Exception):
     pass

class InvalidConfigurationFile(Exception):
     pass

class InvalidCredentialFile(Exception):
     pass

class InvalidUploadID(Exception):
     pass

class MissingName(Exception):
     pass

class NoSuchContainer(Exception):
     pass

class NoSuchObject(Exception):
     pass

class NotAuthenticated(Exception):
     pass

class NotCDNEnabled(Exception):
     pass

class NoTokenLookupException(Exception):
     pass

class Unauthorized(Exception):
     pass

class UploadFailed(Exception):
     pass

def from_response(resp, body):
     pass

