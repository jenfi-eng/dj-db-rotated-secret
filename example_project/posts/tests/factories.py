import factory
from example_project.posts.models import Post

class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post  # Point to the Post model

    title = factory.Faker('sentence', nb_words=4)  # Generates a random title with 4 words
    content = factory.Faker('paragraph', nb_sentences=3)  # Generates random content with 3 sentences
