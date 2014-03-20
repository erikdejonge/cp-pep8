# coding=utf-8
"""
Python encryption utility library, a wrapper around PyCrypto. And a save-able user object.
This source code is property of Active8 BV
Copyright (C)
Erik de Jonge <erik@a8.nl>
Actve8 BV
Rotterdam
www.a8.nl
"""
import re
import os
import sys
import tempfile
import time
import zlib
import math
import base64
import cPickle
import mimetypes
import unicodedata
import random
import multiprocessing
from cStringIO import StringIO
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import HMAC, SHA512, SHA
import crypto_data
from crypto_data import pickled_base64_to_object, object_b64_safe, ServerConfig, b64_object_safe, get_named_temporary_file, cleanup_tempfiles
from crypto_data import console_warning, Mutex, console, smp_apply, gibberish, SaveObjectGoogle
from crypto_data import gcs_delete_from_gcloud, gcs_read_from_gcloud, gcs_write_to_gcloud
from crypto_data import gds_get_dict_list, strcmp, get_file_size, gds_get_ids, gds_delete_items_on_fieldvalue


def get_random_data(size):
    """
    @type size: int
    """
    print "crypto_api:42", "hello"
    return Random.new().read(size)


def get_random_data_aes_blocksize():
    """
    get_random_data_aes_blocksize
    """
    return Random.new().read(AES.block_size)


def mix_match(s, reverse=False):
    """
    @type s: str
    @type reverse: bool
    """
    if reverse:
        return "".join([x[1] for x in map(''.join, zip(*[iter(s)] * 2))])

    r = base64.encodestring(get_random_data(len(s) * 2))

    if len(r) > len(s):
        r = r[:len(s)]
        return "".join([x[0] + x[1] for x in zip(r, s)])
    else:
        raise Exception("not enough random")


def generate_password(size):
    """
    @type size: int
    """
    Random.atfork()

    def filter_chars(password_string):
        """
        @type password_string: str
        """
        npwd = ""

        for c in password_string:
            if c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@":
                npwd += c

        return npwd

    pwd = filter_chars(base64.encodestring(get_random_data(size)))

    while len(pwd) < size:
        pwd += filter_chars(base64.encodestring(get_random_data(size)))

    return pwd[:size]


def get_pronounceable_password(wordcount=2, digitcount=2):
    """
    @type wordcount: int
    @type digitcount: int
    """
    numbermax = 10 ** digitcount
    password = '-'.join(gibberish(wordcount))

    if digitcount >= 1:
        password += "-" + str(int(random.random() * numbermax))

    return password


def password_derivation(key, salt, size=32):
    """
    @type key: str
    @type salt: str
    @type size: int
    """
    iterations = 1000
    return PBKDF2(key, salt, size, count=iterations)


def log(msg):
    """
    log a message in a dict to see all characters
    @param msg: log msg
    @type msg: string
    """
    spl = str({"msg": msg}).replace("{'msg': '", "").replace("'}", "").split(":")

    for i in spl:
        if i != spl[len(spl) - 1]:
            print "crypto_api:130", "\t"
        else:
            print "crypto_api:132", i, "\t"
    return


class EncryptException(Exception):
    """
    EncryptException
    """
    pass


def encrypt(key, data, data_is_list=False, salt_secret=None, base64data=False, initialization_vector=None):
    """
    @type key: str
    @type data: str, list
    @type data_is_list: bool
    @type salt_secret: str, None
    @type base64data: bool
    @type initialization_vector: str, None
    """
    Random.atfork()

    if isinstance(data, int):
        raise EncryptException("encrypt: can only encrypt list or str")

    if not key:
        if not salt_secret[0]:
            raise EncryptException("encrypt data: no password or secret given")

    if data is None:
        raise EncryptException("encrypt: data is None")
    # enhance secret
    if salt_secret:
        salt = salt_secret[0]
        secret = salt_secret[1]
    else:
        salt = get_random_data(32)
        secret = password_derivation(key, salt)
    # create a cipher object using the random secret
    if not initialization_vector:
        try:
            initialization_vector = get_random_data_aes_blocksize()
        except AssertionError:
            Random.atfork()
            initialization_vector = get_random_data_aes_blocksize()

    cipher = AES.new(secret, AES.MODE_CFB, IV=initialization_vector)

    if data_is_list:
        data_hash = make_secure_checksum(data[0], secret)
        encoded_data = []

        if not isinstance(data, list):
            raise EncryptException("can only encrypt lists")

        for ddata in data:
            if base64data:
                encoded_data.append(base64.encodestring(cipher.encrypt(ddata)))
            else:
                encoded_data.append(cipher.encrypt(ddata))

    else:
        data_hash = make_secure_checksum(data, secret)
        encoded_data = cipher.encrypt(data)

        if base64data:
            encoded_data = base64.encodestring(encoded_data)

    encoded_hash = make_secure_checksum(encoded_data, secret)

    if base64data:
        initialization_vector = base64.encodestring(initialization_vector)
    encrypted_data_dict = {"salt": salt,
                           "hash": data_hash,
                           "initialization_vector": initialization_vector,
                           "encoded_data": encoded_data}

    if len(data) > 2:
        if encoded_hash == data_hash:
            console_warning(str(data[0:100]))
            raise EncryptException("data is not encrypted " + str(data[0:100]))

    return encrypted_data_dict


class EncryptionHashMismatch(Exception):
    """
    raised when the hash of the decrypted data doesn't match the hash of the original data

    """
    pass


def decrypt(key, encrypted_data_dict, data_is_list=False, secret=None, hashcheck=True):
    """
    @type key: str
    @type encrypted_data_dict: dict
    @type data_is_list: bool
    @type secret: str, None
    @type hashcheck: bool
    """
    # one-liners to encrypt/encode and decrypt/decode a str
    # encrypt with AES, encode with base64
    # enhance secret
    if not secret:
        if encrypted_data_dict["salt"]:
            secret = password_derivation(key, encrypted_data_dict["salt"])
        else:
            secret = key
            # create a cipher object using the random secret

    if 16 != len(encrypted_data_dict["initialization_vector"]):
        raise Exception("initialization_vector len is not 16")

    cipher = AES.new(secret, AES.MODE_CFB, IV=encrypted_data_dict["initialization_vector"])

    if data_is_list:
        decoded = []

        if not isinstance(encrypted_data_dict["encoded_data"], list):
            raise Exception("can only encrypt lists")

        for data in encrypted_data_dict["encoded_data"]:
            dec_data = cipher.decrypt(data)
            decoded.append(dec_data)
    else:
        dec_data = cipher.decrypt(encrypted_data_dict["encoded_data"])
        decoded = dec_data

    if data_is_list:
        data_hash = make_secure_checksum(decoded[0], secret)
    else:
        data_hash = make_secure_checksum(decoded, secret)

    if "hash" in encrypted_data_dict and hashcheck:
        if data_hash != encrypted_data_dict["hash"]:
            raise EncryptionHashMismatch("the decryption went wrong, hash didn't match")

    return decoded


