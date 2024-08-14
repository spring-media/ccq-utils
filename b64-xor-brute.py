import base64
import sys

# The function encrypts the text by performing
# XOR of all the bytes and the `key` and returns the resultant.   
def single_byte_xor(text: bytes, key: int) -> bytes:
    return bytes([b ^ key for b in text])

# decipher the XORed text by brute-forcing the key using the single_byte_xor function
def decipher_xor(text: bytes) -> bytes:
    for key in range(256):
        result = single_byte_xor(text, key)
        print("Key (decimal): " + str(key) + " : " + str(result))

# python main init function
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python b64-xor-brute.py <file>")
        sys.exit(1)
    
    with open(sys.argv[1], 'rb') as f:
        data = f.read()
        decipher_xor(base64.b64decode(data))
