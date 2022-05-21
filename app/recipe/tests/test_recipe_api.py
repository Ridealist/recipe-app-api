from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def sample_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {"title": "Sample Recipe", "time_minutes": 10, "price": 5.00}
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeAPITests(TestCase):
    """Test unauthenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()

    def test_publicly_get_recipe_list_failed(self):
        """Test that authentication is required"""
        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):
    """Test authenticated recipe API access"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "test@test.com", "testpass1234"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipe_list(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            "other@test.com", "testpass4321"
        )
        default1 = {"title": "Corn Soup"}
        default2 = {"title": "Siroin Steak"}
        sample_recipe(user=self.user, **default1)
        sample_recipe(user=user2, **default2)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
        self.assertEqual(res.data.pop()["title"], "Corn Soup")

    # @classmethod
    # def setUpTestData(cls):
    #     cls.user = get_user_model().objects.create_user(
    #         "test@test.com", "testpass1234"
    #     )
    #     cls.ingredient1 = Ingredient.objects.create(
    #         name="Carrot",
    #         user=cls.user
    #     )
    #     cls.ingredient2 = Ingredient.objects.create(
    #         name="Potato",
    #         user=cls.user
    #     )
    #     cls.tag1 = Tag.objects.create(
    #         name="Meal",
    #         user=cls.user
    #     )
    #     cls.tag2 = Tag.objects.create(
    #         name="Snacks",
    #         user=cls.user
    #     )
