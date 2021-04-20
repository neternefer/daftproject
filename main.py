from fastapi import FastAPI, Request, Response, status
from passlib.hash import sha512_crypt
from typing import Dict
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Optional


class Patient(BaseModel):
    id: Optional[int] = 1
    name: str
    surname: str
    register_date: Optional[date]
    vaccination_date: Optional[date]


app = FastAPI()
app.counter: int = 1
app.storage: Dict[int, Patient] = {}


@app.get("/")
def root():
    return {"message": "Hello world!"}

@app.api_route(path="/method", methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"], status_code = 200)
def read_request(request: Request, response: Response):
    if request.method == "POST":
        response.status_code = status.HTTP_201_CREATED
    return {"method": request.method}

@app.get("/auth")
def check_pass(password, password_hash, response: Response):
    hashed = sha512_crypt.hash(password)
    if password_hash == hashed:
        response.status_code = status.HTTP_204_NO_CONTENT
    else:
        response.status_code = status.HTTP_401_UNAUTHORIZED



@app.post("/register")
async def new_patient(patient: Patient, response: Response):
    length = len(patient.name) + len(patient.surname)
    patient.vaccination_date = patient.register_date + timedelta(days=length)
    patient.id = app.counter
    app.storage[app.counter] = patient
    app.counter += 1
    response.status_code = status.HTTP_201_CREATED
    return patient

@app.get("/patient/{id}")
def show_patient(id: int, response: Response):
    if id in app.storage:
        if id < 1:
            response.status_code = status.HTTP_400_BAD_REQUEST
        return app.storage.get(id)
    response.status_code = status.HTTP_404_NOT_FOUND


