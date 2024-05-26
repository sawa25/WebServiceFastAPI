from fastapi.middleware.cors import CORSMiddleware
# from model import getfilefromgoogledisk пока не доработано
import logging #поиски сбоев ssl под windows (проблема не решена)
logging.basicConfig(filename="err1.txt",level=logging.DEBUG)

from fastapi.responses import HTMLResponse
from model import LLMModel
from pydantic import BaseModel
from fastapi import FastAPI
import functools
# декоратор для подсчета вызовов каждой функции
class CountCalls:
    calls = {} # Глобальный словарь для отслеживания количества вызовов
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
    def __call__(self, *args, **kwargs):
        func_name = self.func.__name__
        if func_name not in CountCalls.calls:
            CountCalls.calls[func_name] = 0
        CountCalls.calls[func_name] += 1
        return self.func(*args, **kwargs)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# получение количества вызовов каждой функции
@app.get("/calls")
def get_calls():
    test = '</br>'.join([f"{func}={cnt}" for func, cnt in CountCalls.calls.items()])
    return {"message": test}
@app.get("/api/num_requests")
def get_sumcalls():
    sum=0
    for func, cnt in CountCalls.calls.items():
        sum+=cnt
    return {"num_requests": sum}

@app.get("/")
@CountCalls
def read_root():
    return {"message": f"!answer!"}

class Item0(BaseModel):
    name: str
    description: str
    price: float

# тестовые вызовы
# функция-обработчик с параметрами пути
@app.get("/users/{id}")
@CountCalls
def user_id(id):
    return {"user_id": id}

# функция-обработчик post запроса с параметрами
@app.post("/users")
@CountCalls
def post_nameprice(item:Item0):
    return {"user_name": item.name, "description": item.description, "price": item.price}

@app.get("/html", response_class=HTMLResponse)
@CountCalls
def get_html():
    with open("my_page.html", 'r', encoding='utf-8') as f:
        html_content = f.read()
    return html_content


# работа консультанта
model = None #модель не инициализирована до первого обращения
# класс с типами данных параметров
class Item(BaseModel):
    text: str
# функция обработки get запроса + декоратор
@app.get("/api/start")
@CountCalls
def start_model():
    global model
    if model is None:
        # инициализация индексной базы
        model = LLMModel("")
        return {"message":"model started and ready to answer"}
    else:
        return {"message":"model already loaded and ready to answer"}
# функция обработки post запроса + декоратор
@app.post("/api/get_answer")
@CountCalls
def post_answer(question: Item):
    global model
    if model is None:
        return {"message":"model is not active. start by /api/start"}
    answer = model.get_answer(query=question.text)
    return {"message": answer}

# асинхронная функция обработки post запроса + декоратор 
@app.post("/api/get_answer_async")
async def get_answer_async(question: Item):
    answer = await model.async_get_answer(query=question.text)
    return {"message": answer}


@app.get("/api/get_answer")
@CountCalls
def get_answer():
    return {"message":"should be post method"}

