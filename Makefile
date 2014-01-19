# lexor makefile

all: install-user

install:
	python setup.py install

install-user:
	python setup.py install --user

build:
	python setup.py sdist

develop:
	python setup.py develop --user

clean:
	rm -rf lexor.egg-info
	rm -rf build
