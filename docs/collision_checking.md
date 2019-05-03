# Collision checking

All rules are checked against each other to verify that no _matches_ overlap. This functionality is a great enabler for having multiple teams work with the same set of ORM rules without the fear of stepping on each others toes.

It's possible to turn off the collision checking, but this will result in unexpected behaviour if any rules should overlap.

When the number of rules starts to grow, the collision checking will take some time. Use the `--cache-path` flag to speed up the process (by avoiding to check rules which have not changed).
