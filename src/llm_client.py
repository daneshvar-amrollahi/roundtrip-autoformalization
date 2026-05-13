"""
LLM client for OpenAI and Anthropic API calls.
Handles communication with LLM APIs for NL to SMT translation.
Supports both OpenAI (GPT) and Anthropic (Claude) as backends.
"""

from openai import OpenAI
from typing import Optional


class LLMClient:
    """Client for making stateless LLM API calls. Supports OpenAI and Anthropic."""
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.3, 
                 top_p: float = 1.0, debug: bool = False, provider: str = "openai"):
        """
        Initialize the LLM client.
        
        Args:
            api_key: API key (OpenAI or Anthropic depending on provider)
            model: Model name to use (default: gpt-4)
            temperature: Sampling temperature (0.0-2.0, default: 0.3)
            top_p: Nucleus sampling parameter (0.0-1.0, default: 1.0)
            debug: Enable debug logging of prompts and responses (default: False)
            provider: LLM provider - "openai" or "anthropic" (default: "openai")
        """
        self.provider = provider.lower()
        self.model = model
        self.temperature = temperature
        self.top_p = top_p
        self.debug = debug
        
        # max_retries=8 lets the SDK absorb transient 429/5xx with exponential backoff
        # so we can keep request_delay low without losing rules to rate limits.
        if self.provider == "openai":
            self.client = OpenAI(api_key=api_key, timeout=60.0, max_retries=8)
        elif self.provider == "anthropic":
            try:
                import anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required for Claude support. "
                    "Install it with: pip install anthropic"
                )
            self.client = anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=8)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}. Use 'openai' or 'anthropic'.")
    
    def _call_openai(self, messages: list, temperature: float, top_p: float) -> str:
        """Make an OpenAI API call."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            top_p=top_p
        )
        return response.choices[0].message.content.strip()
    
    def _call_anthropic(self, messages: list, temperature: float, top_p: float) -> str:
        """
        Make an Anthropic API call.
        
        Anthropic uses a different message format:
        - System prompt is a separate parameter (not in messages)
        - Messages only contain user/assistant roles
        """
        # Extract system prompt if present
        system_prompt = None
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)
        
        # If no user messages but we have messages, treat all as user
        if not user_messages:
            user_messages = [{"role": "user", "content": ""}]
        
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "temperature": temperature,
            "messages": user_messages,
        }
        # Note: Anthropic does not allow both temperature and top_p simultaneously.
        # We use temperature only (the primary sampling control).
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text.strip()
    
    def _call_llm(self, messages: list, temperature: Optional[float] = None, 
                  top_p: Optional[float] = None) -> str:
        """
        Unified LLM call dispatching to the correct provider.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Optional custom temperature
            top_p: Optional custom top_p
            
        Returns:
            Response text
        """
        temp = temperature if temperature is not None else self.temperature
        top_p_val = top_p if top_p is not None else self.top_p
        
        if self.provider == "openai":
            return self._call_openai(messages, temp, top_p_val)
        else:
            return self._call_anthropic(messages, temp, top_p_val)
    
    def translate_to_smt(self, nl_rule: str, system_prompt: str) -> str:
        """
        Translate a natural language rule to SMT.
        
        This is a stateless call - no conversation history is maintained.
        Each call is independent with no memory from previous calls.
        
        Args:
            nl_rule: Natural language rule text
            system_prompt: System prompt with instructions and schema
            
        Returns:
            SMT formalization as string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": nl_rule}
        ]
        
        if self.debug:
            print(f"\n{'='*60}")
            print(f"LLM API CALL [{self.provider.upper()}]")
            print(f"{'='*60}")
            print(f"SYSTEM PROMPT ({len(system_prompt)} chars):")
            print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
            print(f"\nUSER MESSAGE ({len(nl_rule)} chars):")
            print(nl_rule[:500] + "..." if len(nl_rule) > 500 else nl_rule)
            print(f"{'='*60}\n")
        
        content = self._call_llm(messages)
        
        if self.debug:
            print(f"\n{'='*60}")
            print("LLM RAW RESPONSE")
            print(f"{'='*60}")
            print(content)
            print(f"{'='*60}\n")
        
        return content
    
    def generate_with_prompt(self, prompt: str, temperature: Optional[float] = None, 
                            top_p: Optional[float] = None) -> str:
        """
        Generate response from a custom prompt.
        
        This is a stateless call with optional custom sampling parameters.
        Useful for one-off prompts like oracle repair.
        
        Args:
            prompt: Complete prompt text
            temperature: Optional custom temperature (uses default if None)
            top_p: Optional custom top_p (uses default if None)
            
        Returns:
            Generated response as string
        """
        messages = [
            {"role": "user", "content": prompt}
        ]
        
        if self.debug:
            print(f"\n{'='*60}")
            print(f"LLM API CALL (Custom Prompt) [{self.provider.upper()}]")
            print(f"{'='*60}")
            print(f"PROMPT ({len(prompt)} chars):")
            print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
            print(f"Temperature: {temperature}, Top-p: {top_p}")
            print(f"{'='*60}\n")
        
        content = self._call_llm(messages, temperature, top_p)
        
        if self.debug:
            print(f"\n{'='*60}")
            print("LLM RAW RESPONSE")
            print(f"{'='*60}")
            print(content)
            print(f"{'='*60}\n")
        
        return content
    
    def translate_to_nl(self, smt_formula: str, system_prompt: str) -> str:
        """
        Translate an SMT formula back to natural language.
        
        This is a stateless call - no conversation history is maintained.
        
        Args:
            smt_formula: SMT formula text
            system_prompt: System prompt with instructions and schema
            
        Returns:
            Natural language description as string
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": smt_formula}
        ]
        
        if self.debug:
            print(f"\n{'='*60}")
            print(f"LLM API CALL (SMT→NL) [{self.provider.upper()}]")
            print(f"{'='*60}")
            print(f"SYSTEM PROMPT ({len(system_prompt)} chars):")
            print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
            print(f"\nUSER MESSAGE ({len(smt_formula)} chars):")
            print(smt_formula[:500] + "..." if len(smt_formula) > 500 else smt_formula)
            print(f"{'='*60}\n")
        
        content = self._call_llm(messages)
        
        if self.debug:
            print(f"\n{'='*60}")
            print("LLM RAW RESPONSE (SMT→NL)")
            print(f"{'='*60}")
            print(content)
            print(f"{'='*60}\n")
        
        return content
    