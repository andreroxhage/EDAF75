from urllib.parse import quote, unquote
import sqlite3
import datetime
import os

from bottle import request, response, run, post, get
from requests import HTTPError

db = sqlite3.connect("db.sqlite")
PORT = 8888

# Reset the database tables
@post('/reset')
def reset():
    # Close the connection to the database
    # Delete the old db.sqlite file if it exists
    if os.path.exists("db.sqlite"):
        os.system("sqlite3 db.sqlite < create-schema.sql")

    db = sqlite3.connect("db.sqlite")

    response.status = 205
    return {"location": "/"}

@post('/customers')
def postCustomers():
    c = db.cursor()
    data = request.json
    name = data['name']
    address = data['address']

    try:
        c.execute(
            """
            INSERT
            INTO customers (name, address)
            VALUES(?, ?)
            """, (name, address)
        )
    except sqlite3.Error as e:
        response.status = 400
        return "Illegal insertion of customer"

    db.commit()
    response.status = 201
    return { "location": f"/customers/{quote(name)}" }

@get('/customers')
def getCustomers():
    c = db.cursor()

    c.execute(
        """
        SELECT  name, address
        FROM    customers
        """
    )
    found = [{"name": name, "address": address}
             for name, address in c]
    response.status = 200
    return {"data": found}

@post('/cookies')
def postCookies():
    c = db.cursor()
    data = request.json

    name = data['name']
    recipe = data['recipe']

    try:
        c.execute(
            """
            INSERT 
            INTO cookies (name)
            VALUES (?)
            """, (name,)
        )

        for item in recipe:        
            ingredient = item['ingredient']
            amount = item['amount']
            c.execute(
                """
                INSERT
                INTO recipes (amount, ingredient, name)
                VALUES (?, ?, ?)
                """, (amount, ingredient, name)
            )
    except sqlite3.Error as e:
        response.status = 400
        return "Illegal insertion of name or recipe or ingredients doesnt exist:"

    db.commit()
    response.status = 201
    return { "location": f"/cookies/{quote(name)}" }

@get('/cookies')
def getCookies():
    c = db.cursor()

    c.execute(
        """
        SELECT cookies.name, count(id)
        FROM cookies
        LEFT JOIN pallets
        ON cookies.name = pallets.name AND pallets.blocked = 0
        GROUP BY cookies.name
        """
    )
    found = c.fetchall()
    if not found:
        response.status = 404
        return "Invalid JSON or no cookies available"

    cookies = [{'name': f[0], 'pallets': f[1]} for f in found]
    response.status = 200
    return {"data": cookies}

@get('/cookies/<name>/recipe')
def getCookies(name):
    c = db.cursor()

    c.execute(
        """
        SELECT ingredient, amount, unit
        FROM recipes
        WHERE name = ?
        """, [name]
    )

    found = c.fetchone()
    if not found:
        response.status = 404
        return {"data": []}
    
    db.commit()
    response.status = 200
    data = [{"ingredient": row[0], "amount": row[1], "unit": row[2]} for row in found]
    return {"data:": data}


# function is called when a pallet of a certain cookie is about to be produced.
# The type of cookie is set from JSON data
@post('/pallets')
def postPallets():
    c = db.cursor()
    data = request.json

    name = data['cookie']

    currentDate = datetime.datetime.now()
    print(currentDate)

    # Try to produce a pallet of a certain cookie
    try:
        c.execute(
            """
            INSERT
            INTO pallets(name, productionDate)
            VALUES (?, ?)
            RETURNING id
            """, (name, currentDate)
        )
        id = c.fetchone()[0]
        db.commit()
        response.status = 201
        return {"location": f"/pallets/{id}"}
    except sqlite3.Error as e:
        response.status = 422
        print(e)
        return "Not enough ingrediences..."

from bottle import get, request, response
from urllib.parse import unquote

@get('/pallets')
def getPallets():
    c = db.cursor()

    query = """
        SELECT id, name, productionDate, blocked
        FROM pallets
        WHERE 1=1
        """
    params = []

    if request.query.cookie:
        query += " AND name = ?"
        params.append(unquote(request.query.cookie))

    if request.query.after:
        query += " AND productionDate > ?"
        params.append(unquote(request.query.after))

    if request.query.before:
        query += " AND productionDate < ?"
        params.append(unquote(request.query.before))

    c.execute(query, params)
    found = c.fetchall()

    if not found:
        response.status = 404
        return "Invalid JSON or no pallets available"

    data = [{"id": row[0], "cookie": row[1], "productionDate": row[2], "blocked": row[3]} for row in found]

    response.status = 200
    return {"data": data}

@post('/ingredients')
def postIngredients():
    c = db.cursor()
    data = request.json
    ingredient = data['ingredient']
    unit = data['unit']
    
    try:
        c.execute(
            """
            INSERT
            INTO ingredients (ingredient, unit)
            VALUES(?, ?)
            """,
            (ingredient, unit)
        )
        response.status = 201
        db.commit()
        return {'location': f"/ingredients/{quote(ingredient)}"}
    except:
        response.status = 400
        return {''}

@post('/ingredients/<ingredient>/deliveries')
def updateIngredient(ingredient):
    c = db.cursor()
    data = request.json
    deliveryTime = data['deliveryTime']
    quantity = data['quantity']

    decodedIngredient = unquote(ingredient)
    
    c.execute(
            """
            UPDATE ingredients
            SET deliveryTime = ? ,
                quantity = quantity + ?
            WHERE ingredient LIKE ?
            """, (deliveryTime, quantity, decodedIngredient)
    )

    c.execute(
        """
        SELECT ingredient, quantity, unit
        FROM ingredients
        WHERE ingredient = ?
        """, (decodedIngredient,)
    )
    found = c.fetchone()
    db.commit()
   
    response.status = 201

    found = {"ingredient": found[0], "quantity": found[1], "unit": found[2]}
    return {'location': f'data:{found}'}

@get('/ingredients')
def getIngredients():
    c = db.cursor()

    c.execute(
        """
        SELECT ingredient, quantity, unit
        FROM ingredients
        """
    )
    
    found = [{"ingredient": row[0], "quantity": row[1], "unit": row[2]}
             for row in c.fetchall()]

    db.commit()
    response.status = 200

    return {'data': found}

#after: only block pallets baked after (not including) a given date
#before: only block pallets baked before (not including) a given date
@post('/cookies/<cookie_name>/block')
def blockCookie(cookie_name):
    c = db.cursor()
    c.execute(
            """
            UPDATE pallets
            SET blocked = 1
            WHERE name = ?
            """, [cookie_name]
        )
    response.status = 205
    return {''}

@post('/cookies/<cookie_name>/unblock')
def unblockCookie(cookie_name):
    c = db.cursor()
    c.execute(
            """
            UPDATE pallets
            SET blocked = 0
            WHERE name = ?
            """, [cookie_name]
        )
    response.status = 205
    return {''}

run(host='localhost', port=PORT)