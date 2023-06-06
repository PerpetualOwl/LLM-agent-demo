import os
import openai
from bs4 import BeautifulSoup

openai.organization = "org-PRFFzhFRzU9mXJc0aWuYVfgg"
openai.api_key = os.getenv("OPENAI_API_KEY")

recursion = 0

memory = []
progress = ""
task_queue = []

def run_agent(question):
    # decision maker
    global recursion, progress, memory, task_queue

    if not memory:
        memory.append(f"Question posed: {question}")

    recursion += 1

    if recursion > 5:
        query = f'''You are Credit Analyst GPT. Your job is to help your boss understand the answer
                to whatever question is being asked. The question is: {question}. Here is your current progress
                from previous runs: {progress}
                Please answer the boss's question using as much of the progress from previous runs as possible.'''
        result = query_llm(query)

    query = f'''You are Credit Analyst GPT. Your job is to help your boss understand the answer
                to whatever question is being asked. The question is: {question}. Here is your current progress
                from previous runs: {progress}
                Your job is the direct the continued progress towards answering the boss's question, and you have the following options
                1. List up to 5 subtasks between html <li> </li> tags that need to be completed to advance towards the goal. These can include accessing data from
                BAM's credit database (sentiment and investment indicators towards tickers), internet searches which retrieve websites
                and their contents from Google, and price history API calls.
                2. If the progress seems sufficient to answer the initial question write the tag <complete> and craft an answer to the
                question in natural english that your boss will like.'''
    result = query_llm(query)
    if "<complete>" in result:
        return

    result = BeautifulSoup(result, 'html')
    for task in result.find_all("li"):
        task_queue.append(task)
        message = f"Added Task: {task}\n"
        memory.append(message)
        progress += message
        print(message)

    while task_queue:
        execute_task()

    run_agent(question)
    return


def execute_task(task):
    # parse what type of task we are asking for
    # have llm create query
    # execute query
    global recursion, progress, memory, task_queue

    task_queue.remove(task)

    query = f'''You are Credit Analyst GPT. Your job is to help your boss understand the answer
                to whatever question is being asked. {memory[0]}
                Another Credit Analyst GPT has already made a list of tasks to answer that question. Your task
                is {task}.
                In your response please write the type of task asked for and what query to use.
                If the task is a BAM database access, then start your response with <BAM> and then format
                the rest of the text as follows: TICKER; TYPE; DATE_START; DATE_END; the ticker is the stock ticker
                wanted, use commas to separate multiple tickers. the type is either SS for sentiment data, or EI for
                investment indicator signals. The dates are formatted MM/DD/YYYY.
                If the task is a web search, we will use Google. start your response with <GOOGLE> and then put the query
                after it. We will give you the contents of the first article result so format your query well.'''

    result = query_llm(query)
    if "<BAM>" in result:
        result = query_BAM(result.replace("<BAM>", ""))
    elif "<GOOGLE>" in result:
        result = query_GOOGLE(result.replace("<GOOGLE>", ""))
    else:
        return #don't know what to do here

    message = f"Completing Task: {task}; Result: {result}\n"
    memory.append(message)
    progress += message



def query_llm(query):
    # using chatgpt for simplicity
    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": query}])

    return chat_completion.choices[0].message.content

def query_BAM(query):
    query = query.split(";")
    type = "social_sentiment"
    if "SS" in query[1]:
        type = "social_sentiment"
    elif "EI" in query[1]:
        type = "early_indicator"
    tickers = query[0].split(",")

    pass

def query_GOOGLE(query):
    pass


if __name__ == "__main__":
    run_agent()