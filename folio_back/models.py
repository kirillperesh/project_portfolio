from django.db import models
from django.core.validators import URLValidator
from urllib.parse import urlparse, parse_qs
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.defaultfilters import slugify
from django.utils import timezone, dateformat


class Tile(models.Model):
    title = models.CharField(max_length=300)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True) #add deleted user
    post = models.TextField(max_length=1000)
    background_link = models.TextField(validators=[URLValidator()], max_length=2083)
    bg_is_img = models.BooleanField(default=True)
    time_created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    slug = models.SlugField(unique=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"'{self.title}' by {self.author}"

    def save(self, *args, **kwargs):
        if not self.pk:
            parsed_url = urlparse(self.background_link)
            yt_domains = ['googlevideo.com', 'gvt1.com', 'gvt2.com', 'gvt3.com', 'video.google.com', 'youtu.be', 'youtube-nocookie.com', 'youtube-ui.l.google.com', 'youtube.com', 'youtube.googleapis.com', 'youtubeeducation.com', 'youtubei.googleapis.com', 'yt3.ggpht.com', 'ytimg.com']
            is_yt_link = any(domain in parsed_url.netloc for domain in yt_domains)
            if is_yt_link:
                yt_id_search = parse_qs(parsed_url.query)['v']
                if yt_id_search:
                    yt_id = yt_id_search[0]
                    self.background_link = f"https://www.youtube.com/embed/{yt_id}?autoplay=1&mute=1"
                    self.bg_is_img = False

        formatted_date = dateformat.format(timezone.localtime(timezone.now()), 'H-i-s d-m-y')
        self.slug = slugify(f'{self.title[:100]}-{formatted_date}')
        super(Tile, self).save(*args, **kwargs)

