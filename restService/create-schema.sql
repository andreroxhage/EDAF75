PRAGMA foreign_keys = OFF;

DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS cookies;
DROP TABLE IF EXISTS cookie;
DROP TABLE IF EXISTS pallets;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS orderedCookies;
DROP TABLE IF EXISTS deliveries;




PRAGMA foreign_keys = ON;

CREATE TABLE ingredients (
    ingredient TEXT,
    quantity INT DEFAULT 0,
    deliveryTime DATE,
    unit TEXT NOT NULL,

    PRIMARY KEY (ingredient)
);


CREATE TABLE recipes (
    amount INT,
    ingredient TEXT,
    name TEXT,
    recipeId TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),

    FOREIGN KEY (name) REFERENCES cookies (name)
);

CREATE TABLE customers (
    name TEXT NOT NULL,
    customerId TEXT DEFAULT (lower(hex(randomblob(16)))),
    address TEXT NOT NULL,

    PRIMARY KEY (customerId)
);

CREATE TABLE cookies (
    name TEXT PRIMARY KEY
);




CREATE TABLE pallets (
    id TEXT DEFAULT (lower(hex(randomblob(16)))),
    name TEXT,
    productionDate DATE NOT NULL,
    blocked BOOLEAN DEFAULT 0,
    orderId TEXT,

    PRIMARY KEY (id),
    FOREIGN KEY (orderId) REFERENCES orders (orderId),
    FOREIGN KEY (name) REFERENCES cookies (name)    
);


CREATE TABLE orders (
    orderId TEXT DEFAULT (lower(hex(randomblob(16)))),
    deliveryDate DATE NOT NULL,
    deliveryId TEXT,
    customer TEXT NOT NULL,
    orderDate DATE DEFAULT (date('now')),
    orderStatus TEXT DEFAULT 'Pending',

    PRIMARY KEY (orderId),
    FOREIGN KEY (customer) REFERENCES customers (name),
    FOREIGN KEY (deliveryId) REFERENCES deliveries (deliveryId)
);

CREATE TABLE orderedCookies (
    quantity INT NOT NULL,
    orderId TEXT,
    name TEXT,

    FOREIGN KEY (orderId) REFERENCES orders (orderId),
    FOREIGN KEY (name) REFERENCES cookies (name)
);

CREATE TABLE deliveries (
    deliveryId TEXT DEFAULT (lower(hex(randomblob(16)))),
    delivaryDate DATE NOT NULL
);

DROP TRIGGER IF EXISTS palletProduction;
DROP TRIGGER IF EXISTS decreaseIngredients;
    
CREATE TRIGGER palletProduction
BEFORE INSERT ON pallets
BEGIN
    SELECT CASE 
        WHEN EXISTS (
            SELECT recipes.name
            FROM ingredients
            JOIN recipes USING (ingredient)
            WHERE name IS NEW.name AND 54*amount >= quantity
        )
        THEN RAISE(ROLLBACK, "Not enough ingredients for producing a pallet of cookies...")
        END;
END;

CREATE TRIGGER decreaseIngredients
AFTER INSERT ON pallets
BEGIN
    UPDATE ingredients
    SET quantity = quantity - 54*(
        SELECT amount
        FROM recipes
        WHERE NEW.name IS name AND ingredient IS ingredients.ingredient
    )
    WHERE ingredient IN (
        SELECT ingredient
        FROM recipes
        WHERE NEW.name = name
    );
END;


