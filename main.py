import secrets, sqlite3
from datetime import date, datetime, timedelta
from fastapi import Cookie, Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from hashlib import sha256, sha512
from pydantic import BaseModel
from typing import Dict, List, Optional

class Patient(BaseModel):
    id: Optional[int] = 1
    name: str
    surname: str
    register_date: Optional[date]
    vaccination_date: Optional[date]

class Message:
    def __init__(self, format: Optional[str] = Query("")):
        self.format = format
        self.word = ""

    def return_message(self):
        '''Return message in correct format (json/html/plain)'''
        if self.format == "json":
            message = {"message": f"{self.word}!"}
        elif self.format == "html":
            message = HTMLResponse(f"<h1>{self.word}!</h1>", status_code=200)
        else:
            message = PlainTextResponse(f"{self.word}!", status_code=200)
        return message

app = FastAPI()
app.counter: int = 1
app.mount("/static", StaticFiles(directory="static"), name="static")
app.session_cookie_tokens = []
app.session_tokens = []
app.storage: Dict[int, Patient] = {}
templates = Jinja2Templates(directory="templates")
security = HTTPBasic()

#1.1
@app.get("/")
def root():
    return {"message": "Hello world!"}

#1.2
@app.api_route(path = "/method", methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"], status_code = 200)
def read_request(request: Request, response: Response):
    if request.method == "POST":
        response.status_code = status.HTTP_201_CREATED
    return {"method": request.method}

#1.3
@app.get("/auth")
def check_pass(response: Response, password: str = Query(""), password_hash: str = Query("")):
    if password and password_hash:
        hashed = sha512(password.encode("utf-8")).hexdigest()
        if password_hash == hashed:
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

#1.4
@app.post("/register")
async def new_patient(patient: Patient, response: Response):
    name_letters = "".join([item for item in patient.name if item.isalpha()])
    surname_letters = "".join([item for item in patient.surname if item.isalpha()])
    length = len(name_letters) + len(surname_letters)
    patient.vaccination_date = patient.register_date + timedelta(days=length)
    patient.id = app.counter
    app.storage[app.counter] = patient
    app.counter += 1
    response.status_code = status.HTTP_201_CREATED
    return patient

#1.5
@app.get("/patient/{id}")
def show_patient(id: int, response: Response):
    if id in app.storage:
        if id < 1:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
        return app.storage.get(id)
    raise HTTPException(status_code = status.HTTP_404_NOT_FOUND)

#3.1
@app.get("/hello", response_class=HTMLResponse)
def get_hello(request: Request):
    current_date = datetime.now()
    str_date = current_date.strftime("%Y-%m-%d")
    return templates.TemplateResponse("index.html.j2", {
        "request": request, "message": f"Hello! Today date is {str_date}"})

#3.2
def check_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    '''Helper function for username/password check'''
    valid_username = secrets.compare_digest(credentials.username, "4dm1n")
    valid_password = secrets.compare_digest(credentials.password, "NotSoSecurePa$$")
    if not (valid_password and valid_username):
        status_code = 401
    else:
        status_code = 200
    return {"status_code": status_code,
            "valid_username": valid_username,
            "valid_password": valid_password}

@app.post("/login_session", status_code=201)
def login_session(response: Response, authorized: dict = Depends(check_credentials)):
    if authorized["status_code"] == 200:
        secret_key = secrets.token_hex(16)
        session_token = sha256(f'{authorized["valid_username"]}{authorized["valid_password"]}{secret_key}'.encode()).hexdigest()
        if len(app.session_cookie_tokens) >= 3:
            del app.session_cookie_tokens[0]
        app.session_cookie_tokens.append(session_token)
        response.set_cookie(key="session_token", value=session_token)
    elif authorized["status_code"] == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"})
    return {"message": "Session established"}

@app.post("/login_token", status_code=201)
def login_token(authorized: dict = Depends(check_credentials)):
    if authorized["status_code"] == 200:
        secret_key = secrets.token_hex(16)
        token_value = sha256(f'{authorized["valid_username"]}{authorized["valid_password"]}{secret_key}'.encode()).hexdigest()
        if len(app.session_tokens) >= 3:
            del app.session_tokens[0]
        app.session_tokens.append(token_value)
    elif authorized["status_code"] == 401:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"})
    return {"token": token_value}

#3.3
@app.get("/welcome_session")
def welcome_session(session_token: str = Cookie(None), is_format: Message = Depends(Message)):
    if not session_token or session_token not in app.session_cookie_tokens:
        raise HTTPException(status_code=401, detail="Unathorised")
    else:
        is_format.word = "Welcome"
        return is_format.return_message()

@app.get("/welcome_token")
def welcome_token(token: Optional[str] = Query(None), is_format: Message = Depends(Message)):
    if not token or token not in app.session_tokens:
        raise HTTPException(status_code=401, detail="Unathorised")
    else:
        is_format.word = "Welcome"
        return is_format.return_message()

#3.4
@app.delete("/logout_session")
def logout_session(session_token: str = Cookie(None), format: str = Query("")):
    if not session_token or session_token not in app.session_cookie_tokens:
        raise HTTPException(status_code=401, detail="Unathorised")
    else:
        app.session_cookie_tokens.remove(session_token)
        url = f"/logged_out?format={format}"
        return RedirectResponse(url=url, status_code=303)

@app.delete("/logout_token")
def logout_token(token: Optional[str] = Query(None), format: str = Query("")):
    if not token or token not in app.session_tokens:
        raise HTTPException(status_code=401, detail="Unathorised")
    else:
        app.session_tokens.remove(token)
        url = f"/logged_out?format={format}"
        return RedirectResponse(url=url, status_code=303)

@app.get("/logged_out")
def logged_out(is_format: Message = Depends(Message)):
    is_format.word = "Logged out"
    return is_format.return_message()

@app.on_event("startup")
async def startup():
    app.db_connection = sqlite3.connect("northwind.db")
    app.db_connection.text_factory = lambda b: b.decode("cp1252", errors="ignore")#northwind specific


@app.on_event("shutdown")
async def shutdown():
    app.db_connection.close()

#4.1
def cursor():
    app.db_connection.row_factory = sqlite3.Row
    cursor = app.db_connection.cursor()
    return cursor

def status(query_result: List[dict]):
    if not query_result:
        raise HTTPException(status_code=404, detail="Item not found")
    return query_result

@app.get("/categories", status_code=200)
async def get_categories():
    categories = cursor().execute("SELECT  CategoryID id, CategoryName name FROM Categories").fetchall()
    return {
        "categories":  categories
    }

@app.get("/customers", status_code=200)
async def get_customers():
    customers = cursor().execute("SELECT CustomerID id, CompanyName name, Address || ' ' || ifnull(PostalCode, '') || ' ' || City || ' ' || Country full_address FROM Customers").fetchall()
    return {
        "customers": customers
    }

#4.2
@app.get("/products/{id}", status_code=200)
async def get_product(id: int):
    data = cursor().execute("SELECT ProductID id, ProductName name FROM Products WHERE ProductID = ?", (id, )).fetchone()
    return status(data)

#4.3
@app.get("/employees", status_code=200)
async def get_employees(limit: int = Query(10), offset: int = Query(0),order: str = Query("id")):
    x = order if order in ["id", "last_name", "first_name", "city"] else ""
    if not x:
        raise HTTPException(status_code=400, detail="Incorrect query")
    data = cursor().execute(f'''SELECT EmployeeID id,
                                    LastName last_name,
                                    FirstName first_name,
                                    City city FROM Employees
                                    ORDER BY {x}
                                    LIMIT :limit
                                    OFFSET :offset''',
                                    {"limit": limit,
                                     "offset": offset}).fetchall()
    return data

#4.4
@app.get("/products_extended", status_code=200)
async def get_full_product():
    data = cursor().execute('''SELECT p.ProductID id, p.ProductName name,
	                                    c.CategoryName category, s.CompanyName supplier
                                        FROM Products p
                                        JOIN Categories c ON c.CategoryID = p.CategoryID
                                        LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
                                        ORDER BY id;''').fetchall()
    return data

#4.5
@app.get("/products/{id}/orders", status_code=200)
async def get_orders(id: int):
    data = cursor().execute('''SELECT o.OrderID id, c.CompanyName customer,
	                    od.Quantity quantity,
	                    ROUND(((od.UnitPrice * od.Quantity) - (od.Discount * (od.UnitPrice * od.Quantity))), 2) total_price
                        FROM Orders o
                        JOIN "Order Details" od ON o.OrderID = od.OrderID
                        JOIN Customers c ON c.CustomerID = o.CustomerID
                        WHERE od.ProductID = ?
                        ORDER BY id''', (id, )).fetchall()
    return status(data)

#4.6
class Category(BaseModel):
    name: str

@app.post("/categories", status_code=201)
async def add_category(category: Category):
    cursor = app.db_connection.execute('''INSERT INTO Categories (CategoryName)
                                        VALUES (?)
                                        ''', (category.name, )
    )
    app.db_connection.commit()
    app.db_connection.row_factory = sqlite3.Row
    new_category_id = cursor.lastrowid
    category = app.db_connection.execute('''SELECT CategoryID id,
                                        CategoryName name FROM Categories
                                        WHERE CategoryID = ?''',
                                        (new_category_id, )).fetchone()
    return category

@app.put("/categories/{id}", status_code=200)
async def update_category(id: int, category: Category):
    cursor = app.db_connection.execute('''UPDATE Categories
                                        SET CategoryName = ?
                                        WHERE CategoryID = ?
                                        ''', (category.name, id))
    app.db_connection.commit()
    app.db_connection.row_factory = sqlite3.Row
    data = app.db_connection.execute('''SELECT CategoryID id, CategoryName name
                                    FROM Categories WHERE CategoryID = ?''',
                                    (id, )).fetchone()
    return status(data)

@app.delete("/categories/{id}", status_code=200)
async def delete_category(id: int):
    cursor = app.db_connection.execute(
        "DELETE FROM Categories WHERE CategoryID = ?", (id, ))
    app.db_connection.commit()
    if not cursor.rowcount:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"deleted": cursor.rowcount}