def make_hash_hmac(data, secret):
    """
    @type data: str
    @type secret: str
    """
    if secret is None:
        raise PasswordException("make_hash_hmac: no secret given")

    if len(secret) < 6:
        raise PasswordException("make_hash_hmac: secret less then 6")

    hmac = HMAC.new(str(secret), digestmod=SHA512)
    hmac.update(data)
    return hmac.hexdigest()


def make_hash_hmac_lowercase(data, secret):
    """
    @type data: str
    @type secret: str
    """
    if secret is None:
        raise PasswordException("make_hash_hmac_lowercase: no secret given")

    if len(secret) < 6:
        raise PasswordException("make_hash_hmac_lowercase: secret less then 6")

    data = str(data).lower()
    hmac = HMAC.new(secret, digestmod=SHA512)
    hmac.update(data)
    return hmac.hexdigest()


def make_hash(data):
    """
    @type data: str
    """
    sha = SHA512.new(data)
    return sha.hexdigest()


def make_hash_list(data_list):
    """
    @type data_list: list
    """
    sha = SHA512.new()

    for data in data_list:
        sha.update(data)

    return sha.hexdigest()


def make_checksum(data):
    """
    @type data: str, dict, list
    """
    try:
        if isinstance(data, list):
            data = str(data)
        elif isinstance(data, dict):
            data = str(data)
        elif isinstance(data, int):
            data = str(data)

        return str(zlib.adler32(data))
    except OverflowError:
        return base64.encodestring(str(SHA.new(data).hexdigest())).strip().rstrip("=")


def make_secure_checksum(data, secret):
    """
    @type secret: str
    @type data: str
    """
    checksum = make_checksum(data)
    return make_hash_hmac(checksum, secret)


def sign(private_key, data):
    """ hash data and sign the hash
    @param private_key:
    @type private_key:
    @param data:
    @type data:
    """
    Random.atfork()
    private_key = private_key.strip()
    ahash = make_hash(data)
    private_key = RSA.importKey(private_key)
    return private_key.sign(ahash, get_random_data(32))


def verify(public_key, data, signature):
    """ hash data and verify against signature
    @param public_key:
    @type public_key:
    @param data:
    @type data:
    @param signature:
    @type signature:
    """
    public_key = public_key.strip()
    ahash = make_hash(data)
    public_key = RSA.importKey(public_key)
    return public_key.verify(ahash, signature)


class PasswordException(Exception):
    """ password has doesn't match the stored hash """
    pass


class RSAException(Exception):
    """ password has doesn't match the stored hash """
    pass


class TestClassPerson(object):
    """
    Person
    """
    m_naam = ""
    m_age = None


def encrypt_object(key, obj, salt_secret=None):
    """ convert to base64 and encrypt
    @param key:
    @type key:
    @param obj:
    @type obj:
    @param salt_secret:
    @type salt_secret:
    """
    Random.atfork()
    base_t = (get_random_data(32), encrypt(key, cPickle.dumps(obj, cPickle.HIGHEST_PROTOCOL), salt_secret=salt_secret))
    return base64.b64encode(cPickle.dumps(base_t))


def decrypt_object(key, obj_string, secret=None):
    """ encrypted base64 to object
    @param key:
    @type key:
    @param obj_string:
    @type obj_string:
    @param secret:
    @type secret:
    """
    base_t = cPickle.loads(base64.b64decode(obj_string))
    obj = cPickle.loads(decrypt(key, base_t[1], secret=secret))
    return obj


class PasswordStoreError(Exception):
    """
    PasswordStoreError
    """
    pass


class CryptoUserPassword(SaveObjectGoogle):
    """
    CryptoUserPassword
    """

    def __init__(self, serverconfig, user_object_id=None, data_object_id=None, password=None):
        """
        @type serverconfig: ServerConfig
        @type user_object_id: str, None
        @type data_object_id: str, None
        @type password: str, None
        """
        self.m_extra_indexed_keys = ["m_user_object_id", "m_data_object_id"]

        if serverconfig is None:
            pass

        passwords = []

        if user_object_id:
            passwords = serverconfig.gds_run_view(self.get_object_type(), "m_user_object_id", user_object_id, "")
        elif data_object_id:
            passwords = serverconfig.gds_run_view(self.get_object_type(), "m_data_object_id", data_object_id, "")
        loaded = False

        for pw in passwords:
            if pw["m_data_object_id"] == data_object_id:
                super(CryptoUserPassword, self).__init__(serverconfig, object_id=pw["object_id"])
                self.load()
                loaded = True

        if not loaded:
            super(CryptoUserPassword, self).__init__(serverconfig)
        self.m_user_object_id = user_object_id
        self.m_data_object_id = data_object_id
        self.m_password_p64s = password

    def save(self, object_id=None, serverconfig=None, force_consistency=False, store_in_memcached=True, force_save=True, transaction=None, use_datastore=True):
        """
        @type object_id: str, None
        @type serverconfig: ServerConfig, None
        @type force_consistency: bool
        @type store_in_memcached: bool
        @type force_save: bool
        @type transaction: str, None
        @type use_datastore: bool
        """
        if object_id:
            self.object_id = object_id

        super(CryptoUserPassword, self).save(self.object_id, serverconfig, force_consistency=force_consistency, force_save=force_save, transaction=transaction, use_datastore=use_datastore)
        self._remove_obsolete_passwords(300)

    def _remove_obsolete_passwords(self, wait_since_last_update):
        """
        remove_obsolete_passwords
        """
        obsolete = []
        oids = gds_get_ids(self.get_serverconfig())

        oids = [x.lower().strip() for x in oids]
        for pw in self.collection():
            if pw.lifetime_last_update() > wait_since_last_update:
                dataid = pw.m_data_object_id.lower().strip()

                if dataid not in oids:
                    obsolete.append(pw.object_id)

        smp_apply(gds_delete_items_on_fieldvalue, [(self.serverconfig.get_namespace(), "CryptoUserPassword", "object_id", oid, None, True) for oid in obsolete], num_procs_param=32, dummy_pool=True)
        return len(obsolete)


class CryptoUserCvarNotFound(Exception):
    """
    CryptoUserCvarNotFound
    """
    pass


