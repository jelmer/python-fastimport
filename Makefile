PYTHON = python3
RUFF ?= ruff
MYPY ?= mypy
SETUP = $(PYTHON) setup.py
TESTRUNNER ?= unittest
RUNTEST = PYTHONPATH=.:$(PYTHONPATH) $(PYTHON) -m $(TESTRUNNER)

DESTDIR=/

all: build

build::
	$(SETUP) build

install::
	$(SETUP) install --root="$(DESTDIR)"

check:: build
	$(RUNTEST) fastimport.tests.test_suite

check-pypy:: clean
	$(MAKE) check PYTHON=pypy

check-all: check check-pypy

clean::
	$(SETUP) clean --all

style:
	$(RUFF) check fastimport

typing:
	$(MYPY) fastimport
