# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utilities for memcache encryption and integrity check.
"""

import base64
import functools
import hashlib
import json
import os

# make sure pycrypt is available
try:
    from Crypto.Cipher import AES
except ImportError:
    AES = None


# prefix marker indicating data is HMACed (signed by a secret key)
MAC_MARKER = '{MAC:SHA1}'
# prefix marker indicating data is encrypted
ENCRYPT_MARKER = '{ENCRYPT:AES256}'


class InvalidMacError(Exception):
    """ raise when unable to verify MACed data

    This usually indicates that data had been expectedly modified in memcache.

    """
    pass


class DecryptError(Exception):
    """ raise when unable to decrypt encrypted data

    """
    pass


class CryptoUnavailableError(Exception):
    """ raise when Python Crypto module is not available

    """
    pass


def assert_crypto_availability(f):
    """ Ensure Crypto module is available. """

    @functools.wraps(f)
    def wrapper(*args, **kwds):
        if AES is None:
            raise CryptoUnavailableError()
        return f(*args, **kwds)
    return wrapper


def generate_aes_key(token, secret):
    """ Generates and returns a 256 bit AES key, based on sha256 hash. """
    return hashlib.sha256(token + secret).digest()


def compute_mac(token, serialized_data):
    """ Computes and returns the base64 encoded MAC. """
    return hash_data(serialized_data + token)


def hash_data(data):
    """ Return the base64 encoded SHA1 hash of the data. """
    return base64.b64encode(hashlib.sha1(data).digest())


def sign_data(token, data):
    """ MAC the data using SHA1. """
    mac_data = {}
    mac_data['serialized_data'] = json.dumps(data)
    mac = compute_mac(token, mac_data['serialized_data'])
    mac_data['mac'] = mac
    md = MAC_MARKER + base64.b64encode(json.dumps(mac_data))
    return md


def verify_signed_data(token, data):
    """ Verify data integrity by ensuring MAC is valid. """
    if data.startswith(MAC_MARKER):
        try:
            data = data[len(MAC_MARKER):]
            mac_data = json.loads(base64.b64decode(data))
            mac = compute_mac(token, mac_data['serialized_data'])
            if mac != mac_data['mac']:
                raise InvalidMacError('invalid MAC; expect=%s, actual=%s' %
                                      (mac_data['mac'], mac))
            return json.loads(mac_data['serialized_data'])
        except:
            raise InvalidMacError('invalid MAC; data appeared to be corrupted')
    else:
        # doesn't appear to be MACed data
        return data


@assert_crypto_availability
def encrypt_data(token, secret, data):
    """ Encryptes the data with the given secret key. """
    iv = os.urandom(16)
    aes_key = generate_aes_key(token, secret)
    cipher = AES.new(aes_key, AES.MODE_CFB, iv)
    data = json.dumps(data)
    encoded_data = base64.b64encode(iv + cipher.encrypt(data))
    encoded_data = ENCRYPT_MARKER + encoded_data
    return encoded_data


@assert_crypto_availability
def decrypt_data(token, secret, data):
    """ Decrypt the data with the given secret key. """
    if data.startswith(ENCRYPT_MARKER):
        try:
            # encrypted data
            encoded_data = data[len(ENCRYPT_MARKER):]
            aes_key = generate_aes_key(token, secret)
            decoded_data = base64.b64decode(encoded_data)
            iv = decoded_data[:16]
            encrypted_data = decoded_data[16:]
            cipher = AES.new(aes_key, AES.MODE_CFB, iv)
            decrypted_data = cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data)
        except:
            raise DecryptError('data appeared to be corrupted')
    else:
        # doesn't appear to be encrypted data
        return data
