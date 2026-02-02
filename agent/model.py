from openai import OpenAI

class LLMModel:
    def __init__(self, url, key, model):
        self.client = OpenAI(
            api_key=key,
            base_url=url,
        )
        self.model = model

    def llm(self, hist):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=hist,
            temperature=0.9,
        )
        
        print(response.choices[0].message.content)

    def llm_stream(self, hist):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=hist,
            stream=True,
            temperature=0.9,
            #response_format={"type": "json_object"}, # 确保输出为 JSON
        )

        full_content = ""
        
        for chunk in response:
            delta_content = chunk.choices[0].delta.content
            
            if delta_content:
                print(delta_content, end="", flush=True)
                full_content += delta_content

        return full_content

def main():
    model = "gpt-oss-120b"
    url = "http://127.0.0.1:8080"
    key = "no_key"

    llm = LLMModel(url, key, model)
    messages = [
        {"role": "system", "content": "You're a helpful assistant."},
        {"role": "user", "content": "give me a random list of number, size < 10"}
    ]

    answer = llm.llm_stream(messages)

if __name__ == "__main__":
    main()