def generate_rsa_key_pair(key_store_folder, keysize, try_precalc=False):
    """
    @type key_store_folder: str
    @type keysize: int
    @type try_precalc: bool
    """
    if try_precalc:
        if os.path.exists(key_store_folder):
            for fname in os.listdir(key_store_folder):
                try:
                    fpath = os.path.join(key_store_folder, fname)
                    keydata = open(fpath).read()

                    if "-----END PUBLIC KEY-----" in keydata:
                        sep = "-----END PUBLIC KEY-----"
                        keys = open(fpath).read().split(sep)
                        return keys[1].strip(), str(keys[0] + sep).strip()
                finally:
                    os.remove(fpath)

    Random.atfork()
    rng = Random.new().read
    rsa_key_pair = RSA.generate(keysize, rng)
    rsa_private_key = rsa_key_pair.exportKey()
    rsa_public_key = rsa_key_pair.publickey().publickey().exportKey()
    return rsa_private_key, rsa_public_key


def generate_rsa_key_pair_smp(key_store_folder, keysize=2048):
    """
    @type key_store_folder: str
    @type keysize: int
    """
    pr, pub = generate_rsa_key_pair(key_store_folder, keysize)
    fname = base64.encodestring(make_checksum(pr + pub)).strip().strip("=")
    open(os.path.join(key_store_folder, fname), "w").write(pub + "\n" + pr)


def rsa_progress(p=0):
    """
    @type p: int
    """
    sys.stdout.write("generating rsa keys " + str(p) + "%\r")
    sys.stdout.flush()


def make_rsa_keys(key_store_folder, keysize, numkeys, num_procs=None):
    """
    @type key_store_folder: str
    @type keysize: int
    @type numkeys: str
    @type num_procs: str, None
    """
    if not os.path.exists(key_store_folder):
        os.makedirs(key_store_folder)

    if not isinstance(numkeys, int):
        if "+" in str(numkeys):
            try:
                numkeys = int(str(numkeys).split("+")[1]) + len(os.listdir(key_store_folder))
            except Exception, e:
                console_warning(str(e))
                numkeys = 0
        else:
            try:
                numkeys = int(str(numkeys))
            except Exception, e:
                console_warning(str(e))
                numkeys = 0

    numkeys_extra = (float(numkeys) / 100) * 10
    numkeys += numkeys_extra
    numkeys = int(numkeys)

    if not os.path.exists(key_store_folder):
        os.mkdir(key_store_folder)

    while True:
        lsize = numkeys - len(os.listdir(key_store_folder))

        if (lsize - numkeys_extra) <= 0:
            break

        smp_apply(generate_rsa_key_pair_smp, [(key_store_folder, keysize)] * lsize, progress_callback=rsa_progress, num_procs_param=num_procs)


class ClientMandate(SaveObjectGoogle):

    """ a mandate for a device  """

    def __init__(self, serverconfig, object_id=None):
        """
        @type serverconfig: ServerConfig
        @type object_id: str, None
        """
        self.comment = "a mandate for a device"
        self.m_private_key_p64s = {}
        self.m_name = ""
        self.m_user_object_id = ""
        super(ClientMandate, self).__init__(serverconfig, object_id=object_id)


