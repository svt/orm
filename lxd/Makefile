.PHONY: all build clean

BASE_IMAGE = "ubuntu:16.04"
ORM_TAG := $(shell git describe --tags)

all: build

env: requirements.txt
	virtualenv -p python3 env
	. env/bin/activate && \
		pip install -r requirements.txt

clean:
	rm -rf env
	rm -rf dist
	lxc delete --force orm || true
	lxc image delete orm || true

build: clean env
	lxc launch ${BASE_IMAGE} orm
	./wait_for_orm.sh
	lxc exec orm -- apt-get update -q
	lxc exec orm -- apt-get install -y python
	. env/bin/activate && \
		ansible-playbook -i ansible/inventory.yml ansible/orm_provision.yml
	lxc stop orm
	lxc publish orm \
		--alias orm \
		description="ORM Routing Machine" \
		version="${ORM_TAG}"
	mkdir dist
	lxc image export orm dist/orm-image

orm-ip:
	@lxc list orm -c 4 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+"
