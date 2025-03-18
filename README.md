## API скоринга
### Описание
Пятое ДЗ курса Python Developer. Professional
Изучение unit- и интеграционного тестирование
### Запуск

ВНИМАНИЕ! Перед запуском переименовать файл .env_sample в .env и заполнить 
в нем параметры подключения к Redis

```cmd
    docker-compose up -d
    python -m otus_hw5.api.py
```

### Запуск тестов

Юнит-тесты
```cmd
    coverage run -m pytest -v .\tests\unit --without-integration
	coverage report -m
```

Интеграционный тест

ВНИМАНИЕ! Перед запуском переименовать файл .env_sample в .env и заполнить 
в нем параметры подключения к Redis

```cmd
    docker-compose up -d
	coverage run -m pytest -v .\tests\integration --with-integration
	coverage report -m
```