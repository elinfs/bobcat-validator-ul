PYTHON=		/usr/local/python/3.6.3/bin/python3.6
SOURCE=		cron_conf
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

wheel: $(VENV) $(WHEELHOUSE) $(GENERATED)
	$(VENV)/bin/python setup.py bdist_wheel --dist-dir $(WHEELHOUSE)

install:
	$(VENV)/bin/pip install --find-links $(WHEELHOUSE) --upgrade $(SOURCE)

clean:
	rm -fr $(CLEANFILES)

realclean: clean
	rm -fr $(VENV)
