# ORM proxy deployment architecture

ORM generates configuration for Varnish and HAProxy. The deployment uses HAProxy as main frontend, listening on HTTP and HTTPS, and performing TLS termination in front of Varnish when HTTPS is used.

All HTTP traffic is then sent to Varnish which handles all rule `matches` and `actions` except `backend`. If the traffic `matches` a rule with a `backend`, Varnish sets a header which identifies the ORM rule, and sends the traffic back to a second, internal HAProxy listener (on a different port).

HAProxy uses the header to perform the `backend` action. For more details, see the deployment example in the `lxd` folder, and examine the generated output from ORM.

## Example deployment schematic

```
             client
              ^ |
              | |
              | V :80 :443
   +-HAProxy-------------+            +-Varnish-----+
   |          ^  \       | HTTP :6081 |             |
   |          |\  - - - -|----------->|- - - -      |
   |          | - - - - -|<-----------|- - no |     |
   |          |          |            |     \ |     |
   |          |          |            |    backend? |
   |          |          |            |       |     |
   |          |          |            |      yes    |
   |          |          | HTTP :4444 |       |     |
   |          |   - - - -|<-----------|- - - -      |
   |          |  /       |            |             |
   +---------------------+            +-------------+
              ^ |
              | | HTTP/HTTPS
              | |
              | V
         #      %    "
      ?    *       !    $
        =   backends  ^   +
      `              ?
        &    #  &      @
```

## Why HAProxy?

A stand-alone Varnish instance can perform most tasks that the ORM array can. So why take the detour through HAProxy?

The reason for including HAProxy in the deployment stems mainly from the fact that:
- Varnish does not support incoming HTTPS traffic
- Varnish (without Plus) does not support HTTPS backends
- HAProxy does load balancing better than Varnish
