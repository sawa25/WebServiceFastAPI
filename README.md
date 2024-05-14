# WebServiceFastAPI
учебный проект fastapi,django

## первая законченная чать в папке Lesson15, работает только в ubuntu. 
при попытке запустить в windows не удалось решить проблему SSL сертификатов:

test.ipynb -  нотбук с командами проверки сервиса

model.py - код ассистента чатжпт , отвечающего на вопросы по документу "ПРАВИЛА СТРАХОВАНИЯ ОТВЕТСТВЕННОСТИ АЭРОПОРТОВ И АВИАЦИОННЫХ ТОВАРОПРОИЗВОДИТЕЛЕЙ", при первой инициализации модель индексирует базу знаний. если индекс найден в текущей папке, то модель использует существующий при всех последующих изпользованиях.

main.py - код fastapi сервиса, запускается командой uvicorn main:app --port 5000

*.pem файлы - это цепочки сертификатов сайтов api.open.ai и openaipublic.blob.core.windows.net, попытка настроить их в windows - не заработало, для ubuntu они не понадобились.
## вторая законченная чать в папке Lesson16, 
содержит простейший шаблон проекта django, использует api сервис из урока Lesson15 для ответа на вопросы по вышеуказанному документу;
чат бот запускается в django в windows или ubuntu, но api сервис LLM работает только в ubuntu и бот, соответственно, отвечает только в ubuntu. 