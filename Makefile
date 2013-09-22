PYTHON = python
SETUP = $(PYTHON) setup.py
ifeq ($(shell $(PYTHON) -c "import sys; print sys.version_info >= (2, 7)"),True)
TESTRUNNER ?= unittest
else
TESTRUNNER ?= unittest2.__main__
endif
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
	$(MAKE) check-noextensions PYTHON=pypy

check-all: check check-pypy

clean::
	$(SETUP) clean --all
