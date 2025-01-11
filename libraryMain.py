import psycopg2
import base64

databasename = "library"
databaseuser = "postgres"
databasepassword = "123321"
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
    setConnectionSettings()
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
        CREATE TABLE IF NOT EXISTS Authors (
            author_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        );
        ''') 
        
        cur.execute('''
        CREATE TABLE IF NOT EXISTS Books (
            book_id SERIAL PRIMARY KEY,
            title VARCHAR(100) NOT NULL,
            year INT,
            author_id INT,
            genre_id INT,
            FOREIGN KEY (author_id) REFERENCES Authors(author_id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES Genres(genre_id) ON DELETE CASCADE
        );
        ''')

        cur.execute('''
        CREATE TABLE IF NOT EXISTS Reviews (
            review_id SERIAL PRIMARY KEY,
            book_id INT,
            rating INT CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT NOT NULL,
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
        SELECT b.title, b.year, a.name, g.name
        FROM Books b
        JOIN Authors a ON b.author_id=a.author_id
        JOIN Genres g ON b.genre_id=g.genre_id
    """)
    
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def addBook(title, author, year, genre):
    """Adds a book to the database. All parametrs are str; year - int.
    If there are no existing records of given genre or author, they are created."""
    conn = connect()
    cur = conn.cursor()

    if getRecords("Authors", ["name"], [author]) == []:
        cur.execute("INSERT INTO Authors (name) VALUES (%s)", (author,))
        conn.commit()
    author_id = getRecords("Authors", ["name"], [author])[0][0]

    if getRecords("Genres", ["name"], [genre]) == []:
        cur.execute("INSERT INTO Genres (name) VALUES (%s)", (genre,))
        conn.commit()
    genre_id = getRecords("Genres", ["name"], [genre])[0][0]        
        
    cur.execute("INSERT INTO Books (title, year, author_id, genre_id) VALUES (%s, %s, %s, %s)", (title, year, author_id, genre_id))
    conn.commit()
    cur.close()
    conn.close()

def removeByID(table, record_id):
    """Removes a record from a table by a given ID.
        table - string = name of the table (either Genres, Authors, Books or Reviews)
        record_id - int"""
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM " + table + " WHERE " + table.lower()[0:len(table)-1] + "_id = %s", (record_id,))
    conn.commit()
    cur.close()
    conn.close()

def addReview(book, rating, text):
    """Adds review to the book
    args:
    book - str = title
    rating - int = 1 to 5
    text - str"""
    if rating not in list(range(1, 6)):
        print("Error - rating is invalid")
        return
    
    conn = connect()
    cur = conn.cursor()
    reviewInBase64 = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    book_id = getRecords("Books", ["title"], [book])[0][0]
    cur.execute("INSERT INTO Reviews (book_id, rating, review_text) VALUES (%s, %s, %s)", (book_id, rating, reviewInBase64))
    conn.commit()
    cur.close()
    conn.close()

def getReviewText(review_id):
    reviewText = getRecords("Reviews", ["review_id"], [review_id])[0][3]
    return base64.b64decode(reviewText.encode('utf-8')).decode('utf-8')

def getBookRating(book_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT rating FROM Reviews WHERE book_id = %s", (book_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    
    total = 0
    for i in result:
        total += i[0]
    
    return total / len(result)

def getSortedBooksByGenre(genre, descendingOrder = True):
    """genre - str
    descendingOrder - if True, from best to worst; if False - vice versa"""
    conn = connect()
    cur = conn.cursor()
    genre_id = getRecords("Genres", ["name"], [genre])[0][0]
    cur.execute("""
        SELECT b.title, AVG(b.year) as year, MAX(a.name) as name, AVG(r.rating) as rating
        FROM Books b
        JOIN Authors a ON b.author_id=a.author_id
        LEFT JOIN Reviews r ON b.book_id=r.book_id
        WHERE b.genre_id=%s
        GROUP BY b.title
        ORDER BY rating 
    """ + ("DESC" if descendingOrder else "ASC"), (genre_id,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result

def main():
    onLaunch()

if __name__ == "__main__":
    main()