class CryptoUser(SaveObjectGoogle):
    """ user object with encrypted rsa private key, encrypted salt and PBKDF2 password hash """

    def __init__(self, serverconfig, name=None, object_id=None, overwrite=False):
        """
        @type serverconfig: ServerConfig
        @type name: str, None
        @type object_id: str, None
        @type overwrite: bool
        """
        self.calculated_password_hash = None
        self.comment = "a cryptobox user"
        self.password = None
        self.m_password_hash_p64s = None
        self.m_salt_p64s = None
        self.rsa_private_key = None
        self.m_rsa_public_key = None
        self.m_aes_encrypted_rsa_private_key_p64s = None
        self.authorized = False
        self.m_cvars = {}
        self.m_username = name
        self.m_email_p64s = ""
        self.m_is_superuser = False
        self.m_last_login = ""
        self.passwords_to_save = []
        self.passwords_to_delete = []
        super(CryptoUser, self).__init__(serverconfig, object_id=object_id)
        self.set_required(["m_username"])
        #self.add_user_editable("m_username", "text", True, "Inlognaam")
        self.add_user_editable("m_email_p64s", "text", True, "Email")
        self.add_user_editable("m_is_superuser", "bool", False, "Beheerder")
        self.add_user_editable("password", "password", True, "Wachtwoord")

        if name is not None and not overwrite:
            for i in self.collection(serverconfig):
                if i.m_username == name:
                    self.object_id = i.object_id

        if self.m_username is not None:
            if self.m_username not in self.object_id:
                self.object_id += ":" + self.m_username.replace("_", "")

    def save(self, object_id=None, serverconfig=None, force_consistency=False, store_in_memcached=True, force_save=True, transaction=None, use_datastore=True):
        """
        @type object_id: str, None
        @type serverconfig: ServerConfig, None
        @type force_consistency: bool
        @type store_in_memcached: bool
        @type force_save: bool
        @type transaction: str, None
        @type use_datastore: bool
        """
        for user in self.collection():
            if user.m_username == self.m_username:
                if user.object_id != self.object_id:
                    raise Exception("username already exists")

        for cup_dict in self.passwords_to_delete:
            self.get_serverconfig().rs_del(self.object_id + cup_dict["m_data_object_id"])
            cup = CryptoUserPassword(self.get_serverconfig())
            cup.delete(object_id=cup_dict["object_id"])
        self.passwords_to_delete = []

        for cup in self.passwords_to_save:
            self.get_serverconfig().rs_set(self.object_id + cup.m_data_object_id, cup.m_password_p64s)
            cup.m_password_p64s = self.encrypt_with_public_key(cup.m_password_p64s)
            cup.save(force_consistency=True, force_save=True)
        self.passwords_to_save = []
        super(CryptoUser, self).save(object_id, serverconfig, force_consistency=force_consistency, force_save=force_save, transaction=transaction, use_datastore=use_datastore)

    def get_option_fields(self):
        """
        get_option_fields
        """
        d = {"m_email_p64s": self.m_email_p64s}
        return d

    def get_name(self):
        """
        object_id is username
        """
        return self.m_username

    def load(self, object_id=None, serverconfig=None, force_load=False, use_datastore=True):
        """
        @type object_id: str, None
        @type serverconfig: ServerConfig, None
        @type force_load: bool
        @type use_datastore: bool
        """
        if object_id:
            self.object_id = object_id

        if serverconfig:
            self.serverconfig = serverconfig

        return super(CryptoUser, self).load(object_id=self.object_id, force_load=force_load, use_datastore=use_datastore)

    def _check_password(self, password):
        """
        @type password: str
        """
        try:
            if len(self.object_id) <= 0:
                raise Exception("username not set")

            if len(password) < 6:
                raise PasswordException("shorter then 6 characters")
        except PasswordException, ex:
            log("Weak password:" + str(ex))
            return

    def reset_password(self, old_password, new_password):
        """
        @type old_password: str
        @type new_password: str
        """
        if len(self.passwords_to_delete) > 0:
            raise PasswordException("there are passwords to delete, cannot reset now")

        if len(self.passwords_to_save) > 0:
            raise PasswordException("there are passwords to save, cannot reset now")

        self.authorize(password=old_password)
        # decrypt
        if not self.authorized:
            raise PasswordException("reset password - not authorized")

        mtx = Mutex(self.get_serverconfig().get_namespace(), self.object_id + "_reset_password")
        mtx.acquire_lock()
        try:
            self._check_password(new_password)
            self.rsa_private_key = self.get_rsa_private_key()
            decrypted_passwords = {}

            for key in self.get_password_ids():
                decrypted_passwords[key] = self.get_store_password(key)
            # encrypt
            self.password = new_password
            self.m_password_hash_p64s = password_derivation(self.password, self.m_salt_p64s)
            self.m_aes_encrypted_rsa_private_key_p64s = encrypt(key=self.password, data=self.rsa_private_key)

            for key in decrypted_passwords:
                self.set_store_password(key, decrypted_passwords[key], overwrite=True)

            self.set_store_password("password_hash", self.m_password_hash_p64s, overwrite=True)
            return True
        finally:
            mtx.release_lock()

    def create_user(self, password, keystore, keysize):
        """
        @type password: str
        @type keystore: str
        @type keysize: int
        """
        if not self.object_id:
            raise Exception("no object id in create user")

        self._check_password(password)
        self.password = password
        # make a salt and encrypt that too
        self.m_salt_p64s = get_random_data_aes_blocksize()
        self.m_password_hash_p64s = password_derivation(self.password, self.m_salt_p64s)
        # make key pair for user
        mtx = Mutex(self.get_serverconfig().get_namespace(), self.object_id + "_generate_rsa")
        try:
            mtx.acquire_lock()
            self.get_serverconfig().event("generating rsa key: " + str(keysize))
            rsa_private_key, rsa_public_key = generate_rsa_key_pair(keystore, keysize, try_precalc=True)
        finally:
            mtx.release_lock()
        self.rsa_private_key = rsa_private_key
        self.m_rsa_public_key = rsa_public_key
        self.m_aes_encrypted_rsa_private_key_p64s = encrypt(key=self.password, data=self.rsa_private_key)
        self.authorized = True
        self.set_store_password(self.object_id, self.m_password_hash_p64s)
        self.save(force_consistency=True)

    def get_rsa_private_key(self):
        """ decrypt private key """
        if not self.authorized:
            raise RSAException("not authorized")

        if not self.password:
            raise RSAException("no password")

        if not self.rsa_private_key:
            self.rsa_private_key = decrypt(self.password, self.m_aes_encrypted_rsa_private_key_p64s)

        return self.rsa_private_key

    def get_password_hash_b64(self):
        """
            get the passwordhash base64 encoded
        """
        return base64.encodestring(self.m_password_hash_p64s)

    def authorize(self, password=None, password_hash_b64=None, password_hash=None):
        """
        @type password: str, None
        @type password_hash_b64: str, None
        @type password_hash: str, None
        """
        self.get_serverconfig().event("CryptoUser:authorize")
        self.password = password
        self.load(force_load=True)

        if not self.m_salt_p64s:
            raise PasswordException("authorize error: user not loaded")

        if password_hash_b64:
            password_hash = base64.decodestring(password_hash_b64)

        if password_hash:
            if password_hash == self.m_password_hash_p64s:
                self.authorized = True
                return True
            raise PasswordException(self.object_id + " is not authorized")
        else:
            if not password:
                raise PasswordException("password is not given")

        calculated_password_hash = password_derivation(self.password, self.m_salt_p64s)
        self.calculated_password_hash = calculated_password_hash

        if calculated_password_hash == self.m_password_hash_p64s:
            self.authorized = True
        else:
            raise PasswordException(str(self.m_username) + " is not authorized")

        return self.authorized

    def is_authorized(self):
        """
        is_authorized
        """
        return self.authorized

    def encrypt_with_public_key(self, data):
        """ RSAES-OAEP encrypt
        @type data: str
        RSA modulus (in bytes) minus 2, minus twice the hash output size.
        """
        self.get_serverconfig().event("encrypt_with_public_key")

        if len(data) > 210:
            console("too much data in this object -> len(object_b64_safe(data)) > 210", print_stack=True, warning=True)
            raise ValueError()

        if not self.m_rsa_public_key:
            self.load()

        pub_key = RSA.importKey(self.m_rsa_public_key)
        cipher = PKCS1_OAEP.new(pub_key)
        enc_data = cipher.encrypt(data)
        return enc_data

    def decrypt_with_private_key(self, enc_data, private_key=None):
        """
        @type enc_data: str
        @type private_key: str, None
        """
        self.get_serverconfig().event("decrypt_with_private_key")

        if len(enc_data.strip()) == 0:
            raise Exception()

        if not private_key:
            if not self.authorized:
                raise Exception("not authorized")

            if self.rsa_private_key:
                private_key = self.rsa_private_key
            else:
                private_key = self.get_rsa_private_key()

        p_key = RSA.importKey(private_key)
        cipher = PKCS1_OAEP.new(p_key)
        return cipher.decrypt(enc_data)

    def del_store_password(self, pwd_id):
        """
        @type pwd_id: str
        """
        passwords = self.serverconfig.gds_run_view("CryptoUserPassword", "m_user_object_id", self.object_id, "")

        for pw in passwords:
            if strcmp(pw["m_data_object_id"], pwd_id):
                self.passwords_to_delete.append({"object_id": pw["object_id"], "m_data_object_id": pwd_id})

    def has_store_password(self, pwd_id):
        """
        @type pwd_id: str
        """
        for pw in self.passwords_to_delete:
            if strcmp(pw["m_data_object_id"], pwd_id):
                return False

        for pw in self.passwords_to_save:
            if strcmp(pw.m_data_object_id, pwd_id):
                return True

        passwords = self.serverconfig.gds_run_view("CryptoUserPassword", "m_user_object_id", self.object_id, "m_data_object_id")

        for pw in passwords:
            if strcmp(pw["m_data_object_id"], pwd_id):
                return True
        return False

    def set_store_password(self, pwd_id, password, overwrite=False):
        """
        @type pwd_id: str
        @type password: str
        @type overwrite: bool
        """
        self.get_serverconfig().event("set_store_password")

        if self.has_store_password(pwd_id):
            if not overwrite:
                raise PasswordStoreError("password " + pwd_id + " overwritten")
            else:
                for pw in self.passwords_to_save:
                    if strcmp(pw.m_data_object_id, pwd_id):
                        pw.m_password_p64s = password
                        return True

                passwords = self.serverconfig.gds_run_view_fields_values("CryptoUserPassword", [("m_user_object_id", self.object_id), ("m_data_object_id", pwd_id)], member="object_id")

                if len(passwords) > 1:
                    raise PasswordException("set_store_password: retrieved multiple passwords for the same data object")

                for pw in passwords:
                    cup = CryptoUserPassword(self.get_serverconfig(), self.object_id, pwd_id, password)
                    cup.object_id = pw["object_id"]
                    self.passwords_to_save.append(cup)
                    return True

        for pw in list(self.passwords_to_delete):
            if strcmp(pw["m_data_object_id"], pwd_id):
                self.passwords_to_delete.remove(pw)

        cup = CryptoUserPassword(self.get_serverconfig(), self.object_id, pwd_id, password)
        self.passwords_to_save.append(cup)
        return True

    def get_password_ids(self):
        """
        get_password_ids
        """
        pwd_ids = set()
        passwords = self.serverconfig.gds_run_view("CryptoUserPassword", "m_user_object_id", self.object_id, "m_data_object_id")

        for pw in passwords:
            add = True

            for pw2 in self.passwords_to_delete:
                if strcmp(pw2["m_data_object_id"], pw2["m_data_object_id"]):
                    add = False

            if add:
                pwd_ids.add(pw["m_data_object_id"])

        return list(pwd_ids)

    def get_store_password(self, pwd_id, private_key=None):
        """
        @type pwd_id: str
        @type private_key: str, None
        """
        password = self.get_serverconfig().rs_get(self.object_id + pwd_id)

        if password is not None:
            return password

        self.get_serverconfig().event("get_store_password")

        for pw in self.passwords_to_delete:
            if strcmp(pw["m_data_object_id"], pwd_id):
                raise PasswordException("get_store_password: no password for " + str(pwd_id))

        for pw in self.passwords_to_save:
            if strcmp(pw.m_data_object_id, pwd_id):
                return pw.m_password_p64s

        passwords = self.serverconfig.gds_run_view_fields_values("CryptoUserPassword", [("m_user_object_id", self.object_id), ("m_data_object_id", pwd_id)], "")
        enc_key = None

        for pw_view in passwords:
            view_data_id = pw_view["m_data_object_id"]

            if strcmp(view_data_id, pwd_id):
                enc_key = pickled_base64_to_object(pw_view["m_password_p64s"])

        if enc_key is None:
            raise PasswordException("get_store_password: no password for " + str(pwd_id))

        if not private_key:
            if not self.authorized:
                raise Exception("not authorized")

            private_key = self.get_rsa_private_key()

        data = self.decrypt_with_private_key(enc_key, private_key)
        return data

    def authorize_boolean(self, password):
        """
        catch the exception and return a boolean
        @param password:
        @type password:
        """
        #noinspection PyBroadException
        try:
            self.authorize(password)
            return self.is_authorized()
        except PasswordException:
            return False
        except:
            return False

    def authorize_boolean_hash(self, password_hash_b64):
        """
        catch the exception and return a boolean
        @param password_hash_b64:
        @type password_hash_b64:
        """
        try:
            self.authorize(password_hash_b64=password_hash_b64)
            return self.is_authorized()
        except PasswordException:
            return False

    def authorize_private_key(self, private_key):
        """
        @type private_key:
        """
        try:
            if not self._id:
                self.load()

            password_hash_b64 = self.get_store_password(self.object_id, private_key)

            if password_hash_b64:
                self.authorize(password_hash=password_hash_b64)

            if self.is_authorized():
                self.rsa_private_key = private_key
                return True
            return False
        except PasswordException:
            return False

    def set_cvar(self, key, value):
        """
        @type key: str, unicode
        @type value: str, dict
        @rtype: None
        """
        self.m_cvars[key] = object_b64_safe(value)

    def has_cvar(self, key):
        """
        @type key: str
        """
        return key in self.m_cvars

    def get_cvar(self, key, allow_none=False):
        """
        @type key: str
        @type allow_none: bool
        """
        if key in self.m_cvars:
            return b64_object_safe(self.m_cvars[key])
        else:
            if allow_none:
                return None
            else:
                raise CryptoUserCvarNotFound(key)

    def del_cvar(self, key):
        """
        @type key: str
        """
        if key in self.m_cvars:
            del self.m_cvars[key]

    def get_cvars(self):
        """
        get_cvars
        """
        if not isinstance(self.m_cvars, dict):
            self.m_cvars = {}
        d = {}

        for k in self.m_cvars:
            if not k.endswith("_encrypt"):
                d[k] = self.m_cvars[k]

        return d

    def new_client_mandate(self, name, rsa_private_key):
        """
        @type name: str
        @type rsa_private_key: str
        """
        if not self.authorized:
            raise PasswordException("new_client_mandate: user must be authorized")

        mks = name.split("||")

        if len(mks) > 1:
            raise Mandate("illigal character ||")

        mkey = "mandate_" + slugify(name)

        if self.has_cvar(mkey):
            return "mandate_with_this_name_exists"

        mandate_secret = generate_password(32)
        mandate_priv_key = encrypt("", rsa_private_key, salt_secret=(generate_password(32), mandate_secret))
        mandate = ClientMandate(self.get_serverconfig())
        mandate.m_private_key_p64s = mandate_priv_key
        mandate.m_name = name
        mandate.m_user_object_id = self.object_id
        mandate.save()
        self.set_cvar(mkey, mandate.object_id)
        self.save()
        return mkey + "||" + mandate_secret

    def get_client_mandate(self, mandate_key_param):
        """
        @type mandate_key_param: str
        """
        mandate_key = None
        mandate_pw = None
        mks = mandate_key_param.split("||")

        if len(mks) == 2:
            mandate_key = mks[0]
            mandate_pw = mks[1]

        if not self.has_cvar(mandate_key):
            raise NoMandate("key not found")

        if not mandate_pw:
            raise NoMandate("pw not found")

        mandate = ClientMandate(self.get_serverconfig(), object_id=self.get_cvar(mandate_key))
        mandate.load()
        mandate.private_key = decrypt("", mandate.m_private_key_p64s, secret=mandate_pw)
        return mandate.m_name, mandate.private_key

    #noinspection PyMethodMayBeStatic
    def verify_mandate(self, mandate):
        """
        @type mandate: str
        """
        pass

    def delete(self, serverconfig=None, object_id=None, force_consistency=False, force=False, transaction=None, delete_from_datastore=True):
        """
        @type serverconfig: ServerConfig, None
        @type object_id: str, None
        @type force_consistency: bool
        @type force: bool
        @type transaction: str, None
        @type delete_from_datastore: bool
        """
        if object_id:
            self.object_id = object_id

        if not self._id:
            self.load()

        cup = CryptoUserPassword(self.get_serverconfig())

        for pwd in cup.collection():
            if pwd.m_user_object_id == self.object_id:
                pwd.delete(transaction=transaction)

        mandate = ClientMandate(self.get_serverconfig())

        for m in mandate.collection():
            if m.m_user_object_id == self.object_id:
                m.delete(transaction=transaction)

        super(CryptoUser, self).delete(serverconfig, object_id, force, transaction=transaction, delete_from_datastore=delete_from_datastore)


