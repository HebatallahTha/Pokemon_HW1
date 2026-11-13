"""
CIS427 PA2 - SQL part, Heba.
Based on my PA1 database script. 
"""

import math
import os
import sqlite3
import threading

DB_FILE = "pokemon_store.db"
DEFAULT_STARTING_BALANCE = 100.0

# limits so huge numbers can't overflow SQLite (the PA1 crash we got minused points for)
MAX_COUNT = 1_000_000 #do max xoutns so its not out of range, he wants us to make it actual so I did a mil as max for both
MAX_MONEY = 1_000_000_000.0
# the requred users from pa2, their user_name, password, is_root, first name, last name. Only root has is_root = 1. (basically a fake boolean)
REQUIRED_USERS = [
    ("root", "root01", 1, "Root", "User"),
    ("mary", "mary01", 0, "Mary", "Smith"),
    ("john", "john01", 0, "John", "Doe"),
    ("moe",  "moe01",  0, "Moe",  "Howard"),
]

# first line of every reply is needs to have a status code.
STATUS_TEXT = {
    200: "OK",
    210: "the server is about to shutdown  ......",
    400: "invalid command",
    401: "not authorized",
    403: "Wrong UserID or Password",
    404: "Your search did not match any records",
}

conn = None                    # only ONE shared connection, opened in init_db() this is the main diff from PA1, conn = connection.
db_lock = threading.Lock()     # only one client thread may use it at a time (remember what the textbook said!!!)

