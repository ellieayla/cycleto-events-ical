# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html


from scrapy import Item, Field



"""
BEGIN:VCALENDAR
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
URL:https://www.cycleto.ca/coldest_day_2025
DTSTART:20250301T153000Z
DTEND:20250301T183000Z

SUMMARY:Coldest Day of the Year Ride 2025 - Cycle Toronto
LOCATION:
END:VEVENT
END:VCALENDAR


"""
class Event(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    summary = Field()
    url = Field()

    start_datetime = Field()
    end_datetime = Field()

    location = Field()

    description = Field()

    def __repr__(self):
        return f"{self.start_datetime}: {self.url}: {self.summary}"
