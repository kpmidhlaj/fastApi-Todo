from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, status, Request, Form, Header
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse


class NegativeNumberException(Exception):
    def __init__(self, books_to_return):
        self.books_to_return = books_to_return


app = FastAPI()


class Book(BaseModel):
    id: UUID
    title: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=100, title="Description of the book")
    rating: int = Field(gt=-1, lt=101)

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426655440000",
                "title": "title one",
                "author": "author one",
                "description": "description one",
                "rating": 50
            }
        }


class BookNoRating(BaseModel):
    id: UUID
    title: str = Field(min_length=1)
    author: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=100, title="Description of the book")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426655440000",
                "title": "title one",
                "author": "author one",
                "description": "description one",
            }
        }


BOOKS = []


@app.exception_handler(NegativeNumberException)
async def negative_number_exception_handler(request: Request, exc: NegativeNumberException):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": f"Books to return cannot be negative, you requested {exc.books_to_return}"})


@app.post('/books/login')
async def login(book_id: int, username: Optional[str] = Header(default=None),
                password: Optional[str] = Header(default=None)):
    if username == 'kpmidhlaj' and password == '296695':
        return BOOKS[book_id]
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")


@app.get('/headers')
async def read_headers(random_header: Optional[str] = Header(default=None)):
    return {"Random Header": random_header}


@app.get("/")
async def read_all_books(books_to_return: Optional[int] = None):
    if books_to_return and books_to_return < 0:
        raise NegativeNumberException(books_to_return=books_to_return)
    if len(BOOKS) < 1:
        create_book_no_api()
    if books_to_return and len(BOOKS) >= books_to_return > 0:
        i = 1
        new_books = []
        while i <= books_to_return:
            new_books.append(BOOKS[i - 1])
            i += 1
        return new_books
    return BOOKS


@app.get("/book/{book_id}")
async def read_book(book_id: UUID):
    for book in BOOKS:
        if book.id == book_id:
            return book

    raise raise_item_not_found_exception()


@app.get("/book/rating/{book_id}", response_model=BookNoRating)
async def read_book_no_rating(book_id: UUID):
    for book in BOOKS:
        if book.id == book_id:
            return book

    raise raise_item_not_found_exception()


@app.put("/{book_id}")
async def update_book(book_id: UUID, book: Book):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            BOOKS[i] = book
            return BOOKS[i]

    raise raise_item_not_found_exception()


@app.delete("/{book_id}")
async def delete_book(book_id: UUID):
    for i in range(len(BOOKS)):
        if BOOKS[i].id == book_id:
            del BOOKS[i]
            return {"message": "Book with id: " + str(book_id) + " deleted successfully"}

    raise raise_item_not_found_exception()


@app.post("/", status_code=status.HTTP_201_CREATED)
async def create_book(book: Book):
    BOOKS.append(book)
    return book


def create_book_no_api():
    book_1 = Book(
        id=UUID("123e4567-e89b-12d3-a456-426655440000"),
        title="title one",
        author="author one",
        description="description one",
        rating=50)

    book_2 = Book(
        id=UUID("123e4567-e89b-12d3-a456-426655440001"),
        title="title two",
        author="author two",
        description="description two",
        rating=50)

    book_3 = Book(
        id=UUID("123e4567-e89b-12d3-a456-426655440002"),
        title="title three",
        author="author three",
        description="description three",
        rating=50)

    book_4 = Book(
        id=UUID("123e4567-e89b-12d3-a456-426655440003"),
        title="title four",
        author="author four",
        description="description four",
        rating=50)

    BOOKS.extend([book_1, book_2, book_3, book_4])

    return


def raise_item_not_found_exception():
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found",
                        headers={"X-Header": "Nothing to be seen at the UUID"})
