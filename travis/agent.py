import tiktoken
import os
from dotenv import load_dotenv
from langchain.agents import agent
from langchain_core.messages import get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END, START
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langfuse import Langfuse
from langchain.llms import BaseLLM
from langfuse.decorators import observe
from travis.tools import save_recall_memory, search_recall_memories, search

load_dotenv()
from travis.utils import State, prompt, pretty_print_stream_chunk

langfuse = Langfuse(
    host=os.getenv("LANGFUSE_HOST"),
)


class LongTermMemoryAgent:
    """LongTermMemoryAgent"""

    def __init__(self,
                 model_name: str,
                 ):
        self.graph = None
        self.model = self.get_llm(model=model_name)
        self.tokenizer = tiktoken.encoding_for_model(model_name)
        self.model_with_tools = self._bind_tools()

    def _bind_tools(self):
        """Bind tools to the model."""
        self.tools = [save_recall_memory, search_recall_memories, search]
        return self.model.bind_tools(
            self.tools
        )
    
    def get_llm(self, model) -> BaseLLM:
        """
        Get the language model for the agent.
        Args:
            model: if groq use groq-modelname, openai use modelname, ollama if ollama-modelname

        Returns:
            BaseLLM: Language model for the agent.
        """
        if model[:3] == "gpt":
            return ChatOpenAI(model=model, streaming=True)
        if model[:4] == "groq":
            return ChatGroq(model=model[5:], streaming=True)
        if model[:6] == "ollama":
            return ChatOllama(model=model[7:], streaming=True)

    @observe()
    def agent(self, state: State) -> State:
        """Process the current state and generate a response using the LLM.

        Args:
            state (schemas.State): The current state of the conversation.

        Returns:
            schemas.State: The updated state with the agent's response.
        """
        bound = prompt | self.model_with_tools
        recall_str = (
                "<recall_memory>\n" + "\n".join(state["recall_memories"]) + "\n</recall_memory>"
        )
        prediction = bound.invoke(
            {
                "messages": state["messages"],
                "recall_memories": recall_str,
            }
        )
        return dict(messages=[prediction])

    def load_memories(self, state: State, config: RunnableConfig) -> State:
        """Load memories for the current conversation.

        Args:
            state (schemas.State): The current state of the conversation.
            config (RunnableConfig): The runtime configuration for the agent.

        Returns:
            State: The updated state with loaded memories.
        """
        convo_str = get_buffer_string(state["messages"])
        convo_str = self.tokenizer.decode(self.tokenizer.encode(convo_str)[:2048])
        recall_memories = search_recall_memories.invoke(convo_str, config)
        return dict(recall_memories=recall_memories)

    def route_tools(self, state: State):
        """Determine whether to use tools or end the conversation based on the last message.

        Args:
            state (schemas.State): The current state of the conversation.

        Returns:
            schemas.State: The updated state with the agent's response.
        """
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"

        return END

    def build_graph(self) -> None:
        """
        :return:
        """
        builder = StateGraph(State)
        builder.add_node(self.load_memories)
        builder.add_node(self.agent)
        builder.add_node("tools", ToolNode(self.tools))

        # Add edges to the graph
        builder.add_edge(START, "load_memories")
        builder.add_edge("load_memories", "agent")
        builder.add_conditional_edges("agent", self.route_tools, ["tools", END])
        builder.add_edge("tools", "agent")

        # Compile the graph
        memory = MemorySaver()
        self.graph = builder.compile(checkpointer=memory)

    @observe()
    async def run(self, user_message: str, user_config: RunnableConfig):
        """
         Args:
            message (str): The user's message.
            config (RunnableConfig): The runtime configuration for the agent.
        :return:
        Text/Answer
        """
        from langchain_core.messages import AIMessageChunk, HumanMessage

        async for msg, metadata in self.graph.astream({"messages": [("user", user_message)]}, config=user_config,
                                                      stream_mode="messages"):
            if isinstance(msg, AIMessageChunk):
                yield msg.content


        # async for chunk in self.graph.astream({"messages": [("user", user_message)]}, config=user_config):
        #     # print(chunk)
        #     # pretty_print_stream_chunk(chunk)
        #     for node, updates in chunk.items():
        #         print(f"Update from node: {node}")
        #         if "messages" in updates:
        #             yield updates["messages"][-1].content
                
            
            # if 'agent' in chunk.keys():
            #     yield chunk['agent']['messages'][-1].content
        # return "done"

# if __name__ == "__main__":
#     agent = LongTermMemoryAgent(model_name="gpt-4o-mini")
#     agent.build_graph()
#     config = {"configurable": {"user_id": "1", "thread_id": "1"}}
#     while True:
#         message = input("Enter your message: ")
#         print(agent.run(message, config))
