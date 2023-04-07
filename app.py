from bottle import Bottle, run, error, template, request, response, redirect, static_file
import bottle
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.exceptions import InvalidKey
from base64 import urlsafe_b64encode
from os import urandom
import json
import db_handler


app = Bottle()
bottle.debug(True)
dbHandler = db_handler.DBHandler()


CONTENT_RESTRICTIONS = {
    "sender": (5, 20),
    "title": (5, 30),
    "available": (1, 28),
    "message": (1, 1000),
}

SORTING_PARAMS = {
    "Sender A-Z": ("sender", "ASC"),
    "Sender Z-A": ("sender", "DESC"),
    "Title A-Z": ("title", "ASC"),
    "Title Z-A": ("title", "DESC"),
    "Message A-Z": ("message", "ASC"),
    "Message Z-A": ("message", "DESC"),
    "Posted First-Last": ("posted", "ASC"),
    "Posted Last-Fist": ("posted", "DESC"),
    "Availablility Shortest-Longest": ("available", "ASC"),
    "Availablility Longest-Shortest": ("available", "DESC"),
}

MSG_FILTER_KEYS = ["sender", "title", "message"]

DEFAULT_SORT = "Posted Last-Fist"
DEFAUL_DB_SORT = (DEFAULT_SORT, SORTING_PARAMS[DEFAULT_SORT])
MESSAGES_PER_PAGE = 5
TEXT_ENCODING = "UTF-8"
TOTAL_PAGES_IN_DB = 5



def get_key_deriv_func(salt=None):
    salt = salt or urandom(16)
    return (PBKDF2HMAC(hashes.SHA256(), 32, salt, 32), salt)


def get_fernet(pwd_key):
    return Fernet(urlsafe_b64encode(pwd_key))


def hash_password(password, salt=None):
    pwd_gen, salt = get_key_deriv_func(salt)
    pwd_key = pwd_gen.derive(password.encode(TEXT_ENCODING))
    return (pwd_key, salt)


def encrypt_incoming_message(pwd_key, msg):
    fern = get_fernet(pwd_key)
    enc_msg = fern.encrypt(msg.encode(TEXT_ENCODING))
    return enc_msg.hex()


def decrypt_outgoing_message(pwd_key, msg):
    fern = get_fernet(pwd_key)
    dec_msg = fern.decrypt(bytes.fromhex(msg))
    return dec_msg.decode(TEXT_ENCODING)


def validate_field(field, content_length):
    values = CONTENT_RESTRICTIONS[field]
    return content_length >= values[0] and content_length <= values[1]


def validate_form_input(form):
    valid_fields = []
    
    sender = form.get("sender")
    valid_fields.append(validate_field("sender", len(sender)))
    
    title = form.get("title")
    valid_fields.append(validate_field("title", len(title)))
    
    message = form.get("message")
    valid_fields.append(validate_field("message", len(message)))
    
    available = form.get("available")
    values = CONTENT_RESTRICTIONS["available"]
    valid_fields.append(int(available) >= values[0] and int(available) <= values[1])
    
    password = salt = None

    if (pwd := form.get("password")):
        pwd_key, salt = hash_password(pwd)
        password, salt = pwd_key.hex(), salt.hex()
        message = encrypt_incoming_message(pwd_key, message)

    return (sender, title, message, available, password, salt) if all(valid_fields) else None


def validate_password(row_id, password):
    db_pwd, db_salt = dbHandler.get_password_and_salt(row_id)
    kdf, _ = get_key_deriv_func(bytes.fromhex(db_salt))
    pwd_key =  bytes.fromhex(db_pwd)

    try:
        kdf.verify(password.encode(TEXT_ENCODING), pwd_key)
        return pwd_key
    except InvalidKey:
        return None


def decrypt_db_message(row_id, password):
    decr_resp = {"status": "error", "message": "The password you enetered is INCORRECT!"}
    if (pwd_key := validate_password(row_id, password)):
        enc_msg = dbHandler.get_message_content(row_id)
        decr_resp["status"] = "success"
        decr_resp["message"] = decrypt_outgoing_message(pwd_key, enc_msg)

    return decr_resp


def get_filter_params(filter):
    return (filter["sender"], filter["title"], filter["message"]) if filter else ("", "", "")


def get_page_count(num_msgs):
    return num_msgs // MESSAGES_PER_PAGE + (num_msgs % MESSAGES_PER_PAGE > 0)


@app.get("/static/js/<filename:re:.*\.js>")
def get_javascript(filename):
    return static_file(filename, root="static/js")


@app.get("/static/css/<filename:re:.*\.css>")
def get_css(filename):
    return static_file(filename, root="static/css")


@app.get("/")
@app.get("/<page:int>")
def index(sort=None, filter=None, page=1):
    global TOTAL_PAGES_IN_DB

    if page <= 0 or page > int(TOTAL_PAGES_IN_DB * 1.1): return redirect("/")

    sorting, sort_params = (sort, SORTING_PARAMS[sort]) if sort else DEFAUL_DB_SORT
    filtering, filter_params = (filter or {}, get_filter_params(filter))

    #print(f"SORTING: {sorting}, PARAMS: {sort_params}")
    num_msgs, tot_msgs, messages = dbHandler.get_messages(*sort_params, MESSAGES_PER_PAGE, (page - 1) * MESSAGES_PER_PAGE, *filter_params)
    TOTAL_PAGES_IN_DB = get_page_count(tot_msgs)

    data = {
        "num_msgs": num_msgs,
        "tot_msgs": tot_msgs,
        "curr_page": page,
        "pages": get_page_count(num_msgs),
        "restrictions": CONTENT_RESTRICTIONS, 
        "messages": messages, 
        "dateformat": "%Y-%m-%d %H:%M:%S",
        "sorting_options": SORTING_PARAMS.keys(),
        "sorting_on": sorting,
        "filtering_on": filtering,
    }

    return template("index", data)


@app.post("/")
def message_submit():
    form_data = validate_form_input(request.forms)
    if form_data:
        dbHandler.insert_message(*form_data)
        return redirect("/")
    else:
        return "Invalid form input.... Not going to fail gracefully because you have bypassed the html form validators...."


@app.post("/<page:int>")
def change_page(page):
    sort = request.forms.get("sorting", None)
    filter = {key: request.forms.get(key, "") for key in MSG_FILTER_KEYS}

    return index(sort=sort, filter=filter, page=page)


@app.post("/decrypt")
def decrypt_message():
    data = request.json
    # print(f"Incoming POST data from javascript button click: {data}")

    decr_resp = decrypt_db_message(data["row_id"], data["password"])
    #print(decr_resp)

    response.content_type = 'application/json'
    return json.dumps(decr_resp)


@app.error(404)
def error404(error):
    print("ERROR HAPPENED!")
    print(error)
    #return f"What ever you're looking for is NOT here... {error}"
    return f"What ever you're looking for is NOT here..."


run(app, host='localhost', port=8080)#, reloader=True)


