#PYTHON=		/usr/local/python/3.6.3/bin/python3.6
PYTHON=		python3
SOURCE=		bobcat_feeder
VENV=		venv
WHEELHOUSE=	../wheels

$(WHEELHOUSE):
		mkdir $@

$(VENV): requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --pre --find-links $(WHEELHOUSE) -r requirements.txt
	touch $(VENV)

upgrade-venv:: $(VENV)
	$(VENV)/bin/pip install --pre --find-links $(WHEELHOUSE) -r requirements.txt --upgrade

dist: wheel

server: $(VENV)
	env PYTHONPATH=`pwd` $(VENV)/bin/python bobcat_feeder/main.py --config=example/config.yaml --debug

wheel: $(VENV) $(WHEELHOUSE)
	$(VENV)/bin/python setup.py bdist_wheel --dist-dir $(WHEELHOUSE)

install:
	$(VENV)/bin/pip install --find-links $(WHEELHOUSE) --upgrade $(SOURCE)

clean:
	rm -fr $(CLEANFILES)

realclean: clean
	rm -fr $(VENV)

