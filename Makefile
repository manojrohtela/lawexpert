run:
	uvicorn backend.main:app --reload

build:
	python3 -m backend.cli

test:
	pytest -q