class Mandate(Exception):
    """
    Mandate
    """
    pass


class MandateExists(Exception):
    """
    MandateExists
    """
    pass


class NoMandate(Exception):
    """
    NoMandate
    """
    pass


def encrypt_chunk(secret, fpath, chunksize, initialization_vector):
    """
    @type secret: str
    @type fpath: str
    @type chunksize: tuple
    @type initialization_vector: str
    """
    try:
        f = open(fpath)
        f.seek(chunksize[0])
        chunk = f.read(chunksize[1])
        cipher = AES.new(secret, AES.MODE_CFB, IV=initialization_vector)
        data_hash = make_secure_checksum(chunk, secret)
        enc_data = cipher.encrypt(chunk)
        ntf = get_named_temporary_file(auto_delete=False)
        chunk_seek = str(chunksize[0])
        ntf.write(str(len(chunk_seek)) + "\n")
        ntf.write(chunk_seek)
        ntf.write(str(len(initialization_vector)) + "\n")
        ntf.write(initialization_vector)
        ntf.write(str(len(data_hash)) + "\n")
        ntf.write(data_hash)
        ntf.write(str(len(enc_data)) + "\n")
        ntf.write(enc_data)
        return ntf.name, data_hash
    except Exception, e:
        raise e


def hash_chunk(secret, fpath, chunksize):
    """
    @type secret: str
    @type fpath: str
    @type chunksize: tuple
    """
    try:
        f = open(fpath)
        f.seek(chunksize[0])
        chunk = f.read(chunksize[1])
        data_hash = make_secure_checksum(chunk, secret)
        return len(chunk), data_hash
    except Exception, e:
        raise e


