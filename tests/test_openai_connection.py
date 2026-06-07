import os
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def main():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": "Say API connection successful."
            }
        ],
        temperature=0,
    )

    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()