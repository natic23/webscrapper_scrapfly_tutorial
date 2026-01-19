Above we're reimplementing what we've observed in our developer tools. We're making requests to /api/testimonials endpoint with URL parameter page for paging number and secret authentications headers we found in the inspector. Then, we parse the HTML results using the usual HTML parsing tools.

This example illustrates how a backend API is reverse engineered using chrome devtools Network Inspector and it's a very common web scraping pattern.

### Finding Keys and Tokens
When it comes to hidden API scraping replicating headers and the values we see in the devtools is very important to access hidden APIs successfully.

In our scraper example we just hard-coded the required X-Secret-Token: secret123 headers but what if this value was dynamic and changed often? Our scrapers need to know how to retrieve or generate this token to continue scraping.

### Finding Values in HTML
By far the most common scenario is to store the values used in the backend API in the corresponding HTML body. In our /testimonials example, we can open up page source or Elements devtools and ctrl+f for known value - secret123:

------

I’ll use **https://quotes.toscrape.com** and mirror your **Scrapfly** style so every variable has a clear purpose.

---

## 1. Understand what we’re scraping

Open `https://quotes.toscrape.com` in your browser.

Each quote block looks like:

```html
<div class="quote">
    <span class="text">“The world as we have created it...”</span>
    <span>by <small class="author">Albert Einstein</small></span>
    <div class="tags">
        <a class="tag">change</a>
        <a class="tag">deep-thoughts</a>
    </div>
</div>

```

So for each quote we want:

- **Text** → `.text`
- **Author** → `.author`
- **Tags** → `.tag`

And each quote container is `.quote`.

---

## 2. Decide the CSS selectors

We’ll use these:

- **All quotes on page:**
    
    ```css
    .quote
    
    ```
    
- **Quote text:**
    
    ```css
    .text::text
    
    ```
    
- **Author:**
    
    ```css
    .author::text
    
    ```
    
- **Tags:**
    
    ```css
    .tags .tag::text
    
    ```
    

We’ll plug these into `result.selector.css(...)` later.

---

## 3. Look at pagination

At the bottom of the page you’ll see:

```html
<li class="next">
    <a href="/page/2/">Next <span aria-hidden="true">→</span></a>
</li>

```

URLs are:

- Page 1: `https://quotes.toscrape.com/`
- Page 2: `https://quotes.toscrape.com/page/2/`
- Page 3: `https://quotes.toscrape.com/page/3/`
- …

We can either:

- Increment a page number and build URLs, or
- Follow the “Next” link until it disappears.

I’ll show the **“follow Next link”** approach—it’s more general.

---

## 4. Full Scrapfly script with explanation

Here’s a complete script, then I’ll annotate every variable:

```python
import os
from scrapfly import ScrapflyClient, ScrapeConfig, UpstreamHttpClientError

# 1. Create the Scrapfly client using your API key
client = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])

# 2. Start from the first page
base_url = "https://quotes.toscrape.com"
current_url = base_url  # we'll update this as we follow "Next" links

while current_url:
    print(f"Scraping: {current_url}")

    try:
        # 3. Configure and perform the scrape
        result = client.scrape(ScrapeConfig(
            url=current_url,
            # quotes.toscrape doesn't require special headers, but this is where they'd go
            headers={
                "Referer": base_url,
            }
        ))
    except UpstreamHttpClientError as e:
        print(f"Request failed: {e}")
        break

    # 4. Loop over each quote block
    for quote in result.selector.css(".quote"):
        text = quote.css(".text::text").get()
        author = quote.css(".author::text").get()
        tags = quote.css(".tags .tag::text").getall()

        print("—" * 40)
        print(f"Quote : {text}")
        print(f"Author: {author}")
        print(f"Tags  : {', '.join(tags)}")

    # 5. Find the "Next" page link
    next_link = result.selector.css("li.next a::attr(href)").get()
    if next_link:
        # build absolute URL from relative href like "/page/2/"
        if next_link.startswith("/"):
            current_url = base_url.rstrip("/") + next_link
        else:
            current_url = base_url.rstrip("/") + "/" + next_link.lstrip("/")
    else:
        # no more pages
        current_url = None

print("Done.")

```

---

## 5. Every variable and object, explained

### Scrapfly setup

- **`client`**
    
    ```python
    client = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])
    
    ```
    
    **What it is:**
    
    A Scrapfly client object—your connection to the Scrapfly API.
    
    **Why it exists:**
    
    You use this to send all scraping requests. The `key` is your API key, read from an environment variable for safety.
    

---

### URL variables

