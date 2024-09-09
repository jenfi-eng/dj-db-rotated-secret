from django.test import TestCase

from example_project.posts.models import Post
from example_project.posts.tests.factories import PostFactory


class TestBasic(TestCase):
    def test_add(self):
        assert 1 + 1 == 2


class TestPostCreate(TestCase):
    def test_post_create(self):
        post = PostFactory()
        assert post.title
        assert post.content
        assert Post.objects.count() == 1
