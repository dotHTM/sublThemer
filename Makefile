
build: log/build.txt

requirements.txt:
	pip-compile -U

log/install/pip-dev.txt: requirements-dev.txt
	mkdir -p log/install
	pip3 install -r requirements-dev.txt | tee log/install/pip-dev.txt

pre-commit-install: .pre-commit-config.yaml log/install/pip-dev.txt
	pre-commit install

log/build.txt: pyproject.toml src/sublThemer/*.py  requirements.txt log/install/pip-dev.txt
	pip3 install -e . | tee log/build.txt