class ChunkListException(Exception):
    """
    ChunkListException
    """
    pass


def make_chunklist(fpath):
    """
    @type fpath: str
    """
    if not os.path.exists(fpath):
        raise Exception("make_chunklist: file does not exist")

    fstats = os.stat(fpath)
    fsize = fstats.st_size

    if fsize <= 1:
        open(fpath, "a").write("\n")

    fstats = os.stat(fpath)
    fsize = fstats.st_size
    chunksize = (1 * (2 ** 20))

    #noinspection PyBroadException
    try:
        numcores = multiprocessing.cpu_count()

        if (numcores * chunksize) > fsize:
            chunksize = int(math.ceil(float(fsize) / numcores))
    except:
        pass

    if chunksize == 0:
        chunksize = 1
    num_chunks = fsize / chunksize
    chunk_remainder = fsize % chunksize
    chunklist = [chunksize] * num_chunks
    chunklist.append(chunk_remainder)
    chunklist_abs = []
    val = 0

    for i in chunklist:
        chunklist_abs.append((val, i))
        val += i

    if chunk_remainder != 0:
        last = chunklist_abs.pop()
        chunklist_abs.append((last[0], last[1] + chunk_remainder))

    if chunklist_abs[len(chunklist_abs) - 1][1] == 0:
        chunklist_abs.pop()

    return chunklist_abs


def encrypt_file_smp(secret, fname, progress_callback=None, progress_callback_param=None, single_file=False, num_procs_param=None):
    """
    @type secret: str
    @type fname: str
    @type progress_callback: str, None
    @type progress_callback_param: list, dict, int, str, unicode, tuple
    @type single_file: bool
    @type num_procs_param: None, int
    """
    Random.atfork()
    initialization_vector = get_random_data_aes_blocksize()
    chunklist = make_chunklist(fname)

    chunklist = [(secret, fname, chunk_size, initialization_vector) for chunk_size in chunklist]

    if len(chunklist) == 1:
        enc_files = [apply(encrypt_chunk, chunklist[0])]

        if progress_callback:
            progress_callback(100)
    else:
        enc_files = smp_apply(encrypt_chunk, chunklist, progress_callback=progress_callback, progress_callback_param=progress_callback_param, use_dummy_thread_pool=False, num_procs_param=num_procs_param)

    cleanup_tempfiles()

    if single_file:
        enc_file = tempfile.SpooledTemporaryFile(max_size=524288000)
        data_hashes = []

        for efpath, data_hash in enc_files:
            data_hashes.append(data_hash)
            enc_file.write(str(os.stat(efpath).st_size) + "\n") 
            fdata = open(efpath).read()
            enc_file.write(fdata)
            os.remove(efpath)

        enc_file.seek(0)
        return enc_file, make_hash_list(data_hashes)
    else:
        return [x[0] for x in enc_files]


def listener_file_writer(fn, q):
    """
    @type fn: str
    @type q: multiprocessing.Queue
    """
    f = open(fn, 'wb')

    while 1:
        if q:
            m = q.get()
        else:
            raise Exception("listener_file_writer: no Queue")

        if m == 'kill':
            break

        f.seek(m[0])
        f.write(m[1])
        f.flush()

    f.close()


def decrypt_chunk(secret, fpath, queue):
    """
    @type secret: str
    @type fpath: str
    @type queue: multiprocessing.Queue
    """
    chunk_file = open(fpath.strip())
    chunk_pos_len = int(chunk_file.readline())
    chunk_pos = int(chunk_file.read(chunk_pos_len))
    initialization_vector_len = int(chunk_file.readline())
    initialization_vector = chunk_file.read(initialization_vector_len)
    data_hash_len = int(chunk_file.readline())
    data_hash = chunk_file.read(data_hash_len)
    enc_data_len = int(chunk_file.readline())
    enc_data = chunk_file.read(enc_data_len)

    if 16 != len(initialization_vector):
        raise Exception("initialization_vector len is not 16")

    cipher = AES.new(secret, AES.MODE_CFB, IV=initialization_vector)
    dec_data = cipher.decrypt(enc_data)
    calculated_hash = make_secure_checksum(dec_data, secret)

    if data_hash != calculated_hash:
        raise EncryptionHashMismatch("decrypt_file -> the decryption went wrong, hash didn't match")

    if queue.qsize() > 20:
        time.sleep(0.5)

    queue.put((chunk_pos, dec_data))
    return calculated_hash


