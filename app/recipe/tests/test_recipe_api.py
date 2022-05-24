import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPES_URL = reverse("recipe:recipe-list")


def image_upload_ulr(recipe_id):
    """Return URL for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def detail_url(recipe_id):
    """Return recipe detail URL"""
    return reverse("recipe:recipe-detail", kwargs={"pk": recipe_id})
    # return RECIPES_URL + f"/{recipe_id}/" -> raw string보다 함수 사용!


def sample_tag(user, name="Main course"):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Cinnamon"):
    """Create and return a sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


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
            "testuser@recipe.com", "testpass1234"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        # res = self.client.post(
        #     "/api/user/token/",
        #     data={"email": "test@test.com", "password": "testpass1234"},
        # )
        # self.token = res.data["token"]
        # print(self.token)
        # self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token}")
        # self.client.login(email="test@test.com", password="testpass1234")

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

    def test_view_recipe_detail(self):
        """Test viewing a recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Test creating recipe"""
        payload = {
            "title": "Chocolate cheesecake",
            "time_minutes": 15,
            "price": 5.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
            # getattr : python built-in func, 변수를 넘겨줘서 어떤 object의
            #           attribute를 가져올 수 있음

    def test_create_recipe_with_tags(self):
        """Test creating a recipe with tags"""
        tag1 = sample_tag(user=self.user, name="Vegan")
        tag2 = sample_tag(user=self.user, name="Dessert")
        payload = {
            "title": "Avocado lime cheesecake",
            "tags": [tag1.id, tag2.id],
            "time_minutes": 60,
            "price": 20.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        # M2M field에서 연관된 모든 object 가져오기
        tags = recipe.tags.all()
        self.assertTrue(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag1, tags)

    def test_create_recipe_ingredients(self):
        """Test creating a recipe with ingredients"""
        ingredient1 = sample_ingredient(user=self.user, name="Prawns")
        ingredient2 = sample_ingredient(user=self.user, name="Ginger")
        payload = {
            "title": "Thai prawn red curry",
            "ingredients": [ingredient1.id, ingredient2.id],
            "time_minutes": 20,
            "price": 7.00,
        }
        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """Test update a recipe with patch method"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name="Curry")
        payload = {"title": "Chicken tikka", "tags": [new_tag.id]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # recipe = Recipe.objects.get(id=res.data["id"]) -> 불필요!
        # 모델 인스턴스를 만들고 변화가 생겼을 경우 해당 인스턴스에는 변화 반영 X
        # refresh DB를 해줘야 데이터베이스 value 변경사항이 instance에 반영된다.
        recipe.refresh_from_db()
        tags = recipe.tags.all()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_updata_recipe(self):
        """Test updating a recipe with put"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        # PUT method는 전체 update를 하므로 없는 field 값은 제외 시킴
        # 따라서 tags fields는 blank 값으로 초기화됨
        payload = {
            "title": "Spagetti carbonara",
            "time_minutes": 25,
            "price": 5.00,
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))
        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            "user@recipe.com", "testpass1234"
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """Test uploading an image to recipe"""
        url = image_upload_ulr(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading an invalid image"""
        url = image_upload_ulr(self.recipe.id)
        res = self.client.post(url, {"image": "notimage"}, format="multipart")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

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
