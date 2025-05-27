# llm/prompts.py
# 存储字符串形式的 Prompt 模板。
# 可以设计成函数或类，方便填充变量。

from typing import Dict, Any

class PromptTemplates:
    @staticmethod
    def generate_promotional_comment(
        post_summary: str,
        product_name: str,
        product_features: str,
        target_audience: str,
        tone: str = "enthusiastic and helpful",
        language: str = "Chinese"
    ) -> str:
        """
        Generates a prompt for creating a promotional comment.
        Args:
            post_summary (str): A summary of the post to comment on.
            product_name (str): The name of the product/service to promote.
            product_features (str): Key features or selling points of the product.
            target_audience (str): The intended audience for the product.
            tone (str): The desired tone of the comment (e.g., friendly, professional).
            language (str): The desired language of the comment.
        Returns:
            str: A formatted prompt string.
        """
        prompt = f"""
        You are a social media marketing assistant. Your task is to write a {tone} comment in {language} for a social media post.
        The comment should subtly promote '{product_name}'.

        Original Post Summary:
        """{post_summary}"""

        Product Information:
        - Product Name: {product_name}
        - Key Features: {product_features}
        - Target Audience: {target_audience}

        Instructions for the comment:
        1. Make the comment relevant to the original post's content.
        2. Naturally weave in how '{product_name}' could be beneficial or related, without sounding like a direct advertisement.
        3. Keep the comment concise and engaging.
        4. If possible, ask a question to encourage interaction.
        5. Do not use overly salesy language.
        6. The comment should be in {language}.

        Generate the comment now.
        """
        return prompt.strip()

    @staticmethod
    def generate_post_draft(
        topic: str,
        product_name: str,
        core_sell_points: str,
        target_audience: str,
        keywords: list[str],
        post_style: str = "informative and engaging",
        platform: str = "a generic social media platform",
        language: str = "Chinese"
    ) -> str:
        """
        Generates a prompt for creating a social media post draft.
        Args:
            topic (str): The main topic or theme of the post.
            product_name (str): The product/service to be featured.
            core_sell_points (str): The main advantages of the product.
            target_audience (str): Who the post is for.
            keywords (list[str]): Relevant keywords to include for SEO/discoverability.
            post_style (str): Desired style (e.g., humorous, educational).
            platform (str): The target social media platform (e.g., Xiaohongshu, Weibo).
            language (str): The desired language of the post.
        Returns:
            str: A formatted prompt string.
        """
        keyword_str = ", ".join(keywords)
        prompt = f"""
        You are a content creation assistant. Your task is to draft a social media post for {platform} in {language}.
        The post should be {post_style} and focus on the topic: '{topic}'.
        It should also subtly feature or relate to '{product_name}'.

        Product/Service Information:
        - Name: {product_name}
        - Core Selling Points: {core_sell_points}
        - Target Audience: {target_audience}

        Post Requirements:
        1. Address the topic: '{topic}'.
        2. Integrate '{product_name}' naturally, highlighting its benefits related to the topic.
        3. Include relevant keywords such as: {keyword_str}.
        4. The tone should be {post_style}.
        5. If applicable for {platform}, suggest relevant hashtags.
        6. The post should be written in {language}.
        7. Aim for a post length suitable for {platform}.

        Draft the social media post now.
        """
        return prompt.strip()

    # Add more prompt templates as needed
    # For example, a prompt for summarizing text, extracting information, etc.

if __name__ == '__main__':
    print("Testing PromptTemplates...")

    # Test promotional comment prompt
    comment_prompt = PromptTemplates.generate_promotional_comment(
        post_summary="A user is asking for recommendations for good budget-friendly travel cameras.",
        product_name="SnapLite Camera X1",
        product_features="Lightweight, 10x optical zoom, long battery life, affordable price.",
        target_audience="Budget-conscious travelers, photography beginners.",
        tone="friendly and helpful",
        language="English"
    )
    print("\n--- Promotional Comment Prompt ---")
    print(comment_prompt)

    # Test post draft prompt
    post_draft_prompt = PromptTemplates.generate_post_draft(
        topic="Tips for Staying Productive While Working From Home",
        product_name="FocusBooster App",
        core_sell_points="Pomodoro timer, task management, distraction blocking.",
        target_audience="Remote workers, freelancers, students.",
        keywords=["work from home", "productivity", "focus", "time management"],
        post_style="actionable and encouraging",
        platform="LinkedIn",
        language="English"
    )
    print("\n--- Post Draft Prompt ---")
    print(post_draft_prompt)

    # Example in Chinese
    comment_prompt_zh = PromptTemplates.generate_promotional_comment(
        post_summary="小红书用户分享了她的周末烘焙成果，看起来很美味，但她说面团发酵有点问题。",
        product_name="神奇酵母S2000",
        product_features="快速发酵，成功率高，适合新手，天然成分。",
        target_audience="烘焙爱好者，特别是新手。",
        tone="亲切且有帮助的",
        language="简体中文"
    )
    print("\n--- 推广评论模板 (中文) ---")
    print(comment_prompt_zh)