from fastapi import FastAPI

app= FastAPI()

@app.get("/")
def home():
    return {"mensaje:" "Hola, mundo desde FastApi"}