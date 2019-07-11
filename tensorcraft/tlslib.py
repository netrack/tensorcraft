import logging
import pathlib
import ssl

from tensorcraft.logging import internal_logger


def create_server_ssl_context(tls: bool = False,
                              tlsverify: bool = False,
                              tlscert: str = None,
                              tlskey: str = None,
                              tlscacert: str = None,
                              logger: logging.Logger = internal_logger):
    """Create server SSL context with the given TLS parameters."""
    if not tls and not tlsverify:
        return None

    tlscert = pathlib.Path(tlscert).resolve(strict=True)
    tlskey = pathlib.Path(tlskey).resolve(strict=True)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(tlscert, tlskey)
    ssl_context.verify_mode = ssl.CERT_NONE

    logger.info("Using transport layer security")

    if not tlsverify:
        return ssl_context

    tlscacert = pathlib.Path(tlscacert).resolve(strict=True)

    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(cafile=tlscacert)
    logger.info("Using peer certificates validation")

    return ssl_context


def create_client_ssl_context(tls: bool = False,
                              tlsverify: bool = False,
                              tlscert: str = None,
                              tlskey: str = None,
                              tlscacert: str = None):
    """Create client SSL context with the given TLS parameters."""
    if not tls and not tlsverify:
        return None

    tlscert = pathlib.Path(tlscert).resolve(strict=True)
    tlskey = pathlib.Path(tlskey).resolve(strict=True)

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.load_cert_chain(tlscert, tlskey)

    if tlsverify:
        tlscacert = pathlib.Path(tlscacert).resolve(strict=True)

        ssl_context.load_verify_locations(cafile=tlscacert)
        ssl_context.load_default_certs(ssl.Purpose.SERVER_AUTH)
    else:
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    return ssl_context
