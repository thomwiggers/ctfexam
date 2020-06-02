# {{ entry.challenge.title }}

## Submission:

* **User:** {{ user.get_full_name }} ({{ user.student_number }})
{% if partner %}* **Found partner id**: {{ partner }} {% endif %}
* **Completed:** {% if entry.completion_time %}Yes, at {{ entry.completion_time }} {% else %} No. {% endif %}

## Customisation options

```json
{{ settings|safe }}
```

## Writeup

{{ entry.writeup|safe }}
