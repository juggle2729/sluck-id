# -*- coding: utf-8 -*-

import Crypto
import json
from Crypto.Hash import MD5
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Hash import SHA
from Crypto.Hash import HMAC
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as PKCS1_V1_5_Sign
from Crypto.Cipher import DES
from Crypto.Util.asn1 import DerSequence
import base64


class CryptoHelper:
    @staticmethod
    def importKey(content):
        return RSA.importKey(base64.b64decode(content))

    @staticmethod
    def importKeyFile(fileName):
        file = open(fileName)
        pem = file.read()
        file.close()
        return RSA.importKey(pem)

    @staticmethod
    def importPEMX509File(fileName):
        file = open(fileName)
        pem = file.read()
        file.close()
        lines = pem.replace(" ", '').split()
        der = base64.b64decode(''.join(lines[1:-1]))
        cert = DerSequence()
        cert.decode(der)
        tbsCertificate = DerSequence()
        tbsCertificate.decode(cert[0])
        subjectPublicKeyInfo = tbsCertificate[6]
        return RSA.importKey(subjectPublicKeyInfo)

    @staticmethod
    def _pkcs7padding(data, blockSize):
        """
        size 16
        999999999=>9999999997777777
        """
        size = blockSize
        count = size - len(data) % size
        if count:
            data += (chr(count) * count)
        return data

    @staticmethod
    def _depkcs7padding(data, blockSize):
        newdata = ''
        for c in data:
            if ord(c) > blockSize:
                newdata += c
        return newdata

    def aes_encrypt(self, data, key):

        """
        @summary:
            1. pkcs7padding
            2. aes encrypt
            3. base64 encrypt
        @return:
            string
        """
        cipher = AES.new(key)
        return base64.b64encode(cipher.encrypt(self._pkcs7padding(data, AES.block_size)))

    def aes_decrypt(self, data, key):
        """  
        1. base64 decode  
        2. aes decode  
        3. dpkcs7padding  
        """
        cipher = AES.new(key)
        return self._depkcs7padding(cipher.decrypt(base64.b64decode(data)), AES.block_size)

    def rsa_encrypt(self, data, key):
        '''
        1. rsa encrypt
        2. base64 encrypt
        '''
        cipher = PKCS1_v1_5.new(key)
        return base64.b64encode(cipher.encrypt(data))

    def rsa_decrypt(self, data, key):
        cipher = PKCS1_v1_5.new(key)
        return cipher.decrypt(base64.b64decode(data), Random.new().read(15 + SHA.digest_size))

    def md5(self, data, upper=False, binary=False):
        h = MD5.new()
        h.update(data)
        value = h.hexdigest()
        if upper:
            value = value.upper()
        if binary:
            value = h.digest()

        return value

    def sign(self, data, key):
        hash = MD5.new(data)
        signature = PKCS1_V1_5_Sign.new(key)
        return base64.b64encode(signature.sign(hash))

    def checksign(self, data, data_sign, key):
        binary_sign = base64.b64decode(data_sign)
        verifier = PKCS1_V1_5_Sign.new(key)
        return verifier.verify(MD5.new(data), binary_sign)

    def segmentation_data(self, reqData, platpkey):
        data = reqData.split('&')
        if len(data) != 3:
            print "Response data error: " + reqData.encode('utf-8')
            return None
        tdata = data[0].split('=')
        transdata = tdata[1].replace('+', ' ')
        tsign = data[1].split('=')
        sign = tsign[1] + "="
        tsigntype = data[2].split('=')
        signtype = tsigntype[1]
        result = self.checksign(transdata, sign, platpkey)
        return {'transdata': transdata, 'sign': sign, 'sign_type': signtype}

    def des_encrypt(self, data, key):
        cipher = DES.new(key)
        return base64.b64encode(cipher.encrypt(self._pkcs7padding(data, DES.block_size)))

    def des_decrypt(self, data, key):
        cipher = DES.new(key)
        return self._depkcs7padding(cipher.decrypt(base64.b64decode(data)), DES.block_size)

    def hmac_sign(self, data, key):
        hash = HMAC.new(key)
        hash.update(data)
        return hash.hexdigest()
