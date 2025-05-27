# llm/client.py
# 封装对大语言模型 API 的调用。
# 例如，如果使用 OpenAI，这里会有与 OpenAI API 交互的类或函数。

from openai import OpenAI # Assuming use of the official openai package
from typing import Optional, List, Dict, Any

# Assuming settings are configured and accessible
# from ..config.settings import settings # If client.py is in social_automator/llm/
# For now, let's assume direct access or placeholder for API key

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """
        Initializes the LLM client.
        Args:
            api_key (Optional[str]): The API key for the LLM service. 
                                     If None, it might try to use environment variables 
                                     (e.g., OPENAI_API_KEY for OpenAI).
            model_name (str): The name of the model to use (e.g., "gpt-3.5-turbo").
        """
        # In a real app, you'd get the API key from settings or environment variables
        # from social_automator.config.settings import settings
        # self.api_key = api_key or settings.OPENAI_API_KEY
        # self.model_name = model_name or settings.LLM_MODEL_NAME
        
        # For this example, let's make api_key mandatory if not using env var directly by OpenAI lib
        if not api_key:
            # The OpenAI library by default checks for OPENAI_API_KEY env var
            pass # Or raise ValueError("API key must be provided or set as OPENAI_API_KEY environment variable.")

        self.client = OpenAI(api_key=api_key) # api_key can be None, OpenAI lib handles it
        self.model_name = model_name
        print(f"LLM Client initialized for model: {self.model_name}")

    def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: int = 150,
        temperature: float = 0.7,
        **kwargs: Any
    ) -> Optional[str]:
        """
        Generates text using the configured LLM.

        Args:
            prompt (str): The main user prompt/instruction.
            system_message (Optional[str]): An optional system-level instruction to guide the model's behavior.
            max_tokens (int): The maximum number of tokens to generate.
            temperature (float): Controls randomness (0.0 to 2.0). Lower is more deterministic.
            **kwargs: Additional parameters to pass to the LLM API.

        Returns:
            Optional[str]: The generated text, or None if an error occurs.
        """
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            # Accessing the response content correctly for openai >v1.0
            if response.choices and len(response.choices) > 0:
                # Check if the choice has a message and content
                choice = response.choices[0]
                if choice.message and choice.message.content:
                    return choice.message.content.strip()
                else:
                    print(f"LLM API response choice does not contain expected message content: {choice}")
                    return None
            else:
                print(f"LLM API response does not contain choices: {response}")
                return None
        except Exception as e:
            print(f"Error calling LLM API: {e}")
            return None

if __name__ == '__main__':
    print("Testing LLMClient...")
    # To run this test, you need to have OPENAI_API_KEY set in your environment
    # or pass it directly to LLMClient.
    # Example: client = LLMClient(api_key="sk-your-key-here")
    try:
        # Attempt to initialize client (will use OPENAI_API_KEY env var if available)
        llm_client = LLMClient(model_name="gpt-3.5-turbo") 
        
        # A simple test prompt
        test_prompt = "Translate the following English text to French: 'Hello, world!'"
        system_msg = "You are a helpful translation assistant."
        
        print(f"\nSending prompt: '{test_prompt}' with system message: '{system_msg}'")
        generated_content = llm_client.generate_text(test_prompt, system_message=system_msg, max_tokens=50)
        
        if generated_content:
            print(f"\nLLM Generated Content:\n{generated_content}")
        else:
            print("\nFailed to generate content from LLM.")
            print("Please ensure your OPENAI_API_KEY is set correctly in your environment variables or passed to the client.")

    except Exception as e:
        print(f"An error occurred during LLMClient test: {e}")
        print("This might be due to missing API key or network issues.")

    # Example with a different model (if you have access)
    # try:
    #     llm_client_gpt4 = LLMClient(model_name="gpt-4") # Replace with a model you have access to
    #     test_prompt_2 = "What is the capital of France?"
    #     print(f"\nSending prompt to {llm_client_gpt4.model_name}: '{test_prompt_2}'")
    #     generated_content_2 = llm_client_gpt4.generate_text(test_prompt_2, max_tokens=20)
    #     if generated_content_2:
    #         print(f"\nLLM ({llm_client_gpt4.model_name}) Generated Content:\n{generated_content_2}")
    #     else:
    #         print(f"\nFailed to generate content from {llm_client_gpt4.model_name}.")
    # except Exception as e:
    #     print(f"An error occurred with {llm_client_gpt4.model_name} test: {e}")