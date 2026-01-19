import scrapfly
from scrapfly import ScrapflyClient, ScrapeConfig, UpstreamHttpClientError
import os
client = ScrapflyClient(key=os.environ['SCRAPFLY_KEY'])

api_url = "https://web-scraping.dev/api/testimonials"
page_number = 1
result = client.scrape(ScrapeConfig(
    "https://web-scraping.dev/api/testimonials?page=1",
    headers={
        # this API requires these headers:
        "Referer": "https://web-scraping.dev/testimonials",
        "X-Secret-Token": "secret123",
    }
))
for testimonial in result.selector.css('.testimonial'):
    text = testimonial.css('.text::text').get()
    rating = len(testimonial.css('.rating>svg').getall())
    print(text)
    print(f'rating: {rating}/5 stars')