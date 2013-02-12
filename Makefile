develop:
	pip install "flake8>=1.7" --use-mirrors
	pip install ipdb --use-mirrors
	pip install nose --use-mirrors
	pip install mock --use-mirrors
	pip install -e . --use-mirrors
	easy_install readline

test: lint test-python

test-python:
	@echo "Running Python tests"
	nose --with-coverage -w tests
	@echo ""

lint: lint-python

lint-python:
	@echo "Linting Python files"
	flake8 --ignore=E121,W404 . || exit 1
	@echo ""
