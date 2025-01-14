from flask import Flask, render_template, request, flash, redirect, url_for
from backend import *
 
app = Flask(__name__, template_folder='frontend', static_url_path='/')
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

 
valid_genres=[
    "Fantasy",
    "Fiction",
    "Action",
    "Detective",
    "Educational",
    "Drama",
    "Horror",
    "Romance",
    "Satire",
    "Biography"
]
 
unpack_apply = lambda f, arg_tuple: f(*arg_tuple)

@app.route("/")
def root():
    return render_template("index.html", genres=valid_genres)

@app.route("/index")
def index():
    return render_template("index.html", genres=valid_genres)

@app.post('/add_book')
def add_book():
    title = request.form.get('title', '')
    genre = request.form.get('genre', '')
    year = request.form.get('year', '')
    try:
        year = int(year)
        if not (year < 2050 and year > 0):
            raise Exception("")
    except:
        flash("Invalid year", 'error')
        return redirect(url_for("index"))

    description = request.form.get('description', None)

    if genre not in valid_genres:
        flash("Invalid genre", 'error')
        return redirect(url_for("index"))
    if title == '':
        flash("Title is required", 'error')
        return redirect(url_for("index"))
    addBook(title, year, genre, description)

    return redirect(url_for("index"))

@app.route('/search', methods=['GET'])
def search_books():
    title = request.args.get('title', '').lower()
    genre = request.args.get('genre', '')
    if genre == 'any':
        genre = ''
    if genre == '':
        if title == '':
            """
            flash("A title or a genre is required", 'error')
            return redirect(url_for("index"))
            """
            filtered_books = getSortedBooksByName(title)
        else:
            filtered_books = getSortedBooksByName(title)
    else:
        if title == '':
            filtered_books = getSortedBooksByGenre(genre)
        else:
            filtered_books = getSortedBooksByGenreWithName(genre, title)


    # print(filtered_books)
    make_dict = lambda i, t, g, y, d, r: {"title": t,
                                          "description": "No description provided" if d is None else d,
                                          "genre": g,
                                          "rating": "No reviews yet" if r is None else "{:3.1f}/5".format(float(r)) ,
                                          "year": int(y),
                                          "id": int(i)}
    f = lambda tup: unpack_apply(make_dict, tup)

    return render_template('results.html', books=list(map(f,filtered_books)))

@app.post('/delete/<int:book_id>')
def delete_book(book_id):
    removeByID("Books", book_id)

    redirect_url = request.form.get('redirect') or url_for('index')
    return redirect(redirect_url)

@app.post('/review/<int:book_id>')
def add_review(book_id):
    text = request.form.get('review-text', None)
    text_max_len = 200
    if text is not None:
        if len(text) > text_max_len:
            text = text[:text_max_len]
    score = request.form.get('review-score', None)
    redirect_url = request.form.get('redirect') or url_for('index')
    try:
        score = int(score)
        if not (score < 6 and score > 0):
            raise Exception("")
    except:
        flash("Invalid score", 'error')
        return redirect(redirect_url)
    addReview(book_id, score, text)
    return redirect(redirect_url)

@app.get("/book/<int:book_id>")
def get_book(book_id):

    book_dict = lambda i, t, d, y, gi: {
        "id": book_id,
        "title": t,
        "year": y,
        "description": d,
        "genre": getRecords("Genres", ["genre_id",], [gi,])[0][1],
        "rating": (lambda x: ("{:3.1f}".format( float(x))) if x else 'No reviews yet')(getBookRating(book_id)),
    }
    review_dict = lambda rid, bid, rat, txt: {
        "score": rat,
        "text": txt if txt else "No text"
    }
    print(getRecords("Books", ["book_id"], [book_id,])[0])
    book = getRecords("Books", ["book_id"], [book_id,])
    if (len(book) != 1):
        flash("Invalid book id", 'error')
        return redirect(url_for("index"))
    book = unpack_apply(book_dict, book[0])
    reviews = map(lambda x: unpack_apply(review_dict, x), getRecords("Reviews", ["book_id"], [book_id,]))
    print(book, reviews)
    return render_template("book.html", reviews=reviews, book=book)


if __name__ == "__main__":
    app.run(port=8080, debug=True)

