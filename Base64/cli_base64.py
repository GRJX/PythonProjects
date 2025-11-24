import base64
import argparse
import sys

def encode_base64(data):
    """Encode string to Base64"""
    try:
        encoded_bytes = base64.b64encode(data.encode('utf-8'))
        return encoded_bytes.decode('utf-8')
    except Exception as e:
        return f"Error encoding: {e}"

def decode_base64(data):
    """Decode Base64 string"""
    try:
        decoded_bytes = base64.b64decode(data.encode('utf-8'))
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        return f"Error decoding: {e}"

def main():
    parser = argparse.ArgumentParser(description='Base64 Encoder/Decoder')
    parser.add_argument('data', help='Data to encode or decode')
    parser.add_argument('-d', '--decode', action='store_true', 
                       help='Decode Base64 (default is encode)')
    
    args = parser.parse_args()
    
    if args.decode:
        result = decode_base64(args.data)
        print(f"Decoded: {result}")
    else:
        result = encode_base64(args.data)
        print(f"Encoded: {result}")

if __name__ == "__main__":
    main()
