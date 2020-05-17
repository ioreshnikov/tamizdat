Здравствуйте, {% if user.first_name or user.last_name %}{% if user.first_name %}{{ user.first_name }}{% endif %}{% if user.first_name and user.last_name %} {% endif %}{% if user.last_name %}{{ user.last_name }}{% endif %}{% else %}{{ user.username }}{% endif %}!

✉️ {% if user.email %}Адрес вашей электронной почты `{{ user.email }}`.{% else %}Мы не знаем ваш почтовый адрес.{% endif %}


Чтобы поменять почтовый адрес или формат, пожалуйста, нажмите кнопку ниже.
