# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

# items.py
import scrapy

class NikeProductItem(scrapy.Item):
    title = scrapy.Field()
    detail_url = scrapy.Field()
    price = scrapy.Field()
    color = scrapy.Field()
    size = scrapy.Field()
    sku = scrapy.Field()
    detail = scrapy.Field()
    images = scrapy.Field()
