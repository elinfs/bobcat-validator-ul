PYTHON=		/usr/local/3.6.3/bin/python3.6
SUDO=		sudo

VENV?=		${CURDIR}/venv
WHEELHOUSE?=	${CURDIR}/wheels
REQUIREMENTS?=	requirements.txt

ALL_PYMODULES=	cronConf feeder
PYMODULES?=	$(ALL_PYMODULES)


all: build

$(WHEELHOUSE):
	mkdir $@

depend: $(WHEELHOUSE)/.depend

$(WHEELHOUSE)/.depend: $(WHEELHOUSE) $(VENV) $(REQUIREMENTS)
	rm -f $(WHEELHOUSE)/*.whl
	$(VENV)/bin/pip wheel -r $(REQUIREMENTS) -w $(WHEELHOUSE)
	$(VENV)/bin/pip install --find-links $(WHEELHOUSE) -r $(REQUIREMENTS)
	touch $@

$(REQUIREMENTS):
	(for module in $(PYMODULES); do \
		cat ${CURDIR}/$$module/requirements.txt ;\
	done) | sort -u | grep -v bobcat_ > $@

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip wheel

build: $(WHEELHOUSE)/.depend
	for module in $(PYMODULES); do \
		$(MAKE) -C $$module WHEELHOUSE=$(WHEELHOUSE) VENV=$(VENV) wheel install ;\
	done

clean:
	rm -f $(REQUIREMENTS)
	for module in $(PYMODULES); do \
		$(MAKE) -C $$module WHEELHOUSE=$(WHEELHOUSE) VENV=$(VENV) clean ;\
	done

realclean:: clean
	rm -fr $(VENV) $(WHEELHOUSE)
