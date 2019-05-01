К нам постучался новый пользователь

`#{{ user.user_id }}` {% if user.username %} @{{ user.username }}{% endif %}{% if user.first_name %} {{ user.first_name }}{% endif %}{% if user.last_name %} {{ user.last_name }}{% endif %}


/authorize{{ user.user_id }}
