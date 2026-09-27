"""Generate real HTTP requests against the loopback demo; never supplies telemetry."""

import argparse
from urllib.error import HTTPError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["healthy", "errors", "slow"], default="errors")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    paths = {
        "healthy": ["/ok"] * 20,
        "errors": ["/ok", "/ok", "/ok", "/fail"] * 5,
        "slow": ["/slow"] * 3,
    }[args.scenario]
    statuses = []
    for path in paths:
        try:
            with urlopen(f"http://127.0.0.1:{args.port}{path}", timeout=10) as response:
                response.read()
                statuses.append(response.status)
        except HTTPError as error:
            statuses.append(error.code)
            error.close()
    print(f"Sent {len(statuses)} HTTP requests; observed {sum(s >= 500 for s in statuses)} server errors.")
    print("The application reporter measures and sends telemetry on its own timer.")


if __name__ == "__main__":
    main()
