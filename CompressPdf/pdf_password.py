from PyPDF2 import PdfReader, PdfWriter
import getpass

def remove_pdf_password(input_pdf_path, output_pdf_path, password):
    """
    Removes password protection from a PDF file.

    Parameters:
        input_pdf_path (str): Path to the password-protected PDF file.
        output_pdf_path (str): Path to save the decrypted PDF file.
        password (str): Password for the PDF file.

    Returns:
        str: Success message or error message.
    """
    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        if reader.is_encrypted:
            try:
                reader.decrypt(password)  # Attempt decryption with provided password
            except Exception:
                return "Error: The PDF is password protected. Please provide the correct password."

        # Add all pages to the writer
        for page in reader.pages:
            writer.add_page(page)

        # Write the decrypted content to a new file
        with open(output_pdf_path, 'wb') as output_pdf:
            writer.write(output_pdf)

        return f"Decrypted PDF successfully saved to {output_pdf_path}"
    except FileNotFoundError:
        return "Error: The file was not found. Please check the path and try again."
    except Exception as e:
        return f"Error: An unexpected error occurred. {str(e)}"

def set_pdf_password(input_pdf_path, output_pdf_path, password):
    """
    Set a password for a PDF file.

    Args:
        input_pdf_path (str): Path to the input PDF file.
        output_pdf_path (str): Path to save the password-protected PDF file.
        password (str): Password to set for the PDF file.
    """
    try:
        reader = PdfReader(input_pdf_path)
        writer = PdfWriter()

        # Add all pages from the reader to the writer
        for page in reader.pages:
            writer.add_page(page)

        # Set the password for the PDF
        writer.encrypt(password)

        # Write the encrypted PDF to the output file
        with open(output_pdf_path, 'wb') as output_file:
            writer.write(output_file)

        return f"Password-protected PDF successfully saved to {output_pdf_path}"
    except FileNotFoundError:
        return "Error: The file was not found. Please check the path and try again."
    except Exception as e:
        return f"Error: An unexpected error occurred. {str(e)}"

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Remove PDF password")
    print("2. Set PDF password")
    option = input("Enter your choice (1 or 2): ")

    if option == "1":
        input_pdf_path = input("Enter the path to the password-protected PDF file: ")
        output_pdf_path = input("Enter the path to save the decrypted PDF file: ")
        password = getpass.getpass("Enter the password for the PDF file: ")
        result_message = remove_pdf_password(input_pdf_path, output_pdf_path, password)
        print(result_message)
    elif option == "2":
        input_pdf_path = input("Enter the path to the input PDF file: ")
        output_pdf_path = input("Enter the path to save the password-protected PDF file: ")
        password = getpass.getpass("Enter the password to set for the PDF file: ")
        result_message = set_pdf_password(input_pdf_path, output_pdf_path, password)
        print(result_message)
    else:
        print("Invalid option selected. Please run the program again.")
