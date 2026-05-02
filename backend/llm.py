import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq



load_dotenv()

def get_llm():
  """
   Returns the Groq LLM instance.
   Centralised here so every file imports from one place.
  """
  return ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key= os.getenv("GROQ_API_KEY"),
    temperature=0,   #  0 = deterministic, better for tool use
    max_tokens=2048, #  Max number of tokens to generate.

  )

if __name__ == "__main__":
    llm =get_llm()
    response= llm.invoke("Say hello as an HR assistant in one sentence.")
    print(response.content)