- **`base_url`**
    
    ```python
    base_url = "https://quotes.toscrape.com"
    
    ```
    
    **What it is:**
    
    The root URL of the site. Used as a reference for building absolute URLs and headers.
    
- **`current_url`**
    
    ```python
    current_url = base_url
    
    ```
    
    **What it is:**
    
    The page you’re currently scraping.
    
    **How it changes:**
    
    - Starts as the homepage
    - After each page, updated to the “Next” page URL
    - Set to `None` when there’s no next page → loop ends

---

### Scrape configuration and result

- **`ScrapeConfig(...)`**
    
    ```python
    ScrapeConfig(
        url=current_url,
        headers={
            "Referer": base_url,
        }
    )
    
    ```
    
    **What it is:**
    
    A configuration object telling Scrapfly **what** to fetch and **how**.
    
    **Key fields here:**
    
    - `url` → the page to scrape (changes each loop)
    - `headers` → optional HTTP headers (site‑specific; here just a simple Referer)
- **`result`**
    
    ```python
    result = client.scrape(ScrapeConfig(...))
    
    ```
    
    **What it is:**
    
    The response from Scrapfly. It contains:
    
    - Raw HTML
    - A parsed selector interface (`result.selector`) for CSS/XPath queries

---

### Selector and extraction variables

Inside the loop:

```python
for quote in result.selector.css(".quote"):
    text = quote.css(".text::text").get()
    author = quote.css(".author::text").get()
    tags = quote.css(".tags .tag::text").getall()

```

- **`result.selector`**
    
    A helper object that lets you run CSS selectors on the HTML.
    
- **`result.selector.css(".quote")`**
    
    **What it returns:**
    
    A list‑like collection of elements, each representing:
    
    ```html
    <div class="quote"> ... </div>
    
    ```
    
- **`quote`**
    
    Each individual `.quote` block in the page.
    
- **`text`**
    
    ```python
    text = quote.css(".text::text").get()
    
    ```
    
    **What it is:**
    
    The quote text, e.g.
    
    `“The world as we have created it...”`
    
    - `.css(".text::text")` → select the text node inside `.text`
    - `.get()` → return the first match (or `None`)
- **`author`**
    
    ```python
    author = quote.css(".author::text").get()
    
    ```
    
    **What it is:**
    
    The author name, e.g. `"Albert Einstein"`.
    
- **`tags`**
    
    ```python
    tags = quote.css(".tags .tag::text").getall()
    
    ```
    
    **What it is:**
    
    A list of all tags for that quote, e.g.
    
    `["change", "deep-thoughts", "thinking"]`.
    
    - `.getall()` → return **all** matches as a list.

---

### Pagination variables

```python
next_link = result.selector.css("li.next a::attr(href)").get()

```

- **`next_link`**
    
    **What it is:**
    
    The relative URL of the next page, e.g. `"/page/2/"`, or `None` if there is no next page.
    
    - `li.next a` → the `<a>` inside `<li class="next">`
    - `::attr(href)` → get the `href` attribute
    - `.get()` → first match or `None`

Then:

```python
if next_link:
    if next_link.startswith("/"):
        current_url = base_url.rstrip("/") + next_link
    else:
        current_url = base_url.rstrip("/") + "/" + next_link.lstrip("/")
else:
    current_url = None

```

- **Purpose:**
    
    Turn a relative URL like `"/page/2/"` into a full URL like
    
    `"https://quotes.toscrape.com/page/2/"`.
    
- **`current_url = None`**
    
    This is the signal to stop the `while current_url:` loop.
    

---

### Error handling

```python
except UpstreamHttpClientError as e:
    print(f"Request failed: {e}")
    break

```

- **`UpstreamHttpClientError`**
    
    An exception raised when the upstream site (quotes.toscrape.com) returns an error (e.g. 500, 403, etc.).
    
- **Why it’s here:**
    
    To avoid your script crashing silently and to stop the loop if something goes wrong.
    

---

## 6. How this maps to your original tutorial snippet

From your first code:

- `ScrapflyClient(...)` → same idea
- `ScrapeConfig(...)` → same, but URL and headers are site‑specific
- `result.selector.css('.testimonial')` → now `result.selector.css('.quote')`
- `testimonial.css('.text::text')` → now `quote.css('.text::text')`
- `rating = len(testimonial.css('.rating>svg').getall())` → now `tags = quote.css('.tags .tag::text').getall()`

So the **Scrapfly pattern is identical**—only:

- URL
- headers
- CSS selectors
- pagination logic

are different.

---

If you’d like, next step could be:

you paste this script, run it, and then we tweak it together—e.g. saving to JSON/CSV, or switching to XPath so you see the parallel.