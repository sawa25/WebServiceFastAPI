from dotenv import load_dotenv
import os
os.environ.clear()
load_dotenv(".env")
# для ubuntu эти переменные не нужны, а для windows не помогло
# print(os.environ.get("SSL_CERT_FILE"))
# print(os.environ.get('REQUESTS_CA_BUNDLE'))

from langchain_openai import OpenAIEmbeddings
# print(dir(OpenAIEmbeddings))
# print(OpenAIEmbeddings.__doc__)

# from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document

import openai
from openai import OpenAI
from openai import AsyncOpenAI

openai.api_key = os.environ.get("OPENAI_API_KEY")
openai.verify_ssl_certs = False
# print(os.environ.get("OPENAI_API_KEY"))

# Укажите путь к директории
folder_path = ''
# задаем system
default_system = '''Ты-консультант по ПРАВИЛАМ СТРАХОВАНИЯ.
Ответь на вопрос клиента на основе переданного тебе документа с соответствующими правилами. 
Не придумывай ничего от себя, отвечай максимально по документу. 
Если в запросе клиента тебе передана история предшествующего диалога (в формате Вопрос1:...\nОтвет1:...,Последний вопрос:...), используй эту информацию для более точного ответа.
'''

# Проверяем существование файлов
def check_files_exist(folder_path, file_names):
    for file_name in file_names:
        file_path = os.path.join(folder_path, file_name)
        if os.path.exists(file_path):
            pass
        else:
            print(f"Файл '{file_name}' не найден в директории, значит выполнить индексацию '{folder_path}'.")
            return False
    return True



class LLMModel():
    def __init__(self, folder_path: str, sep: str = " ", ch_size: int = 1024):
        # self.client = OpenAI() для синхронной версии
        self.client = AsyncOpenAI(
            # This is the default and can be omitted
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        embeddings = OpenAIEmbeddings()

        index_name = "dbaerofaiss_from_langchain"
        # Список файлов для проверки
        files_to_check = [f'{index_name}.faiss', f'{index_name}.pkl']
        # Вызов функции проверки
        if check_files_exist(folder_path, files_to_check):
            # возможность загрузки предварительно сохраненной индексной базы с диска
            # Имя, используемое при сохранении файлов
            # Загрузка данных и создание нового экземпляра FAISS
            self.db = FAISS.load_local(
                folder_path=folder_path,
                embeddings=embeddings,
                index_name=index_name,
                allow_dangerous_deserialization=True # Разрешить десериализацию проиндексированной ранее базы знаний
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
            self.db = FAISS.from_documents(source_chunks, embeddings)
            # сохраняем db_from_texts на ваш гугл драйв
            self.db.save_local(folder_path=folder_path, index_name=index_name)        


    def get_answer(self,query: str = None, system: str = default_system):
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
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125", #gpt-3.5-turbo-1106
            # response_format={ "type": "json_object" },
            messages=messages,
            temperature=0
        )

        return completion.choices[0].message.content

    async def async_get_answer(self,query: str = None, system: str = default_system):
        '''Асинхронная функция получения ответа от chatgpt
        '''
        # релевантные отрезки из базы
        docs = self.db.similarity_search(query, k=4)
        message_content = '\n'.join([f'{doc.page_content}' for doc in docs])
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": f"Ответь на вопрос клиента. Не упоминай документ с информацией для \
                                          ответа клиенту в ответе. Документ с информацией для ответа клиенту:\
                                          {message_content}\n\nПредшествующий диалог и очередной вопрос клиента: \n{query}"}
        ]

        # получение ответа от chatgpt
        completion = await self.client.chat.completions.create(
            model="gpt-3.5-turbo-0125", #gpt-3.5-turbo-1106
            # response_format={ "type": "json_object" },
            messages=messages,
            temperature=0
        )

        return completion.choices[0].message.content


# model = LLMModel("")