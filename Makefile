PACKAGE := $(shell basename *.spec .spec)
ARCH = noarch
RPMBUILD = rpmbuild --define "_topdir %(pwd)/rpm-build" \
	--define "_builddir %{_topdir}" \
	--define "_rpmdir %(pwd)/rpms" \
	--define "_srcrpmdir %{_rpmdir}" \
	--define "_sourcedir  %{_topdir}"
PYTHON = $(which python)

all: rpms

clean:
	rm -rf dist/ build/ rpm-build/ rpms/
	rm -rf docs/*.gz MANIFEST *~
	rm -rf .tox/
	find . -name '*.pyc' -exec rm -f {} \;
	find . -name '__pycache__' -exec rm -rf {} \; -prune

build: clean
	python setup.py build -f

install: build
	python setup.py install -f

reinstall: uninstall install

uninstall: clean
	rm -f /usr/bin/${PACKAGE}
	rm -rf /usr/lib/python2.*/site-packages/${PACKAGE}

uninstall_rpms: clean
	rpm -e ${PACKAGE}

sdist:
	python setup.py sdist

prep_rpmbuild: build sdist
	mkdir -p rpm-build
	mkdir -p rpms
	cp dist/*.gz rpm-build/

rpms: prep_rpmbuild
	${RPMBUILD} -ba ${PACKAGE}.spec

srpm: prep_rpmbuild
	${RPMBUILD} -bs ${PACKAGE}.spec
