# llm/generator.py
# 接收输入（如帖子摘要、产品信息），选择合适的 Prompt 模板，
# 调用 client.py 生成推广评论或帖子草稿。

from typing import Optional, Dict, Any, List

# Assuming client and prompts are in the same directory or accessible
from .client import LLMClient
from .prompts import PromptTemplates

# You might want to get API key and model from a central config
# from ..config.settings import settings

class ContentGenerator:
    def __init__(self, llm_client: Optional[LLMClient] = None, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """
        Initializes the ContentGenerator.
        Args:
            llm_client (Optional[LLMClient]): An existing LLMClient instance.
                                             If None, a new one will be created.
            api_key (Optional[str]): API key for the LLM, used if llm_client is None.
            model_name (str): Model name for the LLM, used if llm_client is None.
        """
        if llm_client:
            self.llm_client = llm_client
        else:
            # In a real app, get api_key and model_name from settings
            # self.llm_client = LLMClient(api_key=settings.OPENAI_API_KEY, model_name=settings.LLM_MODEL_NAME)
            self.llm_client = LLMClient(api_key=api_key, model_name=model_name)
        
        self.prompt_templates = PromptTemplates()
        print("ContentGenerator initialized.")

    def generate_promotional_comment(
        self,
        post_summary: str,
        product_name: str,
        product_features: str,
        target_audience: str,
        tone: str = "enthusiastic and helpful",
        language: str = "Chinese",
        max_tokens: int = 100, # Comments are usually shorter
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generates a promotional comment using the LLM.
        """
        prompt = self.prompt_templates.generate_promotional_comment(
            post_summary=post_summary,
            product_name=product_name,
            product_features=product_features,
            target_audience=target_audience,
            tone=tone,
            language=language
        )
        
        system_message = f"You are a creative social media assistant writing a {tone} comment in {language}."
        
        print(f"\nGenerating promotional comment for product: {product_name}")
        # print(f"Using prompt:\n{prompt[:300]}...") # Print a snippet of the prompt for debugging

        generated_text = self.llm_client.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return generated_text

    def generate_post_draft(
        self,
        topic: str,
        product_name: str,
        core_sell_points: str,
        target_audience: str,
        keywords: List[str],
        post_style: str = "informative and engaging",
        platform: str = "a generic social media platform",
        language: str = "Chinese",
        max_tokens: int = 300, # Posts can be longer
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generates a social media post draft using the LLM.
        """
        prompt = self.prompt_templates.generate_post_draft(
            topic=topic,
            product_name=product_name,
            core_sell_points=core_sell_points,
            target_audience=target_audience,
            keywords=keywords,
            post_style=post_style,
            platform=platform,
            language=language
        )
        
        system_message = f"You are a skilled content writer drafting a {post_style} social media post in {language} for {platform}."
        
        print(f"\nGenerating post draft for topic: {topic}, product: {product_name}")
        # print(f"Using prompt:\n{prompt[:300]}...")

        generated_text = self.llm_client.generate_text(
            prompt=prompt,
            system_message=system_message,
            max_tokens=max_tokens,
            temperature=temperature
        )
        return generated_text

if __name__ == '__main__':
    print("Testing ContentGenerator...")
    # Ensure OPENAI_API_KEY is set in environment for this test to run, or pass it to ContentGenerator.
    # Example: generator = ContentGenerator(api_key="sk-your-key-here")
    try:
        content_gen = ContentGenerator() # Uses default LLMClient which tries to use OPENAI_API_KEY env var

        # Test comment generation
        print("\n--- Test 1: Generating Promotional Comment ---")
        comment = content_gen.generate_promotional_comment(
            post_summary="A user on Xiaohongshu posted about their new puppy and is looking for durable toy recommendations.",
            product_name="ChewGuard indestructible dog bone",
            product_features="Made from ultra-durable, non-toxic material, veterinarian approved, great for heavy chewers.",
            target_audience="Dog owners, especially those with puppies or strong chewers.",
            tone="friendly and empathetic",
            language="Simplified Chinese",
            max_tokens=150
        )
        if comment:
            print(f"\nGenerated Comment:\n{comment}")
        else:
            print("\nFailed to generate comment.")

        # Test post draft generation
        print("\n--- Test 2: Generating Post Draft ---")
        post_draft = content_gen.generate_post_draft(
            topic="Easy ways to incorporate more vegetables into your daily meals",
            product_name="VeggieBoost Smoothie Powder",
            core_sell_points="Contains 5 servings of organic vegetables, tasteless, mixes easily into any drink or food.",
            target_audience="Busy professionals, health-conscious individuals, families.",
            keywords=["healthy eating", "vegetables", "nutrition", "easy meals", "smoothie"],
            post_style="helpful and practical",
            platform="Instagram",
            language="English",
            max_tokens=250
        )
        if post_draft:
            print(f"\nGenerated Post Draft:\n{post_draft}")
        else:
            print("\nFailed to generate post draft.")

    except Exception as e:
        print(f"An error occurred during ContentGenerator test: {e}")
        print("Please ensure your OPENAI_API_KEY is set correctly or provide it to the ContentGenerator.")