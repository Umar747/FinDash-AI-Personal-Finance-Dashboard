from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_react_agent, load_tools
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from agent_tools import tools

class ToolCallLogger(BaseCallbackHandler):
    def on_tool_start(self, serialized: dict, input_str: str, **kwargs) -> None:
        """Runs when a tool starts running."""
        print("\n--- AGENT TOOL CALL ---")
        print(f"Tool Name: {serialized.get('name')}")
        print(f"Arguments: {input_str}")
        print("-----------------------\n")

# Initialise the handler
tool_logger = ToolCallLogger()

# This template is optimized for Llama 3.1. 
# It uses a strict structure to prevent the model from repeating the question or hallucinating its own observations.
template = """You are a Personal Finance Assistant. Answer the user's question by using the tools provided.
DO NOT repeat the original question. DO NOT hallucinate observations. 
If you have the data from a tool, go straight to the Final Answer.
You have access to the following tools:

{tools}

If the user wants to add a transaction but forgets details:
1. If the amount or description is missing, ask the user for them.
2. If the account_id is missing, assume it is 1 (HSBC Current Account) but mention this to the user.
3. If the date is missing, use the current date.

When calculating sums, totals, or means:
1. List the numbers you found from the database.
2. Pass these numbers to the 'Calculator' tool.
3. WAIT for the Observation. 
4. DO NOT attempt to do the math yourself in the Thought block.
5. Use ONLY the result from the Observation in your Final Answer.

Format to follow:
Thought: your reasoning on what to do.
Action: the action to take (one of [{tool_names}])
Action Input: the input to the action
Observation: the result of the action (this will be provided to you)
Thought: I now have the final answer.
Final Answer: the final response to the user.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# Initialise the local Llama model using Ollama
llm = ChatOllama(model="llama3.1:8b", temperature=0)

math_tool = load_tools(["llm-math"], llm=llm)
tools = tools + math_tool

# Bind STOP sequences. 
# This is the most important part for stopping loops as it prevents the LLM from writing the "Observation:" text itself.
llm_with_stop = llm.bind(stop=["Observation:", "Observation: ", "\nObservation:"])

# Construct the ReAct agent using the LLM with the stop sequence
agent = create_react_agent(llm_with_stop, tools, prompt)

# Create the executor
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=5,
    early_stopping_method="force"
)

def ask_finance_agent(query: str):
    """
    Main entry point for the Flask server to interact with the AI Agent.
    """
    try:
        response = agent_executor.invoke(
            {"input": query}, 
            config={"callbacks": [tool_logger]}
        )
        return response["output"]
    except Exception as e:
        return f"I encountered an error while processing your request: {str(e)}"