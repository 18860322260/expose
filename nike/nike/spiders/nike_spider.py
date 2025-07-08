import scrapy
import json
from urllib.parse import urlencode
from jinja2 import Template
from nike.items import NikeProductItem


class NikeSpiderSpider(scrapy.Spider):
    name = "nike_spider"
    allowed_domains = ["nike.com.cn"]
    with open("template/nike.html", "r", encoding="utf-8") as f:
        template_str = f.read()
    jinja_template = Template(template_str)

    def start_requests(self):
        # 设置要抓取的页数（每页 anchor += 24）
        url = "https://api.nike.com.cn/cic/browse/v2"
        headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "if-none-match": "W/\"12032-X1HG6o/Cw8FMeLdVWzR/grfW/q8\"",
            "origin": "https://www.nike.com.cn",
            "priority": "u=1, i",
            "referer": "https://www.nike.com.cn/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }
        base_endpoint = "/product_feed/rollup_threads/v2?filter=marketplace(CN)&filter=language(zh-Hans)&filter=employeePrice(true)&consumerChannelId=d9a5bc42-4b9c-4976-858a-f159cf99c647&count=24"
        pages = 2  # 抓取前2页

        for i in range(pages):
            anchor = i * 24

            # 构造完整的 endpoint
            endpoint = f"{base_endpoint}&anchor={anchor}"

            # 构造 params
            params = {
                "queryid": "products",
                "anonymousId": "DSWXA781DF576263FA0FE3F79AAA9C05C1D0",
                "country": "cn",
                "endpoint": endpoint,
                "language": "zh-Hans",
                "localizedRangeStr": "{lowestPrice} — {highestPrice}"
            }

            # 将 params 转换为 query string 并附加到 URL 上
            full_url = f"{url}?{urlencode(params)}"

            yield scrapy.Request(
                url=full_url,
                method='GET',
                headers=headers,
                callback=self.parse_list,
                meta={'anchor': anchor},
                dont_filter=True
            )

    def create_list_items(self, response):
        json_data = response.json()
        products = json_data['data']['products']['products']
        items = []

        for product in products:
            item = NikeProductItem()
            url = product['url']
            item['title'] = product['title'] + product['subtitle']
            item['detail_url'] = url.replace("{countryLang}", "https://www.nike.com.cn")
            item['price'] = product['price']['currentPrice']
            items.append(item)

        return items

    def parse_list(self, response, **kwargs):
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "if-none-match": "\"7d3d9-VI6oSTySI0U5cFPGJSI+0bFXy9k\"",
            "priority": "u=0, i",
            "referer": "https://www.nike.com.cn/w/",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        }

        items = self.create_list_items(response)

        for item in items:
            yield scrapy.Request(
                url=item.get('detail_url'),
                method='GET',
                headers=headers,
                callback=self.parse_detail,
                meta={'item': item},
                dont_filter=True
            )

    def creat_detail_item(self, response, item):
        script_text = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        if script_text:
            data = json.loads(script_text.strip())
            pageProps = data["props"]["pageProps"]

            initialState = pageProps.get("initialState")

            if initialState and "Threads" in initialState and "products" in initialState["Threads"]:
                products = initialState["Threads"]["products"]
                product_list = list(products.values())

                item['color'] = [p.get('colorDescription', '') for p in product_list]
                item['size'] = [
                    [sku.get('localizedSize', '') for sku in p.get('skus', [])]
                    for p in product_list
                ]
                item['sku'] = [
                    [sku.get('skuId', '') for sku in p.get('skus', [])]
                    for p in product_list
                ]
                item['detail'] = [p.get('description', '') for p in product_list]
                item['images'] = [
                    p.get('firstImageUrl', '')
                    for p in product_list
                ]
            else:
                item['size'] = [s.get('localizedLabel', '') for s in
                                pageProps.get("selectedProduct", {}).get("sizes", [])]
                item['sku'] = [s.get('merchSkuId', '') for s in pageProps.get("selectedProduct", {}).get("sizes", [])]
                item['color'] = [i.get('colorDescription', '') for i in pageProps.get("colorwayImages", [])]
                item['detail'] = self.jinja_template.render(pageProps)
                item['images'] = [
                    img.get("properties", {}).get("squarish", {}).get("url", '')
                    for img in pageProps.get("selectedProduct", {}).get("contentImages", [])
                    if "properties" in img and "squarish" in img["properties"]
                ]
            return item

    def parse_detail(self, response, **kwargs):
        seed_item = response.meta['item']
        item = self.creat_detail_item(response, seed_item)
        yield item
