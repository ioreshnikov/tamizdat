{% if book.authors %}
  {% set author = book.authors[0] %}{% include "author.md" %}
{% endif %}
{% for author in book.authors[1:2] -%}
  , {% include "author.md" %}
{% endfor %}
{% if book.authors | length > 2 -%}
  _ и другие_
{%- endif %}
