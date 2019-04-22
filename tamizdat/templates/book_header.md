*{{ book.title }}*
{% if book.subtitle -%}{{ book.subtitle }}{% endif %}
_{% include "authors.md" %}_{% if book.year or book.language.lower() != "ru" or book.series %}

Издание{% if book.year %} {{ book.year }} года{% endif %}{% if book.language.lower() != "ru" %} на {% include "language.md" %}{% endif %}{% if book.series %} из серии _{{book.series}}_{% endif %}
{% endif %}
