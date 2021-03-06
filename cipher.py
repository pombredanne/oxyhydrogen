#!/usr/bin/env python
# encoding: utf8

import socket
import sys
from subprocess import Popen, PIPE

from OpenSSL import SSL

CIPHERS = None

def cipers_level(cipher):
    global CIPHERS
    if CIPHERS is None:
        CIPHERS = {}
        for strength in ['HIGH', 'MEDIUM', 'LOW', 'EXPORT']:
            p = Popen(['openssl', 'ciphers', strength], stdout=PIPE)
            for c in p.stdout.readline()[:-1].split(':'):
                CIPHERS[c] = strength
    return CIPHERS.get(cipher, "?")


def audit(cipher):
    c = cipher.split('-')
    bad = ["DSS", "3DES", "RC4", "RC2", "DES", "NULL", "EXP", "EXP1024"]
    for b in bad:
        if b in c:
            return "↓    "
    if c[1] == "DSS":
        return "↓    "
    score = 0
    if c[0] == "DHE" or c[0] == "EDH":
        score += 1
    elif c[0] == "ECDHE":
        score += 2
    if "GCM" in c:
        score += 1
    if "SHA384" in c:
        score += 1
    if score == 0:
        return "→    "
    return (u"↑" * score).ljust(5, u" ")


def verify_cb(conn, cert, errnum, depth, ok):
    # This obviously has to be updated
    #print 'Got certificate: %s' % cert.get_subject()
    return ok


print "OpenSSL", SSL.OPENSSL_VERSION_NUMBER

for method_name, method in [("SSLv23", SSL.SSLv23_METHOD),
                            ("SSLv3", SSL.SSLv3_METHOD),
                            ("TLSv1", SSL.TLSv1_METHOD)]:
    print "\n#", method_name
    ctx = SSL.Context(method)
    # FIXME crash with Openssl v1
    #ctx.set_verify(SSL.VERIFY_PEER, verify_cb)  # Demand a certificate

    sock = SSL.Connection(ctx, socket.socket(socket.AF_INET,
                                             socket.SOCK_STREAM))
    try:
        sock.connect((sys.argv[1], int(sys.argv[2])))

        sock.do_handshake()
    except SSL.Error:
        print "Not handled"
        continue

    ciphers = sock.get_cipher_list()
    sock.close()

    for cipher in ciphers:
        ctx.set_cipher_list(cipher)
        sock = SSL.Connection(ctx, socket.socket(socket.AF_INET,
                                                 socket.SOCK_STREAM))
        sock.connect((sys.argv[1], int(sys.argv[2])))
        try:
            sock.do_handshake()
            print "✓", audit(cipher), "[%s]" % cipers_level(cipher).ljust(6), cipher
            sock.close()
        except SSL.Error:
            #print "✗", audit(cipher), cipher
            pass

    #print sock.get_peer_cert_chain()
    #print sock.get_cipher_list()
    #print dir(sock.get_context())
