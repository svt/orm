# Building ORM from source

## Dependencies

To build ORM and run the included unit tests the following dependencies are needed:

- make
- pyenv

### Optional components

`LXD` is needed to build the ORM deployment image and to run the deployment tests.

`docker` is needed to build and distribute the docker images.

## Build python package

In the top directory, run:
```console
foo@bar $ make dist
```

## Build docker images

In the top directory, run:
```console
foo@bar $ make build-docker
```
Two docker images are built, each using a different interpreter: One with `python` and one with `pypy`. The rule validation is much faster with the `pypy` image.

## Build ORM deployment image (LXD)

In the top directory, run:
```console
foo@bar $ make build-orm-deployment
```
