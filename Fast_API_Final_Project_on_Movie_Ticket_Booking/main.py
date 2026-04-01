from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

# -----------------------------
# DATA
# -----------------------------
movies = [
    {"id": 1, "name": "RRR", "genre": "Action", "price": 200, "available_seats": 50},
    {"id": 2, "name": "KGF", "genre": "Action", "price": 180, "available_seats": 30},
    {"id": 3, "name": "Jawan", "genre": "Drama", "price": 150, "available_seats": 40},
    {"id": 4, "name": "Leo", "genre": "Thriller", "price": 220, "available_seats": 20},
    {"id": 5, "name": "Salaar", "genre": "Action", "price": 250, "available_seats": 25},
]

bookings = []
booking_counter = 1

# -----------------------------
# HELPERS
# -----------------------------
def find_movie(movie_id):
    for movie in movies:
        if movie["id"] == movie_id:
            return movie
    return None

def calculate_total(price, seats):
    return price * seats

# -----------------------------
# DAY 1 - GET APIs
# -----------------------------
@app.get("/")
def home():
    return {"message": "Welcome to Movie Booking API"}

@app.get("/movies")
def get_movies():
    return {"total": len(movies), "movies": movies}

@app.get("/movies/summary")
def summary():
    total = len(movies)
    total_seats = sum(m["available_seats"] for m in movies)
    return {"total_movies": total, "total_seats": total_seats}

@app.get("/bookings")
def get_bookings():
    return {"total": len(bookings), "bookings": bookings}

# -----------------------------
# DAY 6 APIs (IMPORTANT: place BEFORE /{movie_id})
# -----------------------------

# 🔍 SEARCH
@app.get("/movies/search")
def search_movies(keyword: str):
    result = [m for m in movies if keyword.lower() in m["name"].lower()]
    return {"results": result, "count": len(result)}

# 🔃 SORT
@app.get("/movies/sort")
def sort_movies(order: str = "asc"):
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order")

    return sorted(movies, key=lambda x: x["price"], reverse=(order == "desc"))

# 📄 PAGINATION
@app.get("/movies/page")
def paginate(page: int = 1, limit: int = 2):
    start = (page - 1) * limit
    return movies[start:start + limit]

# 🧠 COMBINED API
@app.get("/movies/browse")
def browse(
    keyword: Optional[str] = None,
    order: str = "asc",
    page: int = 1,
    limit: int = 2
):
    data = movies

    if keyword:
        data = [m for m in data if keyword.lower() in m["name"].lower()]

    data = sorted(data, key=lambda x: x["price"], reverse=(order == "desc"))

    start = (page - 1) * limit
    return data[start:start + limit]

# -----------------------------
# NOW VARIABLE ROUTE (VERY IMPORTANT)
# -----------------------------
@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

# -----------------------------
# DAY 2 - POST
# -----------------------------
class BookingRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    movie_id: int = Field(gt=0)
    seats: int = Field(gt=0, le=10)

@app.post("/book")
def book_ticket(request: BookingRequest):
    global booking_counter

    movie = find_movie(request.movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if movie["available_seats"] < request.seats:
        raise HTTPException(status_code=400, detail="Not enough seats")

    total = calculate_total(movie["price"], request.seats)

    booking = {
        "booking_id": booking_counter,
        "customer_name": request.customer_name,
        "movie": movie["name"],
        "seats": request.seats,
        "total_price": total,
        "status": "booked"
    }

    booking_counter += 1
    movie["available_seats"] -= request.seats
    bookings.append(booking)

    return booking

# -----------------------------
# DAY 4 - CRUD
# -----------------------------
class NewMovie(BaseModel):
    name: str
    genre: str
    price: int
    available_seats: int

@app.post("/movies")
def add_movie(movie: NewMovie, response: Response):
    new_id = len(movies) + 1
    new_movie = {"id": new_id, **movie.dict()}
    movies.append(new_movie)
    response.status_code = 201
    return new_movie

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, price: Optional[int] = None):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    if price is not None:
        movie["price"] = price

    return movie

@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    movies.remove(movie)
    return {"message": "Deleted successfully"}

# -----------------------------
# DAY 5 - WORKFLOW
# -----------------------------
@app.post("/checkin/{booking_id}")
def checkin(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "checked_in"
            return b
    raise HTTPException(status_code=404, detail="Booking not found")

@app.post("/checkout/{booking_id}")
def checkout(booking_id: int):
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "completed"
            return b
    raise HTTPException(status_code=404, detail="Booking not found")