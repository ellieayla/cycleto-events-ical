import scrapy

from typing import Generator, Iterable, Iterator

import scrapy.http
from scrapy.item import Item
from scrapy.loader import ItemLoader
from scrapy.selector import SelectorList, Selector
from parsel import Selector as ParselSelector

from ..items import Event
import icalendar
import datauri  # pragma: notype
import logging
from w3lib.html import remove_tags


def remove_node(nodes_to_remove: list[Selector | ParselSelector] | SelectorList) -> None:
    for node_to_remove in nodes_to_remove:
        node_to_remove.root.getparent().remove(node_to_remove.root)

def remove_empty_nodes(selector_list: SelectorList) -> None:
    targets = [_ for _ in selector_list if not remove_tags(_.extract()).strip()]
    remove_node([_ for _ in selector_list if not remove_tags(_.extract()).strip()])


class EventsSpider(scrapy.Spider):
    name = 'events'
    allowed_domains = ['www.cycleto.ca']
    start_urls = [
        'https://www.cycleto.ca/events'
    ]

    def parse(self, response: scrapy.http.Response) -> Iterator[scrapy.Request]:
        # https://docs.scrapy.org/en/latest/topics/loaders.html#nested-loaders ?

        for e in response.css(".calendar-list li.calendar-day-events-event a::attr(href)").getall():
            yield scrapy.Request(
                response.urljoin(e),
                callback=self.parse_meeting_details,
                meta={"playwright": True},
            )

    def parse_meeting_details(self, response: scrapy.http.Response) -> Iterable[Event]:

        ics_blob = response.xpath('//a[contains(@download, "event.ics")]/@href').get()
        a: datauri.datauri.ParsedDataURI = datauri.parse(ics_blob)
        base_calendar: icalendar.Component = icalendar.Calendar.from_ical(a.data)
        base_event = base_calendar.walk('vevent')[0]

        location = base_event.decoded("location").decode()
        start_time = base_event.decoded('dtstart')
        end_time = base_event.decoded('dtend')
        url = base_event.decoded('url')
        summary = base_event.decoded('summary').decode()

        if url != response.url:
            logging.warning("Url in event.ics does not match page url")

        content = response.css("main div.text-content")

        metadata = {}

        if content.css("ul li"):
            # there's a list in here. Extract metadata
            for _ in content.css("ul li"):
                row = remove_tags(_.extract()).strip()
                if ':' in row:
                    # looks like a key:value pair.
                    row_key, row_value = row.split(":",1)
                    if row_key in ('Date', 'Time', 'Location'):
                        continue
                    metadata[row_key] = row_value
            remove_node(content.css("ul li"))

        if content.css("p"):
            # there's a list in here. Extract metadata
            for p in content.css("p"):
                row = remove_tags(p.extract()).strip()
                if ':' in row:
                    # looks like a key:value pair.
                    row_key, row_value = row.split(":",1)
                    if row_key in ('Date', 'Time', 'Location'):
                        continue
                    if len(row_key) > 10:
                        # really long, probably a sentence
                        continue
                    metadata[row_key] = row_value.strip()
                    remove_node([p])

        # convert remaining list items into bullets
        if content.css("li"):
            for li in content.css("li"):
                li.root.text = "* " + li.root.text

        # we can't handle images so just remove them
        remove_node(content.css("img"))

        remove_empty_nodes(content)
        content = response.css("main div.text-content")
        
        left = response.css("main div.text-content").xpath("descendant::text()").getall()
        left = [_.strip() for _ in left]
        left = [_ for _ in left if _]

        description = "\n".join(left)
        
        if metadata:
            for k,v in metadata.items():
                description += f"\n* {k}: {v}"

        yield Event(
            summary = summary,
            url = response.url,

            start_datetime = start_time,
            end_datetime = end_time,

            location = location,
            description = description,
        )
