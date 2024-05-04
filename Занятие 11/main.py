from fastapi import FastAPI
from model import LLMModel
# from model import getfilefromgoogledisk
from pydantic import BaseModel
import logging
logging.basicConfig(filename="err1.txt",level=logging.DEBUG)
model = None

# класс с типами данных параметров


class Item(BaseModel):
    text: str

# создаем объект приложения
app = FastAPI()

# функция обработки get запроса + декоратор

@app.get("/api/start")
def users():
    global model
    if model is None:
        # инициализация индексной базы
        model = LLMModel("")
        return {"message":"model started and ready to answer"}
    else:
        return {"message":"model already loaded and ready to answer"}


@app.get("/")
def read_root():
    return {"message": "!answer!"}

# @app.get("/test")
# def read_root():
#     return {"message": getfilefromgoogledisk("")[:500]}


# функция обработки post запроса + декоратор
@app.post("/api/get_answer")
def get_answer(question: Item):
    global model
    if model is None:
        return {"message":"model is not active. start by /api/start"}
    answer = model.get_answer(query=question.text)
    return {"message": answer}
