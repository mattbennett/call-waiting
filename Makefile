test: flake8 pylint pytest

flake8:
	flake8 call_waiting.py test_call_waiting.py

pylint:
	pylint call_waiting -E

pytest:
	coverage run --source call_waiting.py --branch -m pytest test_call_waiting.py
	coverage report --show-missing --fail-under=100
