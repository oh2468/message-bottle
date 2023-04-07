from db_handler import DBHandler
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from os import urandom
from string import ascii_letters as asclett
import random

#
# Scipt used to populate the database with random data or to delete all the old (expired) messages.
# If the message gets a password it's always set to "x".
#

def delete_messages(dbHandler):
    print("Now deleting old messages.")
    dbHandler.delete_old_messages()
    print("Done with the deletion.")


def populate_random_data(dbHandler, rows):
    print(f"Now populationg database with {rows} rows")
    for _ in range(rows):
        sender = "".join(random.choices(asclett, k=random.randint(5, 20)))
        title = " ".join("".join(random.choices(asclett, k=random.randint(3, 10))) for _ in range(3))
        msg = " ".join("".join(random.choices(asclett, k=random.randint(1, 10))) for _ in range(random.randint(10, 100)))
        avail = random.randint(-28, 28)
        pwd, salt = random.choice([None, "x"]), None

        if pwd:
            salt = urandom(16)
            kdf = PBKDF2HMAC(hashes.SHA256(), 32, salt, 32)
            key = kdf.derive(pwd.encode("UTF-8"))
            f = Fernet(base64.urlsafe_b64encode(key))
            msg = f"START ENCRYPTION - {msg} - END ENCRYPTION"
            msg = f.encrypt(msg.encode("UTF-8")).hex()
            pwd, salt = key.hex(), salt.hex()

        dbHandler.insert_message(sender, title, msg, avail,pwd, salt)
    print("Now done populating the database.")



if __name__ == "__main__":
    dbHandler = DBHandler()
    match input("1: delete, 2: populate, enter option: "):
        case "1":
            delete_messages(dbHandler)
        case "2":
            populate_random_data(dbHandler, 50)
        case _:
            print("Unavailable option chosen....")
    




# def populate_random_data(dbHandler, rows):
#     print(f"Now populationg database with {rows} rows")
#     for _ in range(rows):
#         sender = "".join(random.choices(asclett, k=random.randint(5, 20)))
#         title = " ".join("".join(random.choices(asclett, k=random.randint(3, 10))) for _ in range(3))
#         msg = " ".join("".join(random.choices(asclett, k=random.randint(1, 10))) for _ in range(random.randint(10, 100)))
#         avail = random.randint(-28, 28)
#         pwd, salt = random.choice([None, "x"]), None

#         if pwd:
#             hash_iterations = 10
#             salt = urandom(16) if not salt else salt
#             bin_pwd = pwd.encode("UTF-8")
#             pwd_hash = pbkdf2_hmac("sha256", bin_pwd, salt, hash_iterations)
#             pwd, salt = pwd_hash.hex(), salt.hex()

#         dbHandler.insert_message(sender, title, msg[:1000], avail, pwd, salt)
#     print("Now done populating the database.")
