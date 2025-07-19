from fastapi import FastAPI
from app.routes import router  # If this fails, comment it out for now

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}