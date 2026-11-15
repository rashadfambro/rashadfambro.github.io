# Generators
Source for the generated pages. Edit these, then run from the repo root:

```
python3 scripts/generators/gen_pages.py        # products.html, industries/*.html, privacy.html, sitemap.xml
python3 scripts/generators/gen_prototypes.py   # prototypes/*.html (trial apps + Desk Suite)
```
Then follow TESTING.md (staging first, tests 100%, then promote). `products_data.py` holds the Product Guide content; `protos_more.py` holds nine of the fifteen tool apps.
