
from typing import Any
from io import BufferedWriter

from scrapy.exporters import BaseItemExporter


import icalendar
from uuid import UUID, uuid5

from .items import Event

ns = UUID('df750e3c-e8aa-11ef-aa47-6e2c6d516a99')


class ICalItemExporter(BaseItemExporter):
    # similar to the XML exporter
    def __init__(self, file: BufferedWriter, **kwargs: Any) -> None:
        super().__init__(dont_fail=True, **kwargs)
        self.file = file  # already-open file handle

        self.cal = icalendar.Calendar()
        self._kwargs.setdefault('ensure_ascii', not self.encoding)

    def start_exporting(self) -> None:
        self.cal.add('prodid', '-//CycleTo.ca//verselogic.net//')
        self.cal.add('version', '2.0')
        self.cal.add('method', 'PUBLISH')

    def export_item(self, item: Event) -> None:
        """
        summary = Field()
        url = Field()

        start_datetime = Field()
        end_datetime = Field()

        location = Field()

        description = Field()
        """
        e = icalendar.Event()

        e.add("summary", icalendar.vText(item['summary']))
        e.add('uid', icalendar.vText(str(uuid5(ns, item['url']))))
        e.add('url', icalendar.vText(item['url']))

        e.add("dtstart", icalendar.vDatetime(item['start_datetime']))
        e.add("dtend", icalendar.vDatetime(item['end_datetime']))

        if item['location']:
            e.add("location", icalendar.vText(item['location']))

        if item['description']:
            e.add("description", icalendar.vText(item['description']))

        # print(item['start_datetime'], type(item['start_datetime']), dir(item['start_datetime']))
        self.cal.add_component(e)


    def finish_exporting(self) -> None:
        self.cal.add_missing_timezones()
        self.cal.subcomponents = sorted(self.cal.subcomponents, key=lambda e: e.get("UID"))  # stable ordering; sort top-level subcomponents by UID
        self.file.write(self.cal.to_ical(sorted=True))  # stable ordering; sort properties
