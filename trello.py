import sys
import requests

# Данные авторизации в API Trello  
auth_params = {
    'key': "35bddf9f000989e5f86b847bedeaf31f",
    'token': "749ce4e978b29662cf7125743a566d66b7445a5df224c12f980fa4217680aaaa",}
# Адрес, на котором расположен API Trello,
# Именно туда мы будем отправлять HTTP запросы.
base_url = "https://api.trello.com/1/{}"
# Идентификатор доски
board_id = "CSY3G2J1"

def read_task():
    # Получим данные всех колонок на доске:
    column_data = requests.get(base_url.format('boards') \
    	+ '/' + board_id + '/lists', params=auth_params).json()
    # Теперь выведем название каждой колонки и всех заданий, которые к ней относятся:
    for column in column_data:  
        # Получим данные всех задач в колонке и перечислим все названия
        task_data = requests.get(base_url.format('lists') \
        	+ '/' + column['id'] + '/cards', params=auth_params).json()
        print("{}".format(len(task_data)) + ' --> ' + column['name'])
        if not task_data:
            print('\t-> ' + 'Нет задач!')
            continue
        for task in task_data:
            print('\t-> ' + task['name'] + ' <-> id: ' + task['id'])

def get_duplicated_tasks(task_name):
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format('boards') \
    	+ '/' + board_id + '/lists', params=auth_params).json()
    # Создадим список для дублированных задач
    duplicated_tasks = []
    for column in column_data:
    	# Получим список всех задач
        column_tasks = requests.get(base_url.format('lists') \
        	+ '/' + column['id'] + '/cards', params=auth_params).json()
        for task in column_tasks:
            if task['name'] == task_name:
            	# Добавим дублированную задачу в список
                duplicated_tasks.append(task)
    # Возвращаем список дублированных задач
    return duplicated_tasks

def column_check(column_name):
    column_id = None
    # Получим данные всех колонок на доске
    column_data = requests.get(base_url.format('boards') \
		+ '/' + board_id + '/lists', params=auth_params).json()
	# Переберём данные обо всех колонках, пока не найдём ту колонку, которая нам нужна  
    for column in column_data:
        if column['name'] == column_name:
            column_id = column['id']
            break
	# Возвращаем id нашей колонки
    return column_id

def create_column(column_name, showstatus):
    request = requests.get(base_url.format('boards') + '/' + board_id, params=auth_params)
    if request.status_code != 200:
        print('--- Возникла ошибка {}.'.format(request.status_code))
        return None
    boardid = request.json()['id']
    request = requests.post(base_url.format('lists'), \
    	data={'name': column_name, 'idBoard': boardid, 'pos': 'bottom', **auth_params})
    if request.status_code == 200:
        print('--- Колонка "{}" создана! ---'.format(column_name))
        if showstatus == True:
        	read_task()
    else:
        print('--- Возникла ошибка {}. '.format(request.status_code) \
        	+ 'Колонка "{}" не создана! ---'.format(column_name))
    print(request.json()['id'])
    return request

def create_task(name, column_name):
    # Проверяем существует ли колонка
    column_id = column_check(column_name)
    # Если не существует,
    if column_id is None:
        # то создаем колонку на доске
        column_id = create_column(column_name, False).json()['id']
    # Создадим задачу с именем name в найденной или созданой колонке
    request = requests.post(base_url.format('cards'), \
    	data={'name': name, 'idList': column_id, **auth_params})
    if request.status_code == 200:
        print('--- Задача "{}" добавлена! ---'.format(name))
        read_task()
    else:
        print('--- Возникла ошибка {}. '.format(request.status_code) \
        	+ 'Задача "{}" не добавлена! ---'.format(name))

