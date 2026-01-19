import httpx
from parsel import Selector

api_url = "https://web-scraping.dev/api/testimonials"
# we'll use a simple loop to continue scraping next paging page until no results
page_number = 1
while True:
    print(f"scraping page {page_number}")
    response = httpx.get(
        api_url,
        params={"page": page_number},
        headers={
            # this API requires these headers:
            "Referer": "https://web-scraping.dev/testimonials",
            "X-Secret-Token": "secret123",
        }

    )

    # check if scrape is success:
    if response.status_code != 200:
        # last page reached
        if response.json()['detail']['error'] == 'invalid page':
            break
        # something else went wrong like missing header or wrong url?
        raise ValueError("API returned an error - something is missing?", response.json())

    # parse the HTML
    selector = Selector(response.text)
    for testimonial in selector.css('.testimonial'):
        text = testimonial.css('.text::text').get()
        rating = len(testimonial.css('.rating>svg').getall())
        print(text)
        print(f'rating: {rating}/5 stars')
        print('-------------')

    # next page!
    page_number += 1