def decrypt_file_smp(secret, enc_file=None, enc_files=tuple(), progress_callback=None, delete_enc_files=False, auto_delete_tempfile=True):
    """
    @type secret: str, unicode
    @type enc_file: file, None
    @type enc_files: tuple
    @type progress_callback: function
    @type delete_enc_files: bool
    @type auto_delete_tempfile: bool
    """
    try:
        if enc_file:
            enc_files = []
            enc_file.seek(0)
            chunk_size = int(enc_file.readline())

            while chunk_size:
                delete_enc_files = True
                nef = get_named_temporary_file(auto_delete=False)
                nef.write(enc_file.read(chunk_size))
                nef.close()
                enc_files.append(nef.name)
                chunk_line = enc_file.readline()

                if not chunk_line:
                    chunk_size = None
                else:
                    chunk_size = int(chunk_line)

            enc_file.close()

        if not enc_files:
            raise Exception("nothing to decrypt")

        dec_file = get_named_temporary_file(auto_delete=auto_delete_tempfile)

        chunks_param_sorted = [(secret, file_path) for file_path in enc_files]
        hashes = smp_apply(decrypt_chunk, chunks_param_sorted, progress_callback, listener=listener_file_writer, listener_param=tuple([dec_file.name]), use_dummy_thread_pool=False)
        dec_file.seek(0)

        if enc_file:
            return dec_file, make_hash_list(hashes)
        else:
            return dec_file
    finally:
        if delete_enc_files:
            for efp in enc_files:
                if os.path.exists(efp):
                    os.remove(efp)

        cleanup_tempfiles()


def callback_funcion(progress):
    """
    @param progress:
    @type progress:
    """
    print "crypto_api:1482", progress


class EmptyFile(Exception):
    """
    EmptyFile
    """
    pass


class DataStillEncrypted(Exception):
    """
    DataStillEncrypted
    """
    pass


class PlainDataNotFoundSharedMemory(Exception):
    """
    PlainDataNotFoundSharedMemory
    """
    pass


class CryptoDocMetaDataNotFound(Exception):
    """
    CryptoDocMetaDataNotFound
    """
    pass


class CryptoDocNoNameGivenForFile(Exception):
    """
    CryptDocNoNameGivenForFile
    """
    pass


class CryptoDocException(Exception):
    """
    CryptDocNoNameGivenForFile
    """
    pass


def get_id_to_content_hash(serverconfig):
    """
    @type serverconfig: ServerConfig
    """
    if not serverconfig:
        raise Exception("Database variable not set (serverconfig)")

    hashes = {}
    docs = gds_get_dict_list(serverconfig.get_namespace(), "CryptoDoc")

    for result in docs:
        hashes[result["object_id"]] = (result["m_hmac_sha1_hash"], result["m_doc_last_modified"])

    return hashes


