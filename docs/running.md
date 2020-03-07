# Installing and running ORM

ORM is available as a python `pip` package and as a Docker image.

## Using the python package:

`pip install origin-routing-machine`

`orm --help`

## Using the docker image:

`docker run --name orm --rm -v ${PWD}:${PWD} -w ${PWD} -it svtwebcoreinfra/orm --help`

# What happens when I run ORM?

When ORM is run with a path to a ruleset, the rules under the path are:

 * validated and checked for any collisions, i.e. instances of overlapping rules that try to modify the same requests
 * translated into HAProxy and Varnish configuration

## Example

For an example of using ORM with included example rules, and to try it out locally, see [example/README.md](example/README.md).

For a more production-like setup, see the [lxd/](../lxd) folder. This deployment is used for the release tests of ORM.