def move_task(name, column_name):
    # Проверим существуют ли дубликаты нашей задачи
    duplicated_tasks = get_duplicated_tasks(name)
    # Если задачи не существует,
    if not duplicated_tasks:
    	# то выводим сообщение
        print('--- Задача "{}" не найдена! ---'.format(name))
        return
    # Если найдены дубликаты задач,
    if len(duplicated_tasks) > 1:
        print("Задач с таким названием несколько штук:")
        # то выводим id дубликатов задач
        for index, task in enumerate(duplicated_tasks):
            task_column_name = requests.get(base_url.format('lists') \
            	+ '/' + task['idList'], params=auth_params).json()['name']
            print("Задача #{}\tid: {}\tНаходится в колонке: {}\t ".format \
                (index, task['id'], task_column_name))
        task_id = input("Пожалуйста, введите ID задачи, которую нужно переместить: ")
    else:
        task_id = duplicated_tasks[0]['id']
    # Проверяем существует ли колонка
    column_id = column_check(column_name)
    # Теперь, когда у нас есть id задачи, которую мы хотим переместить    
    # Найдем id колонки, в которую мы будем перемещать задачу
    if column_id is None:
    	# Если ее не существует, то создаем колонку на доске
        column_id = create_column(column_name, False).json()['id']
    # Перемещаем задачу
    request = requests.put(base_url.format('cards') + '/' + task_id \
        + '/idList', data={'value': column_id, **auth_params})
    if request.status_code == 200:
        print('--- Задача "{}" перемещена! ---'.format(name))
        read_task()
    else:
        print('--- Возникла ошибка {}. '.format(request.status_code) \
        	+ 'Задача "{}" не перемещена! ---'.format(name))

def delete_column(column_name):
	# Проверяем существует ли колонка
    column_id = column_check(column_name)
    # Если колонкине существует,
    if column_id is None:
    	# то выводим сообщение
        print('--- Колонки "{}" нет на доске! ---'.format(column_name))
        return
    # Удаляем колонку в архив
    request = requests.put(base_url.format('lists') + '/' + column_id + '/closed', \
    	data={'value': 1, **auth_params})
    if request.status_code == 200:
        print('--- Колонка "{}" удалена в архив! ---'.format(column_name))
        read_task()
    else:
        print('--- Возникла ошибка {}. '.format(request.status_code) \
        	+ 'Колонка "{}" не удалена! ---'.format(column_name))

def delete_task(name):
    # Проверим существуют ли дубликаты нашей задачи
    duplicated_tasks = get_duplicated_tasks(name)
    # Если задачи не существует,
    if not duplicated_tasks:
    	# то выводим сообщение
        print('--- Задача "{}" не найдена! ---'.format(name))
        return
    # Если найдены дубликаты задач, 
    if len(duplicated_tasks) > 1:
        print("Задач с таким названием несколько штук:")
        # то выводим id дубликатов задач
        for index, task in enumerate(duplicated_tasks):
            task_column_name = requests.get(base_url.format('lists') \
            	+ '/' + task['idList'], params=auth_params).json()['name']
            print("Задача #{}\tid: {}\tНаходится в колонке: {}\t ".format \
                (index, task['id'], task_column_name))
        task_id = input("Пожалуйста, введите ID задачи, которую нужно удалить: ")
    else:
        task_id = duplicated_tasks[0]['id'] 	
    # Удалим задачу в найденной колонке
    request = requests.delete(base_url.format('cards') + '/' + task_id, params=auth_params)
    if request.status_code == 200:
        print('--- Задача "{}" удалена! ---'.format(name))
        read_task()
    else:
        print('--- Возникла ошибка {}. '.format(request.status_code) \
        	+ 'Задача "{}" не удалена! ---'.format(name))

def help():
    print('>>> Для работы с приложением используйте следующие параметры:')
    print('\t-ct | для создания задачи в определенной колонке')
    print('\tПример: python trello.py -ct "task_name" "column_name"')
    print('\t-cс | для создания колонки')
    print('\tПример: python trello.py -cc "column_name"')
    print('\t-mt | для перемещения задачи в определенную колонку')
    print('\tПример: python trello.py -mt "task_name" "column_name"')
    print('\t-dс | для удаления колонки')
    print('\tПример: python trello.py -dc "column_name"')
    print('\t-dt | для удаления задачи')
    print('\tПример: python trello.py -dt "task_name"')

if __name__ == "__main__":
    if len(sys.argv) < 2:      # Выводим колонки и их список задач
        read_task()
    elif sys.argv[1] == '-ct': # Создаем задачу в определенной колонке
        create_task(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == '-cc': # Создаем колонку
        create_column(sys.argv[2], True)
    elif sys.argv[1] == '-mt': # Перемаещем задачу в другую колонку
        move_task(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == '-dc': # Удаляем колонку
        delete_column(sys.argv[2])
    elif sys.argv[1] == '-dt': # Удаляем задачу
        delete_task(sys.argv[2])
    else:
    	help()
