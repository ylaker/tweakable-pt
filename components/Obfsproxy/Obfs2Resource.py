MAGIC_VALUE = 0x2BF5CA7E
SEED_LENGTH = 16
MAX_PADDING = 8192
HASH_ITERATIONS = 100000

KEYLEN = 16  # is the length of the key used by E(K,s) -- that is, 16.
IVLEN = 16  # is the length of the IV used by E(K,s) -- that is, 16.

ST_WAIT_FOR_KEY = 0
ST_WAIT_FOR_PADDING = 1
ST_OPEN = 2

def h(x):
    """ H(x) is SHA256 of x. """

    hasher = hashlib.sha256()
    hasher.update(x)
    return hasher.digest()

def hn(x, n):
    """ H^n(x) is H(x) called iteratively n times. """

    data = x
    for _ in xrange(n):
        data = h(data)
    return data