.PHONY: lint test clean clean-dist update-deps list-outdated-deps dist \
	build-docker build-python3-docker build-pypy-docker push-docker \
	push-python3-docker push-pypy-docker push-latest-docker \
	deployment-test release-test

PYTHON_VERSION=3.7.1
PYTHON_INSTALL=.pyenv/versions/${PYTHON_VERSION}

PIP_VERSION=21.0.1

TESTFILES := $(wildcard test/test_*.py)
TESTS := $(subst test/,,$(subst .py,,${TESTFILES}))

CODEFILES := $(wildcard orm/*.py *.py)
LINTFILES := $(patsubst %.py,lint_%,${CODEFILES})

ORM_TAG := $(shell git describe --tags)

DOCKER ?= docker
DOCKER_IMAGE_BASE_NAME ?= svtwebcoreinfra/orm
PYPI_PACKAGE_NAME = origin-routing-machine

ifdef CI
PYENV=

.pyenv: requirements.txt
	@echo "CI detected! Using the CI-provided python."
	python --version
	make env-install
else
PYENV_ENV=PYENV_ROOT=$(shell pwd)/.pyenv PYENV_VERSION=${PYTHON_VERSION}
PYENV=${PYENV_ENV} pyenv exec

${PYTHON_INSTALL}:
	${PYENV_ENV} pyenv install ${PYTHON_VERSION}

.pyenv: ${PYTHON_INSTALL} build_requirements.txt requirements.txt
	@echo "This is a local build! Using pyenv for python"
	${PYENV} python --version
	make env-install
endif

pyenv-exec:
	${PYENV} ${PYENV_ARGS}

env-install: ${PYTHON_INSTALL} build_requirements.txt requirements.txt
	${PYENV} pip install pip==${PIP_VERSION}
	${PYENV} python --version
	${PYENV} pip --version
	${PYENV} pip install -r build_requirements.txt
	${PYENV} pip-sync build_requirements.txt requirements.txt
	touch .pyenv

ifndef CI
update-deps:
	make env-install
	export CUSTOM_COMPILE_COMMAND="make $@" && \
		${PYENV} pip-compile --upgrade --output-file requirements.txt setup.py && \
		${PYENV} pip-compile --upgrade --output-file build_requirements.txt build_requirements.in
	make env-install
endif

list-outdated-deps: .pyenv
	$(PYENV) pip list --outdated

lint: .pyenv
	echo 'lint code'
	${PYENV} pylint ${CODEFILES}
	echo 'lint tests'
	${PYENV} pylint --disable=similarities ${TESTFILES}

formatting:
	${PYENV} pip install black
	@echo 'check formatting'
	${PYENV} black --check orm || (echo "Run 'make black' to run the formatter"; exit 1)

black:
	${PYENV} pip install black
	${PYENV} black orm

${LINTFILES}:
	${PYENV} pylint $(subst lint_,,$@).py

test: .pyenv ${TESTS}

${TESTS}:
	@echo "Test: $@"
	PYTHONPATH=. ${PYENV} python test/$@.py

dist: clean-dist .pyenv
	ORM_TAG=${ORM_TAG} ${PYENV} python setup.py sdist

clean-deployment-test:
	rm -f orm-rules-tests/globals-test/cache.pkl
	rm -f orm-rules-tests/rules-test/cache.pkl
	rm -rf out

clean-dist:
	rm -rf dist *.egg-info orm/__pycache__

clean-pyenv:
	rm -rf .pyenv

clean: clean-dist clean-deployment-test clean-pyenv

build-docker: build-python3-docker build-pypy-docker

build-python3-docker: clean-dist
	${DOCKER} build \
		--build-arg ORM_TAG=${ORM_TAG} \
		-t ${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}-python3 \
		-f .docker/Dockerfile-python3 .

# Build the pypy image and tag it with latest and the ORM_TAG.
# This enables pypy to be the default docker image
build-pypy-docker: clean-dist
ifeq (,$(findstring -,$(ORM_TAG)))
	@echo "Building and tagging with latest."
	${DOCKER} build \
		--build-arg ORM_TAG=${ORM_TAG} \
		-t ${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}-pypy \
		-t ${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG} \
		-t ${DOCKER_IMAGE_BASE_NAME}:latest \
		-f .docker/Dockerfile-pypy .
else
	@echo "Not tagging latest for pre-release versions"
	${DOCKER} build \
		--build-arg ORM_TAG=${ORM_TAG} \
		-t ${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}-pypy \
		-t ${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG} \
		-f .docker/Dockerfile-pypy .
endif

push-docker: push-python3-docker push-pypy-docker push-latest-docker
	${DOCKER} push "${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}"

push-python3-docker: build-python3-docker
	${DOCKER} push "${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}-python3"

push-pypy-docker: build-pypy-docker
	${DOCKER} push "${DOCKER_IMAGE_BASE_NAME}:${ORM_TAG}-pypy"

# Only push the latest tag for non pre-release versions
# NOTICE: The following will only match "-" as part of the tag.
push-latest-docker: build-pypy-docker
ifeq (,$(findstring -,$(ORM_TAG)))
	@echo "Pushing latest tag to the hub"
	${DOCKER} push "${DOCKER_IMAGE_BASE_NAME}:latest"
else
	@echo "Not pushing latest for pre-release versions"
endif

dist/orm-%.tar.gz: orm
	make dist

build-orm-deployment:
	make -C lxd

lxd/dist/orm-image.tar.gz:
	mkdir lxd/dist
	make build-orm-deployment

start-orm-deployment: lxd/dist/orm-image.tar.gz
	lxc image show orm >/dev/null 2>&1 || lxc image import lxd/dist/orm-image.tar.gz --alias orm
	lxc info orm >/dev/null 2>&1 || lxc launch orm orm
	(lxc info orm | grep -q 'Status: Running') || lxc start orm

deployment-test: .pyenv dist/orm-${ORM_TAG}.tar.gz start-orm-deployment
	${PYENV} pip install dist/${PYPI_PACKAGE_NAME}-${ORM_TAG}.tar.gz
	@echo "Linting deployment test rules"
	${PYENV} yamllint -c orm-rules-tests/.yamllint orm-rules-tests/
	@echo "Testing rules without globals actions"
	mkdir -p out/rules-test
	orm-rules-tests/start_echo_servers.sh
	${PYENV} orm \
			-r 'orm-rules-tests/rules-test/rules/**/*.yml' \
			-G 'orm-rules-tests/rules-test/globals.yml' \
			--cache-path 'orm-rules-tests/rules-test/cache.pkl' \
			-o out/rules-test
	lxd/update-orm-config.sh out/rules-test
	orm-rules-tests/wait_for_orm.sh
	${PYENV} orm \
		--test-target "$(shell make -s -C lxd orm-ip)" \
		--test-target-insecure \
		--orm-rules-path 'orm-rules-tests/rules-test/rules/**/*.yml' \
		--no-check
	lxc file push orm-rules-tests/test-maxconn-maxqueue-haproxy-output.sh orm/root/
	lxc exec orm /root/test-maxconn-maxqueue-haproxy-output.sh

	@echo "Testing rules with globals actions"
	mkdir -p out/globals-test
	orm-rules-tests/start_echo_servers.sh
	${PYENV} orm \
			-r 'orm-rules-tests/globals-test/rules/**/*.yml' \
			-G 'orm-rules-tests/globals-test/globals.yml' \
			--cache-path 'orm-rules-tests/globals-test/cache.pkl' \
			-o out/globals-test
	lxd/update-orm-config.sh out/globals-test
	orm-rules-tests/wait_for_orm.sh
	${PYENV} orm \
		--test-target "$(shell make -s -C lxd orm-ip)" \
		--test-target-insecure \
		--orm-rules-path 'orm-rules-tests/globals-test/rules/**/*.yml' \
		--no-check

release-test:
	make clean-dist
	make env-install
	make lint
	make black
	make test
	make clean-deployment-test
	make deployment-test
