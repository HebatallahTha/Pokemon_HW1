"""
Hello Professor, this is the database part of our assignment. 
I used Python since im more comfortable with it. 
Sorry if my comments arent as funny as a I thought they might be . . . 
Thanks ~Hebatallah Tharhan
"""

import sqlite3
import os

#basic setups

# Name of the SQLite database file. Change if you want a different name/path.
DB_FILE = "pokemon_store.db" #my lite database file, just put a simple name :)


DEFAULT_STARTING_BALANCE = 100.0 #each user will start w 100 bucks initallly



#using sqlite 3 to make the tables
def init_db():
    """
    okay so for my function I created it
    because I needed to create theusers and the pke_cards tables for users
    if they dont already exsist in the database.
    """
    conn = sqlite3.connect(DB_FILE, check_same_thread=False) #opens my db file. (creating it if not created before)
    # same thread is set to false to allow multply threads + yt tutorial recommended it. 
    conn.execute("PRAGMA foreign_keys = ON;") #forces it to ensure there is a real connection
    conn.row_factory = sqlite3.Row #make it readable by name, yt tut reccomendation aswell :)
    #conn = connection
    cur = conn.cursor() #creates a cursor object to execute my SQL commands
        #from our pdf we have the code for the Users table.
    cur.execute("""
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
        #from pdf we have poke table aswell!
    cur.execute("""
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
        #using execute to run our sql cmnd. remember to commit because it wont save changes (learned the hard way :<)
    conn.commit()

    # making my user if not existing... yet.
    user_count = conn.execute("SELECT COUNT(*) AS n FROM Users;").fetchone()["n"]
    #using sql to select the number of rows exsist in my db, similar to prev guitar assignment. 
    # just set it as n for easy ref.
    # need to use fetchone() to get the first row of the result, really different to just straight sql coding I know...
    if user_count == 0: 
    #if we dont have a user, make one using the sample data we got 
    # in our pdf. I just used the first guy! Placeholders were used for my vals.
        conn.execute("""
            INSERT INTO Users (email, first_name, last_name, user_name,
                                password, usd_balance, is_root)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, ("j.doe@abc.com", "john", "doe", "j_doe",
              "Passwrd4", DEFAULT_STARTING_BALANCE, 1))
        conn.commit() #REMEMBER TO COMMIT AT ENDDD!
        #easier to show creation for our screen recording ->
        print(f"NO USERS WERE FOUND. Created a default user 'j_doe' "
              f"(ID=1) with rounded balance ${DEFAULT_STARTING_BALANCE:.2f}") 

    conn.close() #shutdown connection once done and we know a user is there.



def get_user_by_id(owner_id):
    #similar to above.
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    #selecting all my cols from user table where my id = owner_id.
    row = conn.execute(
        "SELECT * FROM Users WHERE ID = ?;", (owner_id,) #had error bc I didnt make a tuple b4
    ).fetchone() #there should only be 1 match
    conn.close()
    return row


def update_user_balance(owner_id, new_balance):
    #same three lines (prob should have made this a common helper func ... sorry to my code reviewer :<)
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    #now im literally just updatting by setting the users 
    # $ balance to the new value 
    #the id needs to be the owners id so it doesnt update all of em
    conn.execute(
        "UPDATE Users SET usd_balance = ? WHERE ID = ?;",
        (new_balance, owner_id)
    )
    conn.commit()
    conn.close()



def get_card(card_name, owner_id):
    #same 3 lines
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    #select all rows from my pke table where my card name and owner id match.
    #so im checking does this user have this card?? (is it true poke cards are expensive now??)
    row = conn.execute(
        "SELECT * FROM Pokemon_cards WHERE card_name = ? AND owner_id = ?;",
        (card_name, owner_id)
    ).fetchone()
    conn.close()
    return row


def list_cards_for_user(owner_id):
    #same three lines againn
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    #selecting all my rows from my poke table where my owner id matches. i wanna see all his/hers cards.
    rows = conn.execute(
        "SELECT * FROM Pokemon_cards WHERE owner_id = ?;", (owner_id,)
    ).fetchall() #GET ALL NOT ONE!
    conn.close()
    return rows


#Mariam your server will use these!
def handle_buy(card_name, card_type, rarity, price, count, owner_id):
    
    # did all this validation just so my user doesnt crash our server with
    #bad inputs and we get -10 pts.
    try:
        price = float(price) #prices are my floats in case of decimals
        count = int(count) #count will always be an integer
        owner_id = int(owner_id) #same w owner id
        #IF AN ERROR THROW A MESSAGE, used bool to indicate failure/success
    except (ValueError, TypeError):
        return {"ok": False, "code": 403,
                "message": "ERRRRROR: price/count/owner_id must be numeric!"}
    #you need to buy a postive and at least 1 card girl
    if count <= 0 or price < 0:
        return {"ok": False, "code": 403,
                "message": "ERROR NEED TO BUY 1+ CARDS: count must be > 0 and price >= 0"}
    #check if the user exists before proceeding with the purchase
    user = get_user_by_id(owner_id)
    if user is None:
        return {"ok": False, "code": 400,
                "message": f"user {owner_id} doesn't exist"}
    #calculate the total cost of the purchase, just my prict X amt
    total_cost = price * count
    #if my user is broke, they cant buy it. tough luck buddy.
    if user["usd_balance"] < total_cost:
        return {"ok": False, "code": 400, "message": "Not enough balance"}
    #needing to update the balance to my users new usd baalnce $$$
    new_balance = user["usd_balance"] - total_cost
    # get the card 
    existing = get_card(card_name, owner_id)

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    
    #need to check if its exisitng bc we might be adding 
    # to an existing card entry
    if existing:
        new_count = existing["count"] + count #increment my count
        conn.execute(
            "UPDATE Pokemon_cards SET count = ?, card_type = ?, rarity = ? "
            "WHERE ID = ?;",
            (new_count, card_type, rarity, existing["ID"])
        )
        #updating the poke set with the amt, the type, if rare
        #if not exsitng my new count is MY COUNT and similar for the rest.
    else:
        new_count = count
        conn.execute(
            "INSERT INTO Pokemon_cards (card_name, card_type, rarity, count, owner_id) "
            "VALUES (?, ?, ?, ?, ?);",
            (card_name, card_type, rarity, count, owner_id)
        )
    #executing to update the new balance for the customer id.
    conn.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?;",
                 (new_balance, owner_id))
    conn.commit()
    conn.close()
    #yay test case passed!
    return {
        "ok": True, "code": 200,
        "message": f"BOUGHT: Your new balance and card name are: {new_count} {card_name}. "
                   f"User USD balance ${new_balance:.2f}",
        "new_count": new_count, "new_balance": new_balance
    }


def handle_sell(card_name, count, price, owner_id):
    #really super duper similar to above.
    try:
        count = int(count)
        price = float(price)
        owner_id = int(owner_id)
    except (ValueError, TypeError):
        return {"ok": False, "code": 403,
                "message": "ERROR: count/price/owner_id must be numeric"}

    if count <= 0 or price < 0:
        return {"ok": False, "code": 403,
                "message": "ERROR, need to buy 1+ cards: count must be > 0 and price >= 0"}
    #grabbing my user
    user = get_user_by_id(owner_id)
    if user is None:
        #no user = fault
        return {"ok": False, "code": 400,
                "message": f"user {owner_id} doesn't exist"}
    #grab my card
    card = get_card(card_name, owner_id)
    if card is None or card["count"] < count:
        return {"ok": False, "code": 400,
                "message": "Not enough Pokemon balance"}

    new_card_count = card["count"] - count
    proceeds = price * count
    new_balance = user["usd_balance"] + proceeds

    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row

    if new_card_count == 0:
        # deleting the row once he sold them all. just a better way then count = 0 so I dont have that in my rows.
        conn.execute("DELETE FROM Pokemon_cards WHERE ID = ?;", (card["ID"],))
    else:
        conn.execute("UPDATE Pokemon_cards SET count = ? WHERE ID = ?;",
                     (new_card_count, card["ID"]))

    conn.execute("UPDATE Users SET usd_balance = ? WHERE ID = ?;",
                 (new_balance, owner_id))
    conn.commit()
    conn.close()
    #PASS TEST CASE YAY
    return {
        "ok": True, "code": 200,
        "message": f"SOLD, congrats: New balance: {new_card_count} {card_name}. "
                   f"User's balance USD ${new_balance:.2f}",
        "new_count": new_card_count, "new_balance": new_balance
    }


def handle_list(owner_id):
    #again with the error handles
    try:
        owner_id = int(owner_id)
    except (ValueError, TypeError):
        return {"ok": False, "code": 403,
                "message": "ERROR: owner_id must be numeric"}
    #my user lookup
    user = get_user_by_id(owner_id)
    if user is None:
        return {"ok": False, "code": 400,
                "message": f"user {owner_id} doesn't exist"}
    #my row lookup
    rows = list_cards_for_user(owner_id)

    lines = [f"Record list of cards for user: {owner_id}:"]
    #adding the header id, card name, type, raring, count, and user id.
    lines.append(f"{'ID':<4}{'Card Name':<15}{'Type':<12}{'Rarity':<12}{'Count':<7}{'OwnerID':<8}")
    #looping for each card row the owner has.
    for r in rows:
        lines.append(f"{r['ID']:<4}{r['card_name']:<15}{r['card_type']:<12}"
                      f"{r['rarity']:<12}{r['count']:<7}{r['owner_id']:<8}")

    return {"ok": True, "code": 200, "message": "\n".join(lines), "rows": rows}

#finally at long last, the last func :)
def handle_balance(owner_id):
    #error handls
    try:
        owner_id = int(owner_id)
    except (ValueError, TypeError):
        return {"ok": False, "code": 403,
                "message": "ERROR: owner_id must be numeric"}

    user = get_user_by_id(owner_id)
    if user is None:
        return {"ok": False, "code": 400,
                "message": f"user {owner_id} doesn't exist"}
    #grabbing users full gov name, no middle name
    full_name = f"{user['first_name']} {user['last_name']}".strip()
    return {
        "ok": True, "code": 200,
        "message": f"Balance for user {full_name}: ${user['usd_balance']:.2f}",
        "balance": user["usd_balance"]
    }


#testing to see if it works.
if __name__ == "__main__":
    #clean start
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    init_db()

    print(handle_buy("Pikachu", "Electric", "Common", 19.99, 2, 1))
    print(handle_sell("Pikachu", 1, 34.99, 1))
    print(handle_list(1))
    print(handle_balance(1))
    print(handle_buy("Pikachu", "Electric", "Common", 999999, 1, 1))  # broke user
    print(handle_balance(42))  # fake user