# See documentation in:
# https://docs.scrapy.org/en/latest/topics/download-handlers.html#writing-your-own-download-handler

from waybackpy import WaybackMachineAvailabilityAPI

from scrapy import Request
from scrapy.http import Response

from logging import getLogger

logger = getLogger(__name__)


class Wayback:
    """
    Convert requests for normal HTTPS webpages to fetch from Wayback Machine's web archive.
    """

    def process_request(self, request: Request) -> Request | Response | None:

        if request.meta.get('wayback_request') or request.url.startswith("https://web.archive.org/"):
            logger.info(f"Skipping re-entrant request for url {request.url}")
            return None

        # if isinstance(request.headers['User-Agent'], NoneType):
        #    raise ValueError("User-Agent must be specified.")

        cdx_api = WaybackMachineAvailabilityAPI(
            url=request.url,
            user_agent=str(request.headers['User-Agent']),
        )
        meta = cdx_api.newest()

        logger.debug(f"Fetched wayback info {meta}")
        logger.info(f"Resource {meta.archive_url} age {meta.timestamp()}")

        # will restart the request -- this function will receive the modified one and need to skip it.
        ret = request.replace(
            url=meta.archive_url,
            dont_filter=True,
        )
        ret.meta['wayback_request'] = True
        ret.meta['wayback_original_url'] = request.url
        return ret
