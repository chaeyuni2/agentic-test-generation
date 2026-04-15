from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class LoginRequest(BaseModel):
    userId: str
    password: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/login")
def login(req: LoginRequest):
    if req.userId == "locked":
        return {"result": "LOCKED_USER"}

    if req.userId != "admin":
        return {"result": "USER_NOT_FOUND"}

    if req.password != "1234":
        return {"result": "INVALID_PASSWORD"}

    return {"result": "SUCCESS"}