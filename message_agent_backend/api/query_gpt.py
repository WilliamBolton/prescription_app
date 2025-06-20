from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")

def query_gpt4(messages, model='gpt-4o-2024-05-13', temperature=0):
    # Initialize the OpenAI API client
    
    # Create client
    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        #max_tokens=6000, # Max is 4096
        messages=messages,
    )

    return completion

'''
model="gpt-4o-2024-05-13",

messages=[
    {"role": "system", "content": system},
    {"role": "user", "content": combined_input}
]
)
'''

def query_llm_assistant(message, assistant_id):
    # Initialize the OpenAI API client
    client = OpenAI(api_key=api_key)
    thread = client.beta.threads.create()
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
        )
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id,
        #instructions="Please address the user as Jane Doe. The user has a premium account."
        )
    if run.status == 'completed': 
        output = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        #print(output)
        return output
    else:
        print(run.status)