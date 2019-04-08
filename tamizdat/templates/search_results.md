{% for book in books %}
{% include "book_header.md" %}

/info{{book.book_id}}

{% endfor %}
