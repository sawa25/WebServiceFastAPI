from fastapi import FastAPI
from pydantic import BaseModel
from model import LLMModel

# аннотации типов
# класс с типами данных параметров



class Item(BaseModel):
    name: str
    description: str
    price: float


# создаем объект приложения
app = FastAPI()

# функция, которая будет обрабатывать запрос по пути "/"
# полный путь запроса http://127.0.0.1:8000/


@app.get("/")
def root():
    return {"message": "Hello FastAPI"}

# функция, которая обрабатывает запрос по пути "/about"


@app.get("/about")
def about():
    return {"message": "Страница с описанием проекта"}

# функция-обработчик с параметрами пути



# # функция-обработчик post запроса с параметрами


@app.post("/users")
def get_model(item: Item):
    return {"name": item.name}


