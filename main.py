from fastapi import FastAPI, Request, Response, status




app = FastAPI()
app.counter: int = 0


@app.get("/")
def root():
    return {"message": "Hello world!"}

@app.api_route(path="/method", methods=["GET", "POST", "DELETE", "PUT", "OPTIONS"], status_code = 200)
def read_request(request: Request, response: Response):
    if request.method == "POST":
        response.status_code = status.HTTP_201_CREATED

    return {"method": request.method}

