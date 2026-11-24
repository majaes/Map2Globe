# -*- coding: utf-8 -*-
"""Run pip with TLS limited to 1.2.

Some networks / antivirus / firewalls stall the TLS 1.3 handshake, which makes pip fail with
"Could not find a version that satisfies the requirement ..." (no versions found). Forcing TLS 1.2
for this pip process works around it. Usage (with the QGIS Python):

    & "C:\\Program Files\\QGIS 4.0.1\\bin\\python-qgis.bat" dev\\pip_tls12.py install --user pytest pytest-qgis
"""
import runpy
import ssl
import sys

_original_new = ssl.SSLContext.__new__


def _new(cls, *args, **kwargs):
    context = _original_new(cls, *args, **kwargs)
    # Only plain SSLContext objects: pip's truststore subclass wraps one internally, which is patched too.
    if cls is ssl.SSLContext:
        context.maximum_version = ssl.TLSVersion.TLSv1_2
    return context


ssl.SSLContext.__new__ = _new

sys.argv = ["pip"] + sys.argv[1:]
runpy.run_module("pip", run_name="__main__")