#here this func is our main datab func like pa1
def init_db():
    """
    it opens up the database, create the tables, and create the 4 users if none exist. 
    """
    global conn #made it global so all functions can use it (like what we did in C++ proj)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)  # False = threads are allowed to share it
    conn.execute("PRAGMA foreign_keys = ON;") #gives foreign key constraints
    conn.row_factory = sqlite3.Row
    #similar to PA1
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            first_name TEXT,
            last_name TEXT,
            user_name TEXT NOT NULL,
            password TEXT,
            usd_balance DOUBLE NOT NULL,
            is_root INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS Pokemon_cards (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            card_name TEXT NOT NULL,
            card_type TEXT NOT NULL,
            rarity TEXT NOT NULL,
            count INTEGER,
            owner_id INTEGER,
            FOREIGN KEY (owner_id) REFERENCES Users(ID)
        );
    """)
    conn.commit()

    # since no users yet make the 4 req ones, n = number of users currently in the database 
    n = conn.execute("SELECT COUNT(*) AS n FROM Users;").fetchone()["n"]
    if n == 0: # if there are no users, create the 4 required ones
        for name, pw, is_root, first, last in REQUIRED_USERS: #get the required users by our table
            conn.execute(
                "INSERT INTO Users (email, first_name, last_name, user_name, "
                "password, usd_balance, is_root) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (f"{name}@example.com", first, last, name, pw,
                 DEFAULT_STARTING_BALANCE, is_root))
        conn.commit()
        print("NO USERS WERE FOUND. Created root, mary, john and moe.") #tell the user that the 4 required users were created

#Closing function. just close.
def close_db():
    """
    when we shutdown we can use this func
    """
    conn.close()


# result function to get a dictionary of the code and the mesage and ANY extra data.

def result(code, message="", **extra):
    """
    just needed to get the code, mess, and extra data. like what I did in prev proj in c++
    """
    return {"code": code, "message": message, **extra}


def format_reply(res): #just sent in the result
    """
    the message ends in \\n. so no minus poits hoepfully
    """
    reply = f"{res['code']} {STATUS_TEXT[res['code']]}\n" #starts with the code and status text
    if res["message"]: #if there is a message, add it to the reply
        reply += res["message"] + "\n" #add the message and a newline at the end
    return reply #return the reply mes

# created a safety function so that only one thread can use the db at a time
def safe(func):
    """
    now any error will return 400 instead of a crach like in PA1.
    """
    def wrapper(*args): #take in any number of arguments
        with db_lock: #only one thread can use the database at a time
            try: #try to run the function
                return func(*args)
            except Exception as e: #catch any errors
                conn.rollback()          # undo any half-finished change in the database
                return result(400, f"Error: {e}") #return a 400 error with the error message
    return wrapper

# convert text to a valid money amount, rounded to cents, or None if invalid made simple parsing basically for money and count
def to_money(text, allow_zero=False):
    """
     so now a text will become a float rounded to cents (2 decimal places only), or None if bad (not a number, nan, inf, negative, too big wtv the issue).
    """
    try: #try to convert the value to a float
        v = float(text)
    except ValueError: #catch any errors
        return None #return None if the value is not a valid number
    if not math.isfinite(v) or v < 0 or v > MAX_MONEY or (v == 0 and not allow_zero): #check if the value is invalid like going over 1 mil
        return None #return None if the value is invalid
    return round(v, 2) #return the value rounded to 2 decimal places 

# to count the number of items, rounded to an integer, or None if invalid
def to_count(text):
    """
    so now a text will become an integer from 1 to MAX_COUNT, or None if bad (not a number, too small, too big).
    """
    try: #try to convert the value to an integer
        v = int(text)
    except ValueError: #catch any errors
        return None #return None if the value is not a valid number
    return v if 1 <= v <= MAX_COUNT else None #return the value if it is within the valid range, if not return None

#get the user by the id kinda like pa1
def get_user_by_id(user_id): #just get the user by their ID 
    return conn.execute("SELECT * FROM Users WHERE ID = ?;", (user_id,)).fetchone()

#get the card by the name and owner id
def get_card(card_name, owner_id): #just get the card by its name and owner ID
    return conn.execute(
        "SELECT * FROM Pokemon_cards WHERE card_name = ? AND owner_id = ?;",
        (card_name, owner_id)).fetchone()

#needed to format for display like pa1 kinda
def format_table(rows):
    """
    rows have the usm rom owner cols.
    """
    lines = [f"{'ID':<4}{'Card Name':<16}{'Type':<12}{'Rarity':<12}{'Count':<7}{'Owner':<10}"]
    for r in rows:
        lines.append(f"{r['ID']:<4}{r['card_name']:<16}{r['card_type']:<12}"
                     f"{r['rarity']:<12}{r['count']:<7}{r['user_name']:<10}")
    return lines


# run inside safety wrapper, need to ensure safety check passed. didnt want to rewrite = safe(handle) so used teh decor
@safe
def handle_login(args): #just handle the login command
    """
    if correct, user is the session.
    """
    if len(args) != 2: #check args are added/
        return result(400, "Format: LOGIN <UserID> <Password>") #return error if args are not added
    row = conn.execute("SELECT * FROM Users WHERE user_name = ? AND password = ?;",
                       (args[0], args[1])).fetchone() #get the user by their username and password
    if row is None: #check if the user was found
        return result(403) #return error if the user was not found
    return result(200, user={"id": row["ID"], "user_name": row["user_name"],
                             "is_root": bool(row["is_root"])}) #return success with the user session is_root = true

#same safety check
@safe
def handle_buy(session, args): #just handle the buy command
    """
    buy a card 
    """
    if session is None: #check if the user is logged in
        return result(401, "You must LOGIN first") #return error if the user is not logged in
    if len(args) != 5: #check args are added/
        return result(400, "Format: BUY <name> <type> <rarity> <price> <count>") #return error if args are not added
    card_name, card_type, rarity = args[0], args[1], args[2] #get the card name, type, and rarity
    price = to_money(args[3], allow_zero=True) #get the card price
    count = to_count(args[4]) #get the card count
    if price is None: #check if the price is valid
        return result(400, "Price must be a valid non-negative number") #return error if the price is invalid
    if count is None: #check if the count is valid
        return result(400, f"Count must be a whole number from 1 to {MAX_COUNT}") #return error if the count is invalid

    user = get_user_by_id(session["id"]) #get the user by their ID
    total_cost = round(price * count, 2) #calculate the total cost of the cards
    if user["usd_balance"] < total_cost: #check if the user has enough balance
        return result(400, "Not enough balance") #return error if the user does not have enough balance
    new_balance = round(user["usd_balance"] - total_cost, 2) #calculate the new balance after the purchase

    existing = get_card(card_name, user["ID"]) #get the existing card by its name and owner ID
    if existing: #check if the user already owns the card
        new_count = existing["count"] + count #calculate the new card count
        conn.execute("UPDATE Pokemon_cards SET count = ?, card_type = ?, rarity = ? "
                     "WHERE ID = ?;", (new_count, card_type, rarity, existing["ID"])) #update the existing card
    else: #check if the user does not already own the card
        new_count = count #set the new card count
        conn.execute("INSERT INTO Pokemon_cards (card_name, card_type, rarity, count, "
                     "owner_id) VALUES (?, ?, ?, ?, ?);",
                     (card_name, card_type, rarity, count, user["ID"])) #add the new card
    conn.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?;", (new_balance, user["ID"])) #update the user balance
    conn.commit() #save the changes to the db
    return result(200, f"BOUGHT: New balance: {new_count} {card_name}. " #return success message like PA1 
                       f"User USD balance ${new_balance:.2f}") #return the user's new USD balance


@safe
def handle_sell(session, args): #handle the sell command
    """
    sell gives the name counts and price
    """
    if session is None: #check if the user is logged in
        return result(401, "You must LOGIN first") #return error if the user is not logged in
    if len(args) != 3: #check if the command has the correct number of arguments
        return result(400, "Format: SELL <name> <count> <price>") #return error if the command format is invalid
    card_name = args[0] #get the card name from the command arguments
    count = to_count(args[1]) #get the card count from the command arguments
    price = to_money(args[2], allow_zero=True) #get the card price from the command arguments
    if count is None: #check if the card count is valid
        return result(400, f"Count must be a whole number from 1 to {MAX_COUNT}") #return error if the card count is invalid
    if price is None: #check if the card price is valid
        return result(400, "Price must be a valid non-negative number") #return error if the card price is invalid

    user = get_user_by_id(session["id"]) #get the user from the database
    card = get_card(card_name, user["ID"]) #get the card from the database
    if card is None or card["count"] < count: #check if the card exists and has enough balance
        return result(400, "Not enough Pokemon balance") #return error if the card does not exist or has insufficient balance

    new_count = card["count"] - count #calculate the new card count
    new_balance = round(user["usd_balance"] + price * count, 2) #calculate the new USD balance
    if new_count == 0: #check if all cards were sold
        conn.execute("DELETE FROM Pokemon_cards WHERE ID = ?;", (card["ID"],)) #delete the card from the database
    else: #update the remaining card count
        conn.execute("UPDATE Pokemon_cards SET count = ? WHERE ID = ?;",
                     (new_count, card["ID"]))
    conn.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?;", (new_balance, user["ID"]))
    conn.commit()
    return result(200, f"SOLD: New balance: {new_count} {card_name}. "
                       f"User's balance USD ${new_balance:.2f}")


@safe
def handle_deposit(session, args): 
    """
    deposit amount into the user's USD balance, similar to funcs above.
    """
    if session is None:
        return result(401, "You must LOGIN first")
    if len(args) != 1:
        return result(400, "Format: DEPOSIT <amount>")
    amount = to_money(args[0])
    if amount is None:
        return result(400, "Deposit amount must be a positive number.")

    user = get_user_by_id(session["id"]) #get the user from the database
    new_balance = round(user["usd_balance"] + amount, 2) #calculate the new USD balance
    conn.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?;", (new_balance, user["ID"]))
    conn.commit()
    return result(200, f"Deposit successful. New User balance ${new_balance:.2f}")


@safe
def handle_list(session, args):
    """ 
    this function makes sure the root sees every card
    a regular user sees only their own."""
    if session is None:
        return result(401, "You must LOGIN first")
    if len(args) != 0:
        return result(400, "Format: LIST")
 
    query = ("SELECT c.ID, c.card_name, c.card_type, c.rarity, c.count, u.user_name "
             "FROM Pokemon_cards c JOIN Users u ON c.owner_id = u.ID ")
    if session["is_root"]:
        rows = conn.execute(query + "ORDER BY c.ID;").fetchall() #get all cards from the database
        header = "The list of records in the cards database:"
    else:
        rows = conn.execute(query + "WHERE c.owner_id = ? ORDER BY c.ID;",
                            (session["id"],)).fetchall() #get the current user's cards from the database
        header = (f"The list of records in the Pokémon cards table for "
                  f"current user, {session['user_name']}:")
    return result(200, "\n".join([header] + format_table(rows)))


@safe
def handle_balance(session, args): #handle the balance command
    """
    logged in users balance
    """
    if session is None:
        return result(401, "You must LOGIN first")
    if len(args) != 0:
        return result(400, "Format: BALANCE")
    user = get_user_by_id(session["id"]) #get the user from the database
    return result(200, f"Balance for user {user['first_name']} {user['last_name']}: "
                       f"${user['usd_balance']:.2f}")


@safe

def handle_lookup(session, args): #handle the lookup command
    """
    searches the logged-in user's cards only.
    """
    if session is None:
        return result(401, "You must LOGIN first")
    if len(args) != 1:
        return result(400, "Format: LOOKUP <card name>")

    #needed to be case insensitive
    rows = conn.execute(
        "SELECT c.ID, c.card_name, c.card_type, c.rarity, c.count, u.user_name "
        "FROM Pokemon_cards c JOIN Users u ON c.owner_id = u.ID "
        "WHERE c.owner_id = ? AND instr(lower(c.card_name), lower(?)) > 0 "
        "ORDER BY c.ID;", (session["id"], args[0])).fetchall()
    if not rows:
        return result(404)
    head = f"Found {len(rows)} match" + ("" if len(rows) == 1 else "es")
    return result(200, "\n".join([head] + format_table(rows))) #return the matching cards


# test cases for fake users and overflow to see if it works now
if __name__ == "__main__":
    if os.path.exists(DB_FILE): #my db file
        os.remove(DB_FILE)
    init_db()

    def show(label, res):
        print(f"--- {label}\n{format_reply(res)}") #print the test case label and result, easier to see/read

    show("not logged in", handle_list(None, []))
    show("bad login", handle_login(["john", "wrong"]))
    john = handle_login(["john", "john01"])["user"]
    root = handle_login(["root", "root01"])["user"]

    show("BUY", handle_buy(john, ["Pikachu", "Electric", "Common", "19.99", "2"]))
    show("BUY Charizard", handle_buy(john, ["Charizard", "Fire", "Rare", "5", "6"]))
    show("SELL", handle_sell(john, ["Pikachu", "1", "34.99"]))
    show("SELL too many", handle_sell(john, ["Pikachu", "50", "1"]))
    show("DEPOSIT", handle_deposit(john, ["12.34"]))
    show("DEPOSIT bad", handle_deposit(john, ["-5"]))
    show("BALANCE", handle_balance(john, []))
    show("LIST john", handle_list(john, []))
    show("LIST root", handle_list(root, []))
    show("LOOKUP Char", handle_lookup(john, ["Char"]))
    show("LOOKUP none", handle_lookup(john, ["random_card"]))
    show("BUY too short", handle_buy(john, ["Charizard", "Fire"]))
    show("BUY nan price", handle_buy(john, ["X", "Fire", "Rare", "nan", "1"]))
    show("BUY huge count", handle_buy(john, ["X", "Fire", "Rare", "1", "9" * 30]))
    show("BUY too expensive", handle_buy(john, ["X", "Fire", "Rare", "999999", "1"]))
    close_db()
