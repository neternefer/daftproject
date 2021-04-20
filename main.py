from fastapi import FastAPI, Request, Response, status
from passlib.context import CryptContext
from typing import Dict
from pydantic import BaseModel
from datetime import date


class Patient(BaseModel):
    name: str
    surename: str
    register_date: date
    vaccination_date: date


app = FastAPI()
app.counter: int = 0
app.storage: Dict[int, Patient] = {}


@app.get("/")
def root():
    return {"message": "Hello world!"}

@app.api_route(path="/method", methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"], status_code = 200)
def read_request(request: Request, response: Response):
    if request.method == "POST":
        response.status_code = status.HTTP_201_CREATED

    return {"method": request.method}

@app.post("/register")
def new_patient(patient: Patient, request: Request, response: Response):
    length = len(patient.name) + len(patient.surename)
    reg_date = date
    vac_date = reg_date + length
    resp = {
    "id": app.counter,
    "name": patient.name,
    "surname": patient.surename,
    "register_date": reg_date,
    "vaccination_date": vac_date
}
    app.storage[app.counter] = patient
    app.counter += 1
    response.status_code = status.HTTP_201_CREATED
    return resp

@app.get("/patient/{id}")
def show_patient(id: int, response: Response):
    if id in app.storage:
        if id > 0:
            return app.storage.get(id)
        else:
            response.status_code = status.HTTP_400_BAD_REQUEST
    response.status_code = status.HTTP_404_NOT_FOUND


