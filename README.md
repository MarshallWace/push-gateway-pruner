# Push Gateway Pruner

[![Docker](https://github.com/MarshallWace/push-gateway-pruner/workflows/Publish%20Docker/badge.svg)](https://github.com/MarshallWace/push-gateway-pruner/actions?query=workflow%3A%22Publish+Docker%22) 

Pruner for Prometheus Pushgateway.

Features:
* Prunes (deletes) Pushgateway groups based on elapsed time.
* Elapsed time is calculated via utcnow - prune_metric_name, where prune_metric_name defaults to 'push_time_seconds'


# Run
```
$ docker run -it ghcr.io/marshallwace/push-gateway-pruner --pushgateway_url <YOUR URL> --prune_interval_seconds <YOUR VALUE>
```

# Local Dev
Setup:
```
make setup
```
Test:
```
make test
```
Run:
```
make run
```

Build with CA cert:
```
docker build --build-arg CA_CERT_PATH=<YOUR PATH> .
```