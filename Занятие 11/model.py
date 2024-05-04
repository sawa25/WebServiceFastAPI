from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import httplib2
import google_auth_httplib2
import io
import os
# import logging
# logging.basicConfig(filename="err.txt",level=logging.DEBUG)
import openai
from dotenv import load_dotenv
os.environ.clear()
load_dotenv(".env")

# API-key
openai.api_key = os.environ.get("OPENAI_API_KEY")
# print(os.environ.get("OPENAI_API_KEY"))

# задаем system
default_system = "Ты-консультант в компании Simble, ответь на вопрос клиента на основе документа с информацией. Не придумывай ничего от себя, отвечай максимально по документу. Не упоминай Документ с информацией для ответа клиенту. Клиент ничего не должен знать про Документ с информацией для ответа клиенту"


# Укажите путь к директории
folder_path = ''

# Проверяем существование файлов
def check_files_exist(folder_path, file_names):
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            pass
        else:
            print(f"Файл '{file_name}' не найден в директории '{folder_path}'.")
            return False
    return True
# Список файлов для проверки
files_to_check = ['dbfaiss_from_langchain.faiss', 'dbfaiss_from_langchain.pkl']



class LLMModel():
    def __init__(self, folder_path: str, sep: str = " ", ch_size: int = 1024):

        # Вызов функции проверки
        if check_files_exist(folder_path, files_to_check):
            # возможность загрузки предварительно сохраненной индексной базы с диска
            embeddings = OpenAIEmbeddings()
            # Имя, используемое при сохранении файлов
            index_name = "dbfaiss_from_langchain"
            # Загрузка данных и создание нового экземпляра FAISS
            self.db = FAISS.load_local(
                folder_path=folder_path,
                embeddings=embeddings,
                index_name=index_name
            )

        else: # база не проиндексирована - сделать это с нуля
            # прочитать с гуглдрайва из под uvicorn не получилось из-за ssl ошибок.
            # простой запуск без uvicorn - сработывал нормально
            # document=getfilefromgoogledisk(uniquesubstringfromfilename='АЭРОПОРТОВ И АВИАЦИОННЫХ ТОВАРОПРОИЗВОДИТЕЛЕЙ')

            # чтение локальной копии файла базы знаний
            with open("Копия ПРАВИЛА СТРАХОВАНИЯ ОТВЕТСТВЕННОСТИ АЭРОПОРТОВ И АВИАЦИОННЫХ ТОВАРОПРОИЗВОДИТЕЛЕЙ.txt", "r", encoding="utf-8") as f:
                document = f.read()

            # создаем список чанков
            source_chunks = []
            splitter = CharacterTextSplitter(separator=sep, chunk_size=ch_size)
            for chunk in splitter.split_text(document):
                source_chunks.append(Document(page_content=chunk, metadata={}))

            # создаем индексную базу
            embeddings = OpenAIEmbeddings()
            self.db = FAISS.from_documents(source_chunks, embeddings)

            # сохраняем db_from_texts на ваш гугл драйв
            self.db.save_local(folder_path=folder_path, index_name=index_name)        

    def get_answer(self, system: str = default_system, query: str = None):
        '''Функция получения ответа от chatgpt
        '''
        # релевантные отрезки из базы
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ответь на вопрос клиента. Не упоминай документ с информацией для \
                                          ответа клиенту в ответе. Документ с информацией для ответа клиенту:\
                                          {message_content}\n\nВопрос клиента: \n{query}"}
        ]

        # получение ответа от chatgpt
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                  messages=messages,
                                                  temperature=0)

        return completion.choices[0].message.content
