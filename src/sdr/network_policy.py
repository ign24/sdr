"""Política de red segura para requests HTTP salientes."""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

CONNECT_TIMEOUT = 5.0
READ_TIMEOUT = 10.0
MAX_REDIRECTS = 5
MAX_RESPONSE_BYTES = 5 * 1024 * 1024

Resolver = Callable[[str], Iterable[str]]

_METADATA_HOSTS = {
    "instance-data.ec2.internal",
    "metadata.azure.internal",
    "metadata.google.internal",
    "metadata.goog",
}
_METADATA_ADDRESSES = {
    ipaddress.ip_address("100.100.100.200"),
    ipaddress.ip_address("169.254.169.254"),
    ipaddress.ip_address("169.254.170.2"),
    ipaddress.ip_address("192.0.0.192"),
    ipaddress.ip_address("fd00:ec2::254"),
}
_SUPPORTED_APPLICATION_TYPES = {
    "application/json",
    "application/markdown",
    "application/xhtml+xml",
    "application/xml",
}


class NetworkPolicyError(ValueError):
    """La URL o respuesta viola la política de red saliente."""


@dataclass(frozen=True)
class HttpResult:
    """Respuesta HTTP acotada, ya cerrada y segura para persistir."""

    url: str
    status_code: int
    headers: dict[str, str]
    content: bytes

    @property
    def text(self) -> str:
        content_type = self.headers.get("content-type", "")
        charset = "utf-8"
        for parameter in content_type.split(";")[1:]:
            key, separator, value = parameter.strip().partition("=")
            if separator and key.lower() == "charset":
                charset = value.strip(' "') or charset
                break
        try:
            return self.content.decode(charset, errors="replace")
        except LookupError:
            return self.content.decode("utf-8", errors="replace")


def resolve_host(host: str) -> list[str]:
    """Resuelve todas las direcciones candidatas de un hostname."""
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise NetworkPolicyError(f"no se pudo resolver el hostname {host!r}") from exc
    return sorted({str(record[4][0]) for record in records})


def validate_http_url(url: str, *, resolver: Resolver | None = None) -> None:
    """Valida esquema y todas las IP resultantes antes de conectar."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise NetworkPolicyError(f"URL HTTP/HTTPS inválida: {url!r}") from exc
    if parsed.scheme.lower() not in {"http", "https"} or not host:
        raise NetworkPolicyError("solo se permiten URLs HTTP/HTTPS absolutas")
    if port is not None and not 1 <= port <= 65535:
        raise NetworkPolicyError(f"puerto inválido en URL: {url!r}")

    normalized_host = host.rstrip(".").lower()
    if normalized_host in _METADATA_HOSTS or any(
        normalized_host.endswith(f".{metadata_host}") for metadata_host in _METADATA_HOSTS
    ):
        raise NetworkPolicyError(f"hostname de metadata cloud bloqueado: {host}")

    try:
        literal_address = ipaddress.ip_address(normalized_host)
    except ValueError:
        addresses = list((resolver or resolve_host)(normalized_host))
        if not addresses:
            raise NetworkPolicyError(f"el hostname {host!r} no resolvió direcciones") from None
    else:
        addresses = [str(literal_address)]

    for raw_address in addresses:
        try:
            address = ipaddress.ip_address(raw_address)
        except ValueError as exc:
            raise NetworkPolicyError(
                f"resolución DNS inválida para {host!r}: {raw_address!r}"
            ) from exc
        if address in _METADATA_ADDRESSES:
            raise NetworkPolicyError(f"dirección de metadata cloud bloqueada: {address}")
        if any(
            (
                address.is_loopback,
                address.is_private,
                address.is_link_local,
                address.is_multicast,
                address.is_unspecified,
                address.is_reserved,
                not address.is_global,
            )
        ):
            raise NetworkPolicyError(f"dirección no pública bloqueada para {host!r}: {address}")


def fetch_http(
    url: str,
    *,
    method: str = "GET",
    client: httpx.Client | None = None,
    resolver: Resolver | None = None,
    max_redirects: int = MAX_REDIRECTS,
    max_response_bytes: int | None = None,
    require_text_content: bool = False,
) -> HttpResult:
    """Ejecuta un request validando cada salto y leyendo el cuerpo de forma acotada."""
    timeout = httpx.Timeout(READ_TIMEOUT, connect=CONNECT_TIMEOUT)
    owned_client = client is None
    active_client = client or httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
    )
    current_url = url
    redirects = 0
    try:
        while True:
            validate_http_url(current_url, resolver=resolver)
            with active_client.stream(
                method,
                current_url,
                follow_redirects=False,
                timeout=timeout,
            ) as response:
                if response.has_redirect_location:
                    if redirects >= max_redirects:
                        raise NetworkPolicyError(
                            f"se excedió el límite de {max_redirects} redirects"
                        )
                    current_url = urljoin(str(response.url), response.headers["location"])
                    redirects += 1
                    continue

                content = b""
                if max_response_bytes is not None:
                    _validate_content_type(response, require_text_content=require_text_content)
                    _validate_content_length(response, max_response_bytes)
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > max_response_bytes:
                            raise NetworkPolicyError(
                                "la respuesta excede el tamaño máximo de "
                                f"{max_response_bytes} bytes"
                            )
                        chunks.append(chunk)
                    content = b"".join(chunks)
                return HttpResult(
                    url=str(response.url),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                )
    finally:
        if owned_client:
            active_client.close()


def _validate_content_type(response: httpx.Response, *, require_text_content: bool) -> None:
    if not require_text_content:
        return
    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if not content_type.startswith("text/") and content_type not in _SUPPORTED_APPLICATION_TYPES:
        raise NetworkPolicyError(f"content-type no soportado: {content_type or 'ausente'}")


def _validate_content_length(response: httpx.Response, maximum: int) -> None:
    raw_length = response.headers.get("content-length")
    if raw_length is None:
        return
    try:
        length = int(raw_length)
    except ValueError:
        return
    if length > maximum:
        raise NetworkPolicyError(f"la respuesta excede el tamaño máximo de {maximum} bytes")
