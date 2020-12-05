import hashlib

hash1 = hashlib.md5(b'Mypass123')
hash2 = hashlib.md5(b'Mypass023')
print(hash1.hexdigest())
print(hash2.hexdigest())




