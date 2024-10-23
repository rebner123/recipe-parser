import requests
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Recipe:
    name: str
    description: Optional[str]
    ingredients: List[str]
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
        
        ingredients = data.get('recipeIngredient', [])
        if isinstance(ingredients, str):
            ingredients = [ingredients]
        ingredients = [i.strip() for i in ingredients if i.strip()]

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
        # Try to find recipe name
        name = ''
        name_candidates = [
            soup.find('h1'),
            soup.find('title'),
            soup.find(class_=re.compile(r'recipe.*title|title.*recipe', re.I))
        ]
        for candidate in name_candidates:
            if candidate and candidate.text.strip():
                name = candidate.text.strip()
                break

        # Try to find description
        description = ''
        desc_candidates = [
            soup.find(class_=re.compile(r'recipe.*description|description', re.I)),
            soup.find('meta', {'name': 'description'})
        ]
        for candidate in desc_candidates:
            if candidate:
                text = candidate.get('content', candidate.text).strip()
                if text:
                    description = text
                    break

        # Try to find ingredients
        ingredients = []
        ingredients_section = soup.find(
            ['ul', 'div'], 
            class_=re.compile(r'ingredient', re.I)
        )
        if ingredients_section:
            ingredients = [
                item.text.strip() 
                for item in ingredients_section.find_all(['li', 'p']) 
                if item.text.strip()
            ]

        # Try to find instructions
        instructions = []
        instructions_section = soup.find(
            ['ol', 'div'], 
            class_=re.compile(r'instruction|direction|method', re.I)
        )
        if instructions_section:
            instructions = [
                item.text.strip() 
                for item in instructions_section.find_all(['li', 'p']) 
                if item.text.strip()
            ]

        return Recipe(name=name, description=description, 
                     ingredients=ingredients, instructions=instructions, 
                     url=url)

def parse_recipe_url(url: str) -> Recipe:
    """
    Convenience function to parse a recipe from a URL.
    
    Args:
        url (str): The URL of the recipe to parse
        
    Returns:
        Recipe: A Recipe object containing the parsed data
        
    Example:
        recipe = parse_recipe_url('https://example.com/recipe')
        print(f"Recipe: {recipe.name}")
        print("\nIngredients:")
        for ingredient in recipe.ingredients:
            print(f"- {ingredient}")
    """
    parser = RecipeParser()
    return parser.parse_recipe(url)


if __name__ == "__main__":
    # Replace with an actual recipe URL
    url = "https://www.allrecipes.com/recipe/24074/alysias-basic-meat-lasagna/"
    recipe = parse_recipe_url(url)

    # Print out the parsed recipe
    print(f"Recipe: {recipe.name}")
    print(f"Description: {recipe.description}")
    print("\nIngredients:")
    for ingredient in recipe.ingredients:
        print(f"- {ingredient}")
    
    print("\nInstructions:")
    for instruction in recipe.instructions:
        print(f"- {instruction}")