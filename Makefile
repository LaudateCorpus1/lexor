# lexor makefile

all: install-user

install:
	python setup.py install
	make clean

install-user:
	python setup.py install --user
	make clean

build:
	python setup.py sdist
	make clean

develop:
	python setup.py develop --user
	make clean

clean:
	rm -rf lexor.egg-info
	rm -rf build
