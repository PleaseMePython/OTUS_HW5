setup:
	pip install poetry
	poetry env activate
	poetry lock
	poetry install
run:
	docker-compose up -d
	python -m otus_hw5\api.py
lint:
	poetry run ruff check src
	poetry run ruff check tests
format:
	poetry run ruff format src
	poetry run ruff format tests
test:
	coverage run -m pytest -v .\tests\unit --without-integration
	coverage report -m
integration:
	docker-compose up -d
	coverage run -m pytest -v .\tests\integration --with-integration
	coverage report -m
