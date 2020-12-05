import hashlib

hash1 = hashlib.md5(b'MyPassword123')
hash2 = hashlib.md5(b'MyPassword023')
print(hash1.hexdigest())
print(hash2.hexdigest())
