import base64
import argparse
import sys
import os


def encode_pdf_to_base64(pdf_path, output_path=None):
    """Encode PDF file to Base64"""
    try:
        if not os.path.exists(pdf_path):
            return f"Error: File '{pdf_path}' not found"
        
        with open(pdf_path, 'rb') as pdf_file:
            encoded_bytes = base64.b64encode(pdf_file.read())
            encoded_string = encoded_bytes.decode('utf-8')
        
        if output_path:
            with open(output_path, 'w') as output_file:
                output_file.write(encoded_string)
            return f"Encoded PDF saved to: {output_path}"
        else:
            return encoded_string
    except Exception as e:
        return f"Error encoding: {e}"


def decode_base64_to_pdf(base64_input, output_path):
    """Decode Base64 string or file to PDF"""
    try:
        # Check if input is a file path
        if os.path.exists(base64_input):
            with open(base64_input, 'r') as input_file:
                base64_string = input_file.read().strip()
        else:
            base64_string = base64_input
        
        decoded_bytes = base64.b64decode(base64_string)
        
        with open(output_path, 'wb') as pdf_file:
            pdf_file.write(decoded_bytes)
        
        return f"Decoded PDF saved to: {output_path}"
    except Exception as e:
        return f"Error decoding: {e}"


def main():
    parser = argparse.ArgumentParser(description='Base64 PDF Encoder/Decoder')
    parser.add_argument('input', help='PDF file to encode, or Base64 file/string to decode')
    parser.add_argument('-d', '--decode', action='store_true', 
                       help='Decode Base64 to PDF (default is encode PDF to Base64)')
    parser.add_argument('-o', '--output', 
                       help='Output file path (required for decode, optional for encode)')
    
    args = parser.parse_args()
    
    if args.decode:
        if not args.output:
            print("Error: Output path (-o) is required when decoding")
            sys.exit(1)
        result = decode_base64_to_pdf(args.input, args.output)
        print(result)
    else:
        result = encode_pdf_to_base64(args.input, args.output)
        print(result)


if __name__ == "__main__":
    main()
