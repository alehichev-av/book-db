import psycopg2
import base64

databasename = "library"
databaseuser = "postgres"
databasepassword = ""
databasehost = "127.0.0.1"

def setConnectionSettings():
    global databasename
    global databaseuser
    global databasepassword
    global databasehost
    
    databasename = input("Enter database name: ")
    databaseuser = input("Enter database user: ")
    databasepassword = input("Enter user password: ")
    host = input("Enter database host (127.0.0.1 by default): ")
    
    if host != "":
        databasehost = host

def connect():
    conn = psycopg2.connect(
        dbname = databasename,
        user = databaseuser,
        password = databasepassword,
        host = databasehost
    )
    return conn


def onLaunch():
    # setConnectionSettings()
    try: 
        conn = connect()
        print("Connected to the database successfully")
    except:
        print("Database not found...")
        connCreate = psycopg2.connect(dbname="postgres", user=databaseuser, password=databasepassword, host=databasehost)
        cursor = connCreate.cursor()
        connCreate.autocommit = True
        cursor.execute("CREATE DATABASE " + databasename)
        print("New database was created successfully")
        cursor.close()
        connCreate.close()

        conn = connect()
    finally:
        cur = conn.cursor()

        cur.execute('''
        CREATE TABLE IF NOT EXISTS Genres (
            genre_id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL
        );
        ''')

        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Books (
            book_id SERIAL PRIMARY KEY,
            title VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            year INT,
            genre_id INT,
            FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id SERIAL PRIMARY KEY,
            book_id INT NOT NULL,
            rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            FOREIGN KEY (book_id) REFERENCES Books(book_id) ON DELETE CASCADE
        );
        ''') 

    conn.commit()    

    cur.close()
    conn.close()

def getRecords(table, fields=[], values=[]):
    """
    Returns a list - result of a query.
    table - str = name of the table to look for the data in
    fields - list = list of fields that take part in the conditional query
    values - list = list of values that take part in the conditional query

    Example:
    getRecord("Books", ["title", "year"], ["AAA", 2001]) <=>
        SELECT * FROM Books WHERE title = 'AAA' AND year = 2001;
    """

    if len(fields) != len(values):
        print("Invalid input - lists are not of the same length")
        return []
    
    conn = connect()
    cur = conn.cursor()
    query = "SELECT * FROM " + table
    
    for i in range(0, len(fields)):
        if (i == 0):
            query += " WHERE "
        else:
            query += " AND "
        query += fields[i] + " = " + ("'" + str(values[i]) + "'" if isinstance(values[i], str) else str(values[i]))
        
    cur.execute(query)
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def getLibrary():
    """Returns the list of books"""
    conn = connect()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT b.title, b.year, g.name, desc
        FROM Books b
        JOIN Genres g ON b.genre_id=g.genre_id
    """)
    
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def addBook(title, year, genre, description):
    """Adds a book to the database. All parametrs are str; year - int.
    If there are no existing records of given genre, they are created."""
    print(description)
    conn = connect()
    cur = conn.cursor()
    if getRecords("Genres", ["name"], [genre]) == []:
        cur.execute("INSERT INTO Genres (name) VALUES (%s)", (genre,))
        conn.commit()
    genre_id = getRecords("Genres", ["name"], [genre])[0][0]        
        
    desc_max_len = 180
    if description is not None:
        if len(description) > desc_max_len:
            description = description[:desc_max_len]
    cur.execute("INSERT INTO Books (title, year, genre_id, description) VALUES (%s, %s, %s, %s)", (title, year, genre_id, description))
    conn.commit()
    cur.close()
    conn.close()

def removeByID(table, record_id):
    """Removes a record from a table by a given ID.
        table - string = name of the table (either Genres, Books or Reviews)
        record_id - int"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM " + table + " WHERE " + table.lower()[0:len(table)-1] + "_id = %s", (record_id,))
    conn.commit()
    cur.close()
    conn.close()

def addReview(book_id, rating, text):
    """Adds review to the book
    args:
    book_id - int = id of the book
    rating - int = 1 to 5
    text - str"""
    if rating not in list(range(1, 6)):
        print("Error - rating is invalid")
        return
    
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO Reviews (book_id, rating, review_text) VALUES (%s, %s, %s)", (book_id, rating, text))
    conn.commit()
    cur.close()
    conn.close()

def getReviewText(review_id):
    return getRecords("Reviews", ["review_id"], [review_id])[0][3]

def getBookRating(book_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT AVG(rating) FROM Reviews WHERE book_id = %s GROUP BY book_id", (book_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    
    total = 0
    for i in result:
        total += i[0]
    
    return total

def getSortedBooksByGenre(genre, descendingOrder = True):
    """genre - str
    descendingOrder - if True, from best to worst; if False - vice versa"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(b.book_id), b.title, MAX(g.name), AVG(b.year) as year, MAX(b.description), AVG(r.rating) as rating
        FROM Books b
        JOIN Genres g ON b.genre_id=g.genre_id
        LEFT JOIN Reviews r ON b.book_id=r.book_id
        WHERE g.name=%s
        GROUP BY b.title
        ORDER BY rating 
    """ + ("DESC" if descendingOrder else "ASC"), (genre,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def getSortedBooksByName(name, descendingOrder = True):
    """name - str
    descendingOrder - if True, from best to worst; if False - vice versa"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(b.book_id), b.title, MAX(g.name), AVG(b.year) as year, MAX(b.description), AVG(r.rating) as rating
        FROM Books b
        JOIN Genres g ON b.genre_id=g.genre_id
        LEFT JOIN Reviews r ON b.book_id=r.book_id
        WHERE b.title ILIKE %s
        GROUP BY b.title
        ORDER BY rating 
    """ + ("DESC" if descendingOrder else "ASC"), ('%' + name + '%',))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def getSortedBooksByGenreWithName(genre, name, descendingOrder = True):
    """genre - str
    descendingOrder - if True, from best to worst; if False - vice versa"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT MAX(b.book_id), b.title, MAX(g.name), AVG(b.year) as year, MAX(b.description), AVG(r.rating) as rating
        FROM Books b
        JOIN Genres g ON b.genre_id=g.genre_id
        LEFT JOIN Reviews r ON b.book_id=r.book_id
        WHERE (b.title ILIKE %s) AND (g.name=%s)
        GROUP BY b.title
        ORDER BY rating
    """ + ("DESC" if descendingOrder else "ASC"), ('%' + name + '%', genre,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def drop_database():
    """Drops database.
    Used when I need to change the scheme during development, since idk how to use postgresql shell"""
    conn = psycopg2.connect(dbname="postgres", user=databaseuser, password=databasepassword, host=databasehost)
    with conn.cursor() as cur:
        conn.autocommit = True
        cur.execute("drop database " + databasename)


def main():
    drop_database()
    onLaunch()

if __name__ == "__main__":
    main()
