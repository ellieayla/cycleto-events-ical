import scrapy

from typing import Iterator

import scrapy.http
from scrapy.selector import SelectorList, Selector
from parsel import Selector as ParselSelector

from ..items import Event
from w3lib.html import remove_tags
from datetime import datetime, timedelta


def remove_node(nodes_to_remove: list[Selector | ParselSelector] | SelectorList) -> None:
    for node_to_remove in nodes_to_remove:
        node_to_remove.root.getparent().remove(node_to_remove.root)


def remove_empty_nodes(selector_list: SelectorList) -> None:
    remove_node([_ for _ in selector_list if not remove_tags(_.extract()).strip()])


class EventsSpider(scrapy.Spider):
    name = 'events'
    allowed_domains = ['www.cycleto.ca', 'web.archive.org']
    start_urls = ['https://www.cycleto.ca/events']

    """
    async def start(self) -> AsyncIterator[Any]:
        # override default implementation of start() to pass meta{playwright=true}
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={"playwright": True},
                dont_filter=True,
            )
    """

    def parse(self, response: scrapy.http.Response) -> Iterator[Event]:
        # https://docs.scrapy.org/en/latest/topics/loaders.html#nested-loaders ?

        for e in response.css(".calendar-list li.calendar-day-events-event"):
            """
            yield scrapy.Request(
                response.urljoin(e),
                callback=self.parse_meeting_details,
                meta={"playwright": True},
            )
            """

            # instead of fetching details from the event page (which might not be fetchable),
            # just make a short summary from the information available in the events list here.
            summary = e.css(".calendar-day-events-event-headline::text").extract_first("").strip()
            start_time = datetime.fromisoformat(e.css("time").attrib['datetime'].strip())
            end_time = start_time + timedelta(hours=1)

            url_fragment: str = e.css("a::attr(href)").extract_first("")
            if response.meta.get('wayback_request'):
                event_url = url_fragment.split("/", maxsplit=3)[3]
            else:
                event_url = response.urljoin(url_fragment)

            yield Event(
                summary=summary,
                url=event_url,
                start_datetime=start_time,
                end_datetime=end_time,
                location=None,
                description=None,
            )
