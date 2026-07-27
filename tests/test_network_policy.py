import httpx
import pytest

from sdr.network_policy import NetworkPolicyError, fetch_http

PUBLIC_IP = "93.184.216.34"


def _resolver(mapping):
    def resolve(host: str):
        return mapping.get(host, [PUBLIC_IP])

    return resolve


@pytest.mark.parametrize("url", ["ftp://example.com/file", "file:///etc/passwd", "//example.com"])
def test_fetch_http_rejects_non_http_schemes_before_request(url):
    calls = []
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200))
    )

    with pytest.raises(NetworkPolicyError, match="HTTP/HTTPS"):
        fetch_http(url, client=client, resolver=_resolver({}))

    assert calls == []


def test_fetch_http_rejects_hostname_resolving_to_private_address_before_request():
    calls = []
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: calls.append(request) or httpx.Response(200))
    )

    with pytest.raises(NetworkPolicyError, match="no pública"):
        fetch_http(
            "https://public.example/resource",
            client=client,
            resolver=_resolver({"public.example": ["10.0.0.7"]}),
        )

    assert calls == []


def test_fetch_http_revalidates_redirect_target_and_blocks_private_destination():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/admin"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(NetworkPolicyError, match="no pública"):
        fetch_http(
            "https://public.example/start",
            client=client,
            resolver=_resolver({"public.example": [PUBLIC_IP]}),
        )

    assert calls == ["https://public.example/start"]


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.1.1",
        "224.0.0.1",
        "0.0.0.0",
        "240.0.0.1",
        "100.100.100.200",
    ],
)
def test_fetch_http_blocks_non_public_and_cloud_metadata_addresses(address):
    with pytest.raises(NetworkPolicyError, match="no pública|metadata"):
        fetch_http(f"http://{address}/", resolver=_resolver({}))


def test_fetch_http_limits_redirects():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "/again"})

    client = httpx.Client(transport=httpx.MockTransport(handler))

    with pytest.raises(NetworkPolicyError, match="redirects"):
        fetch_http(
            "https://public.example/start",
            client=client,
            resolver=_resolver({"public.example": [PUBLIC_IP]}),
            max_redirects=2,
        )
