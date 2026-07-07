---
layout: default
permalink: /news/
title: news
nav: true
nav_order: 3
---

<div class="post">

  <ul class="post-list">

    {% assign postlist = site.posts | concat: site.news | sort: "date" | reverse %}

    {% for post in postlist %}

    {% assign tags = post.tags | join: "" %}

    <li>
      {% if post.inline %}
        <p class="post-meta">{{ post.date | date: '%B %-d, %Y' }}</p>
        <p>{{ post.content | remove: '<p>' | remove: '</p>' | emojify }}</p>
      {% else %}
        <h3>
          <a class="post-title" href="{{ post.url | relative_url }}">{{ post.title }}</a>
        </h3>
        {% if post.excerpt %}
          <p>{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        {% endif %}
        <p class="post-meta">
          {{ post.date | date: '%B %-d, %Y' }}
          {% if tags != "" %}
            &nbsp; &middot; &nbsp;
            {% for tag in post.tags %}
              <a href="{{ tag | slugify | prepend: '/news/tag/' | relative_url }}">
                <i class="fa-solid fa-hashtag fa-sm"></i> {{ tag }}</a>
              {% unless forloop.last %}&nbsp;{% endunless %}
            {% endfor %}
          {% endif %}
        </p>
      {% endif %}
    </li>

    {% endfor %}

  </ul>

</div>
