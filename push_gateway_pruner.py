import requests
import logging
import base64
import sys
import threading
import urllib.parse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from typing import Generator, Dict
from datetime import datetime

import click
from prometheus_client import parser, Metric
from prometheus_client.samples import Sample

logger = logging.getLogger()


def start_interval(
    prune_interval_seconds,
    pushgateway_url,
    prune_threshold_seconds,
    requests_timeout,
    prune_metric_name,
):
    threading.Timer(
        prune_interval_seconds,
        start_interval,
        [
            prune_interval_seconds,
            pushgateway_url,
            prune_threshold_seconds,
            requests_timeout,
            prune_metric_name,
        ],
    ).start()
    prune(pushgateway_url, prune_threshold_seconds, requests_timeout, prune_metric_name)


def configure_requests() -> requests.Session:
    # Mount HTTPAdapter to add retries for all requests.
    retry_strategy = Retry(
        total=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "DELETE"],
        backoff_factor=1,  # sleep between retries
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    assert_status_hook = lambda response, *args, **kwargs: response.raise_for_status()
    http.hooks["response"] = [assert_status_hook]
    return http


def prune(
    pushgateway_url: str,
    prune_threshold_seconds: int,
    requests_timeout: int,
    prune_metric_name: str,
):
    logger.info(
        f"Starting pruning for {pushgateway_url} with prune threshold = {prune_threshold_seconds} seconds"
    )
    http = configure_requests()
    raw_metrics = get_metrics(pushgateway_url, requests_timeout, http)
    metrics = parse_raw_metrics(raw_metrics)
    filtered_samples = filter_metrics(
        metrics, prune_metric_name, prune_threshold_seconds
    )
    delete_old_samples(filtered_samples, pushgateway_url, requests_timeout, http)
    logger.info(f"Done with push_gateway_pruner.")


def get_metrics(
    pushgateway_url: str, requests_timeout: int, http: requests.Session
) -> str:
    url = urllib.parse.urljoin(pushgateway_url, "metrics")
    res = http.get(url, timeout=requests_timeout)
    return res.text


def parse_raw_metrics(metrics_txt: str) -> Generator[Metric, None, None]:
    return parser.text_string_to_metric_families(metrics_txt)


def filter_metrics(
    metrics: Generator[Metric, None, None],
    prune_metric_name: str,
    prune_threshold_seconds: int,
) -> Generator[Sample, None, None]:
    now = datetime.utcnow().timestamp()
    for metric in metrics:
        if metric.name == prune_metric_name:
            for sample in metric.samples:
                if now - sample.value > prune_threshold_seconds:
                    yield sample


def delete_old_samples(
    samples: Generator[Sample, None, None],
    pushgateway_url: str,
    requests_timeout: int,
    http: requests.Session,
):
    for sample in samples:
        url = build_url_from_labels(sample.labels, pushgateway_url)
        http.delete(url, timeout=requests_timeout)
        logger.debug(f"Sent delete request for {url}")


def build_url_from_labels(labels: Dict[str, str], pushgateway_url: str) -> str:
    """
    Converts dictionary of labels to the format required by pushgateway:
    <pushgateway_url>/metrics/job/<JOB_NAME>{/<LABEL_NAME>/<LABEL_VALUE>}

    Must start with job key/value. Order of remaining keys doesn't matter
    and will match any group with the same set of labels.

    There is a bug where if the group is /job/<job>/instance/<EMPTY STRING> and there are no other labels,
    it wouldn't be able to delete it for some reason. Extreme edge case since instance should almost always be provided.
    """

    if "job" not in labels:
        raise ValueError(f"Job key not found in labels. Labels: {labels}")

    url = urllib.parse.urljoin(pushgateway_url, f"metrics/job/{labels['job']}")
    for key, value in labels.items():
        if key != "job":
            # empty strings need to be replaced with '='
            urlsafe_value = (
                base64.urlsafe_b64encode(bytes(value, "utf-8")).decode("utf-8")
                if len(value) > 0
                else "="
            )
            url += f"/{key}@base64/{urlsafe_value}"
    return url


@click.command()
@click.option(
    "--prune_interval_seconds",
    default=600,
    type=int,
    help="How often to start the pruning job in seconds. Default is 600.",
)
@click.option(
    "--pushgateway_url",
    default="http://localhost:9091/",
    type=str,
    help="URL for your pushgateway instance (without /metrics postfix). Default is http://localhost:9091/",
)
@click.option(
    "--prune_threshold_seconds",
    default=600,
    type=int,
    help="Number of seconds since <prune_metric_name>'s value after which to prune a sample. Default is 600.",
)
@click.option(
    "--requests_timeout",
    default=10,
    type=int,
    help="Timeout in seconds for the Get request to <pushgateway url>/metrics. Default is 10.",
)
@click.option(
    "--prune_metric_name",
    default="push_time_seconds",
    type=str,
    help="The name of the metric which is used as each group's start time. Default is 'push_time_seconds'.",
)
@click.option(
    "--logging_level",
    default="INFO",
    type=str,
    help="Logging Level",
)
def main(
    prune_interval_seconds,
    pushgateway_url,
    prune_threshold_seconds,
    requests_timeout,
    prune_metric_name,
    logging_level,
):
    try:
        logger.setLevel(logging_level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging_level)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        start_interval(
            prune_interval_seconds,
            pushgateway_url,
            prune_threshold_seconds,
            requests_timeout,
            prune_metric_name,
        )

    except Exception as e:
        logger.error(
            f"Error for push-gateway-pruner pruning pushgateway at {pushgateway_url}", e
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
