import re
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Ingredient:
    quantity: Optional[str]
    unit: Optional[str]
    name: str


@dataclass
class Recipe:
    name: str
    description: Optional[str]
    ingredients: List[Ingredient]
    instructions: List[str]
    url: str


class RecipeParser:
    """A tool for parsing recipes from URLs."""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_page(self, url: str) -> str:
        """Fetch the webpage content."""
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch recipe page: {str(e)}")

    def parse_recipe(self, url: str) -> Recipe:
        """Parse a recipe from a given URL."""
        html = self.fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')

        # Look for structured data first (Schema.org)
        schema_data = soup.find('script', type='application/ld+json')
        if schema_data:
            try:
                import json
                data = json.loads(schema_data.string)
                if isinstance(data, list):
                    data = data[0]
                if '@type' in data and data['@type'] in ['Recipe', 'recipe']:
                    return self._parse_schema_recipe(data, url)
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback to HTML parsing
        return self._parse_html_recipe(soup, url)

    def _parse_schema_recipe(self, data: dict, url: str) -> Recipe:
        """Parse recipe from Schema.org JSON-LD data."""
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        ingredients = [self._split_ingredient(i) for i in data.get('recipeIngredient', []) if self._valid_ingredient(i)]

        instructions = data.get('recipeInstructions', [])
        if isinstance(instructions, str):
            instructions = [instructions]
        elif isinstance(instructions, list):
            instructions = [
                i.get('text', i) if isinstance(i, dict) else i
                for i in instructions
            ]
        instructions = [i.strip() for i in instructions if i.strip()]

        return Recipe(name=name, description=description,
                      ingredients=ingredients, instructions=instructions,
                      url=url)

    def _parse_html_recipe(self, soup: BeautifulSoup, url: str) -> Recipe:
        """Parse recipe from HTML when structured data is not available."""
        name = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
        description = soup.find('meta', {'name': 'description'})['content'].strip() if soup.find('meta', {'name': 'description'}) else ''

        # Extract ingredients
        ingredients_section = soup.find(class_=re.compile(r'ingredient', re.I))
        ingredients = []
        if ingredients_section:
            for item in ingredients_section.find_all(['li', 'p']):
                ingredient = item.text.strip()
                if self._valid_ingredient(ingredient):
                    ingredients.append(self._split_ingredient(ingredient))

        # Extract instructions
        instructions_section = soup.find(class_=re.compile(r'instruction|direction|method', re.I))
        instructions = []
        if instructions_section:
            instructions = [item.text.strip() for item in instructions_section.find_all(['li', 'p'])]

        return Recipe(name=name, description=description,
                      ingredients=ingredients, instructions=instructions,
                      url=url)

    def _split_ingredient(self, ingredient: str) -> Ingredient:
        """Attempt to split an ingredient into quantity, unit, and name."""
        # Regular expression for ingredient parsing (you can refine it further)
        pattern = r'(?P<quantity>[\d/.,\s]*)(?P<unit>[a-zA-Z]*)\s(?P<name>.*)'
        match = re.match(pattern, ingredient)
        if match:
            quantity = match.group('quantity').strip() or None
            unit = match.group('unit').strip() or None
            name = match.group('name').strip()
            return Ingredient(quantity=quantity, unit=unit, name=name)
        return Ingredient(quantity=None, unit=None, name=ingredient)

    def _valid_ingredient(self, ingredient: str) -> bool:
        """Check if the ingredient is valid and not a serving size."""
        serving_keywords = ['serving', 'serves', 'yields']
        return not any(keyword in ingredient.lower() for keyword in serving_keywords)


def parse_recipe_url(url: str) -> Recipe:
    parser = RecipeParser()
    return parser.parse_recipe(url)