#noinspection PyMethodParameters,PyMethodFirstArgAssignment
def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    @param value:
    @type value:
    """
    value = unicodedata.normalize("NFKD", unicode(value)).encode("ascii", "ignore")
    value = unicode(re.sub("[^\w\s-]", "", value).strip().lower())
    return re.sub("[-\s]+", "-", value)


def slugify_path(path):
    """
    @type path: str
    """
    spath = ""
    ps = path.split("/")
    lenps = len(ps)
    cnt = 0

    for i in ps:
        spath += slugify(i)

        if cnt < lenps - 1:
            spath += "/"
        cnt += 1

    return spath


def make_sha1_hash_file(prefix=None, fpath=None, data=None, fpi=None):
    """ make hash
    @type prefix: str
    @type fpath: str, None
    @type data: str, None
    @type fpi: file, None, FileIO
    """
    sha = SHA.new()

    if prefix:
        sha.update(prefix)

    if data:
        fp = StringIO(data)
    elif fpath:
        fp = open(fpath)
    else:
        fp = fpi
        fp.seek(0)

    one_mb = (1 * (2 ** 20))
    chunksize = one_mb / 2
    chunk = fp.read(chunksize)
    cnt = 1

    while chunk:
        crc = base64.encodestring(str(zlib.adler32(chunk))).strip().rstrip("=")
        sha.update(crc)
        fp.seek(cnt * chunksize)
        cnt += 1
        chunk = fp.read(100)

    return sha.hexdigest()


class CryptoDoc(SaveObjectGoogle):
    """
    placeholder for encrypted documents
    """

    def __init__(self, serverconfig=None, object_id=None, comment="an encrypted document"):
        """
        @type serverconfig: ServerConfig
        @type object_id: str, unicode
        @type comment: str, unicode
        """
        Random.atfork()
        self.dec_data = None
        super(CryptoDoc, self).__init__(serverconfig, object_id, comment)
        self.m_hmac_sha1_hash = None
        self.m_document_name_p64s = ""
        self.m_mime_type_p64s = ""
        self.m_size_p64s = ""
        self.m_file_format = "cryptobox_document_12"
        self.m_doc_last_modified = ""
        self.m_created_by = ""
        self.m_data_p64s = ""
        self.m_salt_p64s = get_random_data(32)
        self.m_num_chunks = -1
        self.encrypted = False
        self.cloudstorage = True
        self.m_extra_indexed_keys = ["m_hmac_sha1_hash", "m_doc_last_modified", "m_created_by"]
        self.size = None

        if "lycia" in crypto_data.GLOBAL_HOSTNAME:
            self.cloudstorage = False

        if "cryptoboxtestserver" in crypto_data.GLOBAL_HOSTNAME:
            self.cloudstorage = False

    def get_bucket_name(self):
        """
        get_bucket_name
        """
        bucket_name = self.get_serverconfig().identifcation() + "_" + crypto_data.CRYPTODOCFOLDERGOOGLE
        return bucket_name

    def find_doc_same_hash(self, key, ufile=None):
        """
        @type key: str
        @type ufile: FileIO
        """
        if ufile:
            hmac_sha1_hash = make_hash_hmac(make_sha1_hash_file(fpi=ufile), key)
        else:
            hmac_sha1_hash = self.m_hmac_sha1_hash

        for hashes in self.get_serverconfig().gds_run_view(kind="CryptoDoc", filterfield="m_hmac_sha1_hash", filterfieldval=hmac_sha1_hash, member="object_id"):
            return hashes["object_id"]
        return None

    def get_size(self):
        """
        get_size
        """
        if self.size is None:
            raise CryptoDocException("get_size: no size set")
        else:
            return int(self.size)

    def encrypt_save(self, key, user_object_id, ufile, progress_callback_encrypt=None, progress_callback_param_encrypt=None, secret=None, use_dummy_thread_pool=False, num_procs_param=None):
        """
        @type key: str
        @type user_object_id: str
        @type ufile: FileIO
        @type progress_callback_encrypt: str, None
        @type progress_callback_param_encrypt: str, None
        @type secret: str, None
        @type use_dummy_thread_pool: bool
        @type num_procs_param: None, int
        """
        if self.encrypted:
            return False

        if not use_dummy_thread_pool:
            Random.atfork()

        if not secret:
            if not key or len(key) == 0:
                raise Exception("CryptoDoc:encrypt_data no key or secret given")

            if self.m_salt_p64s is None:
                self.m_salt_p64s = get_random_data(32)

            secret = password_derivation(key, self.m_salt_p64s)

        self.m_size_p64s = str(get_file_size(fpi=ufile))
        self.size = self.m_size_p64s
        self.m_hmac_sha1_hash = make_hash_hmac(make_sha1_hash_file(fpi=ufile), key)
        self.m_mime_type_p64s = None

        if len(self.m_document_name_p64s) is 0:
            if hasattr(ufile, "name"):
                self.m_mime_type_p64s = mimetypes.guess_type(ufile.name, strict=False)[0]

                if not self.m_document_name_p64s:
                    if len(self.m_document_name_p64s) == 0:
                        self.m_document_name_p64s = ufile.name

            else:
                raise CryptoDocNoNameGivenForFile(self.object_id)
        else:
            self.m_mime_type_p64s = mimetypes.guess_type(self.m_document_name_p64s, strict=False)[0]

        if not self.m_mime_type_p64s:
            if hasattr(ufile, "content_type"):
                self.m_mime_type_p64s = ufile.content_type
            else:
                self.m_mime_type_p64s = "application/octet-stream"

        self.m_created_by = user_object_id
        enc_chunks = encrypt_file_smp(secret, ufile.name, progress_callback=progress_callback_encrypt, progress_callback_param=progress_callback_param_encrypt, num_procs_param=num_procs_param)
        self.m_num_chunks = len(enc_chunks)
        bucket_name = self.get_bucket_name()
        name = self.object_id
        write_chunks_param = [(bucket_name, name + "_" + str(fpath[0]), fpath[1], self.cloudstorage) for fpath in enumerate(enc_chunks)]
        num_procs = len(write_chunks_param)
        smp_apply(gcs_write_to_gcloud, write_chunks_param, num_procs_param=num_procs, use_dummy_thread_pool=use_dummy_thread_pool)

        for fp in enc_chunks:
            if os.path.exists(fp):
                os.remove(fp)

        cleanup_tempfiles()
        ss = (self.m_salt_p64s, secret)
        m_document_name_p64s = self.m_document_name_p64s
        self.m_document_name_p64s = encrypt(key, self.m_document_name_p64s, salt_secret=ss)
        m_mime_type_p64s = self.m_mime_type_p64s
        self.m_mime_type_p64s = encrypt(key, self.m_mime_type_p64s, salt_secret=ss)
        self.m_size_p64s = encrypt(key, self.m_size_p64s, salt_secret=ss)
        self.m_doc_last_modified = time.time()
        self.encrypted = True
        self.save(force_save=True, force_consistency=True)
        self.m_document_name_p64s = m_document_name_p64s
        self.m_mime_type_p64s = m_mime_type_p64s
        self.dec_data = None
        return True

    def load_decrypt(self, key, file_data=True, progress_callback_decrypt=None, secret=None, use_dummy_thread_pool=False, auto_delete_tempfile=True):
        """
        @type key: str
        @type file_data: bool
        @type progress_callback_decrypt: function, None
        @type secret: str, None
        @type use_dummy_thread_pool: bool
        @type auto_delete_tempfile: bool
        """
        if not self._id:
            self.load()

        if not self._id:
            raise Exception("CryptoDoc:decrypt_data object_id does not exist")

        if not secret:
            secret = password_derivation(key, self.m_salt_p64s)

        bucket_name = self.get_bucket_name()
        name = self.object_id
        read_chunks_param = [(bucket_name, name + "_" + str(cnt), self.cloudstorage) for cnt in range(0, self.m_num_chunks)]
        num_procs = len(read_chunks_param)
        dec_chunks = smp_apply(gcs_read_from_gcloud, read_chunks_param, num_procs_param=num_procs, use_dummy_thread_pool=use_dummy_thread_pool)

        if file_data:
            dec_data = decrypt_file_smp(secret, enc_files=tuple(dec_chunks), progress_callback=progress_callback_decrypt, auto_delete_tempfile=auto_delete_tempfile)
        else:
            dec_data = None

        for fp in dec_chunks:
            if os.path.exists(fp):
                os.remove(fp)

        cleanup_tempfiles()
        self.m_size_p64s = decrypt("", self.m_size_p64s, secret=secret)
        self.size = self.m_size_p64s
        self.m_document_name_p64s = decrypt("", self.m_document_name_p64s, secret=secret)
        self.m_mime_type_p64s = decrypt("", self.m_mime_type_p64s, secret=secret)
        self.encrypted = False
        self.dec_data = dec_data
        return dec_data

    def get_data(self):
        """
        get_data\#
        """
        if self.dec_data is None:
            raise CryptoDocException("CryptoDoc:get_data -> no decrypted data found")

        self.dec_data.seek(0)
        return self.dec_data.read()

    def delete(self, serverconfig=None, object_id=None, force_consistency=False, force=False, transaction=None, delete_from_datastore=True):
        """
        @type serverconfig: ServerConfig, None
        @type object_id: str, None
        @type force_consistency: bool
        @type force: bool
        @type transaction: str, None
        @type delete_from_datastore: bool
        """
        transaction = None

        if object_id:
            self.object_id = object_id

        if not self._id:
            self.load()

        if self.object_id is None:
            return
        cnt = 0
        chunks_param = []

        while cnt < self.m_num_chunks:
            chunks_param.append((self.get_serverconfig().identifcation() + "_" + crypto_data.CRYPTODOCFOLDERGOOGLE, self.object_id + "_" + str(cnt), self.cloudstorage))
            cnt += 1

        smp_apply(gcs_delete_from_gcloud, chunks_param)
        super(CryptoDoc, self).delete(serverconfig, self.object_id, force, transaction=transaction, delete_from_datastore=delete_from_datastore)
