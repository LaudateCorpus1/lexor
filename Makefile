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

export:
	git archive --format zip --output lexor.zip master

clean:
	rm -rf lexor.egg-info
	rm -rf build

pypi:
	python setup.py sdist upload

test:
	nosetests -vs .
