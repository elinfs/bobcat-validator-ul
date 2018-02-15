PYTHON=		/usr/local/3.6.3/bin/python3.6
SOURCE=		twins_test
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

wheel: $(VENV) $(WHEELHOUSE)
	$(VENV)/bin/python setup.py bdist_wheel --dist-dir $(WHEELHOUSE)

install:
	$(VENV)/bin/pip install --find-links $(WHEELHOUSE) --upgrade $(SOURCE)

clean:
	rm -fr $(CLEANFILES)

realclean: clean
	rm -fr $(VENV)

agent:
	$(VENV)/bin/python $(SOURCE)/ReportConnectivity.py