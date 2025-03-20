from typing import Optional

from fastapi import FastAPI
from enum import Enum

app = FastAPI()

BOOKS = {
    "book_1": {
        "title": "title one",
        "author": "author one"
    },
    "book_2": {
        "title": "title two",
        "author": "author two"
    },
    "book_3": {
        "title": "title three",
        "author": "author three"
    },
    'book_4': {
        "title": "title four",
        "author": "author four"
    },
    'book_5': {
        "title": "title five",
        "author": "author five"
    }
}


@app.get("/")
async def read_all_books(skip_book: Optional[str] = None):
    if skip_book is None:
        return BOOKS
    new_books = BOOKS.copy()
    del new_books[skip_book]
    return new_books


@app.get("/book/{book_name}")
async def read_book(book_name: str):
    return BOOKS[book_name]


@app.post("/")
async def create_book(book_title: str, book_author: str):
    current_book_id = 0
    if len(BOOKS) > 0:
        for book in BOOKS:
            x = int(book.split('_')[-1])
            if x > current_book_id:
                current_book_id = x

    BOOKS[f'book_{current_book_id + 1}'] = {
        "title": book_title,
        "author": book_author
    }
    return BOOKS[f'book_{current_book_id + 1}']


@app.put("/{book_name}")
async def update_book(book_name: str, book_title: str, book_author: str):
    book_info = {
        "title": book_title,
        "author": book_author
    }
    BOOKS[book_name] = book_info
    return book_info


@app.delete("/{book_name}")
async def delete_book(book_name: str):
    del BOOKS[book_name]
    return f"Book {book_name} deleted"


@app.get('/assignment/')
async def read_book_assignment(book_name: str):
    return BOOKS[book_name]


@app.delete('/assignment/')
async def delete_book_assignment(book_name: str):
    del BOOKS[book_name]
    return {"message": f"Book {book_name} deleted", "books": BOOKS}

# class Direction(str, Enum):
#     north = "North"
#     south = "South"
#     east = "East"
#     west = "West"

# @app.get('/direction/{direction_name}')
# async def get_direction(direction_name: Direction):
#     if direction_name == Direction.north:
#         return {"direction": direction_name,'sub':'Up'}
#     elif direction_name == Direction.south:
#         return {"direction": direction_name,'sub':'Down'}
#     elif direction_name == Direction.east:
#         return {"direction": direction_name,'sub':'Right'}
#     return {"direction": direction_name,'sub':'Left'}
