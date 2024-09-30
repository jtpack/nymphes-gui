from pathlib import Path
import json
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from activation_code_verifier.common import hash_from_string, generate_license_string
from cryptography.hazmat.primitives import serialization
from activation_code_verifier.common import validate_activation_code_parameters


def verify_activation_code(activation_code, public_key):
    """
    Verify that activation_code is valid.
    Raises an Exception if it is invalid or if anything else goes wrong.
    :param activation_code: str
    :param public_key: RSAPublicKey
    :return: True if code is valid
    """
    if activation_code is None or len(activation_code) == 0:
        raise Exception('activation_code is None or empty')

    # Load activation_code data into a dict
    data_dict = data_from_activation_code(activation_code)

    # Verify the data parameters.
    # This will generate an Exception if any parameters are invalid.
    validate_activation_code_parameters(name=data_dict['name'],
                                        display_name=data_dict['display_name'],
                                        email=data_dict['email'],
                                        app_name=data_dict['app_name'],
                                        license_type=data_dict['license_type'],
                                        expiration_date=data_dict['expiration_date'])

    # Verify signature matches the parameters and is valid.
    # This will generate an Exception if it fails.
    _verify_signature(name=data_dict['name'],
                      display_name=data_dict['display_name'],
                      email=data_dict['email'],
                      app_name=data_dict['app_name'],
                      license_type=data_dict['license_type'],
                      expiration_date=data_dict['expiration_date'],
                      signature=data_dict['signature'],
                      public_key=public_key)

    return True


def load_activation_code_from_file(file_path):
    """
    Load the contents of file_path and return as a string
    :param file_path: Path or str
    :return: str
    """
    # Make sure file_path is a Path
    file_path = Path(file_path).expanduser()

    # Load the file
    with open(file_path, 'r') as file:
        return file.read()


def data_from_activation_code(activation_code):
    """
    Extract the data from the json-encoded activation
    code and return as a dict
    :param activation_code: str
    :return: dict
    """
    return json.loads(activation_code)


def _verify_signature(name, display_name, email,
                      app_name, license_type, expiration_date,
                      signature, public_key):
    """
    Verify that the supplied signature was generated
    using the private key which matches the supplied
    public key, and that the signature contains the
    correct hash for the supplied name, display_name, email,
    app_name, license type and expiration date.
    Raises an Exception if the signature is not valid or if anything else goes wrong.
    :param name: str
    :param display_name: str
    :param email: str
    :param app_name: str
    :param license_type: str
    :param expiration_date: str or None. Should be formatted as YYYY-MM-DD
    :param signature: str
    :param public_key: RSAPublicKey
    :return: True if signature is valid
    """
    # Generate a code string from the name, email, license_type and expiration date
    code_string = generate_license_string(name=name,
                                          display_name=display_name,
                                          email=email,
                                          app_name=app_name,
                                          license_type=license_type,
                                          expiration_date=expiration_date)

    # Generate a hash
    code_hash = hash_from_string(code_string=code_string)

    public_key.verify(
        base64.b64decode(signature),
        code_hash,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )

    return True


def load_public_key_from_file(file_path):
    """
    Load the public key at file_path and return it
    :param file_path: Path or str
    :param password: str
    :return: RSAPublicKey
    """
    # Make sure file_path is a Path
    file_path = Path(file_path).expanduser()

    with open(file_path, "rb") as key_file:
        public_key = serialization.load_pem_public_key(
            key_file.read()
        )
    return public_key