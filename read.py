import os
import asyncio
from git import Repo
from concurrent.futures import ThreadPoolExecutor
import subprocess

username = ''
password = ''

project = ''
repo_slug = ''

bitbucket_url = ''

# Список репозиториев
repositories = [
    f'http://{username}:{password}@{bitbucket_url}/scm/{project}/{repo_slug}.git',
    # Добавьте другие репозитории здесь
]

# Временная директория для клонирования репозиториев
base_clone_dir = 'repos'

# Создаем базовую директорию, если она не существует
os.makedirs(base_clone_dir, exist_ok=True)

base_clone_dir = f"{base_clone_dir}/{project}"

# Функция для подсчета строк в репозитории
def count_lines_in_repo(repo_url, clone_dir):
    # Извлекаем имя репозитория из URL
    repo_name = repo_url.split('/')[-1].replace('.git', '')
    repo_clone_path = os.path.join(clone_dir, repo_name)

    print(f'Клонируем репозиторий: {repo_name}...')
    try:
        # Клонируем репозиторий
        Repo.clone_from(repo_url, repo_clone_path, branch='master')
    except Exception as e:
        print(f'Ошибка при клонировании репозитория {repo_name}: {e}')
        return repo_name, 0

    # Переходим в директорию репозитория
    os.chdir(repo_clone_path)

    # Выполняем команду git ls-files | xargs wc -l
    result = subprocess.run(
        'git ls-files | xargs wc -l',
        shell=True,  # Используем shell для выполнения пайпов
        capture_output=True,
        text=True
    )

    # Проверяем, что команда выполнена успешно
    if result.returncode != 0:
        print(f"Ошибка при выполнении команды в репозитории {repo_name}: {result.stderr}")
        return repo_name, 0

    # Получаем вывод команды
    output = result.stdout

    # Парсим вывод, чтобы получить общее количество строк
    total_lines = 0
    # for line in output.splitlines():
    #   if line.strip().endswith(' main.cpp'):
    #        total_lines = int(line.strip().split()[0])
    #        break
    if ' total' in output:
        # Если есть строка с 'total', берем значение из неё
        for line in output.splitlines():
            if line.strip().endswith(' total'):
                total_lines = int(line.strip().split()[0])
                break
    else:
        # Если строки с 'total' нет, берем последнюю строку
        last_line = output.splitlines()[-1]
        if last_line.strip():  # Проверяем, что строка не пустая
            total_lines = int(last_line.strip().split()[0])

    print(f'Результат для {repo_name}: {total_lines} строк')
    return repo_name, total_lines

# Словарь для хранения результатов
results = {}

# Обрабатываем каждый репозиторий в отдельном потоке
with ThreadPoolExecutor(max_workers=7) as executor:
    futures = {executor.submit(count_lines_in_repo, repo_url, base_clone_dir): repo_url for repo_url in repositories}

    for future in futures:
        repo_url = futures[future]
        try:
            repo_name, total_lines = future.result()
            results[repo_name] = total_lines
        except Exception as e:
            print(f'Ошибка при обработке репозитория {repo_url}: {e}')

# Выводим итоговые результаты
print("\nИтоговые результаты:")
for repo_name, total_lines in results.items():
    print(f'{repo_name}: {total_lines} строк')
