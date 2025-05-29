# Import relevant functionality
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.prebuilt import create_react_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_openai import ChatOpenAI 
import os
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv
from functions.download_transcripts_func import download_transcripts_func
from common.common import GraphState
from tools.crawl_web_page_tool import CrawlWebPageSyncTool
from tools.query_database_tool import QueryDatabaseTool
from functions.initialize_database import initialize_database
import asyncio
from common.logging_config import logger

load_dotenv()

async def main():
    """Main function to set up the state graph and invoke the LLM with tools."""
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o")

    tools = [CrawlWebPageSyncTool(),
            QueryDatabaseTool(db_path=os.getenv("DB_PATH"))]

    llm_with_tools = llm.bind_tools(tools)

    async def tool_calling_llm(state: GraphState) -> dict:
        """Function to call the LLM with tools."""
        response = await llm_with_tools.ainvoke(
            [HumanMessage(content=state["query"])]
        )
        state["messages"] = [response]
        logger.info(f"LLM Response: {response}")
        return state

    def decide_next_node(state: GraphState) -> str:
        """Decide the next node based on the state."""
        # print(f"decide_next_node: state: {state}")
        
        messages = state["messages"]
        tool_messages = [msg for msg in messages if isinstance(msg, ToolMessage)]
        
        for msg in tool_messages:
            if msg.name == "crawl_web_page":
                return "download_transcripts_func"
            elif msg.name == "query_database":
                return END
            
    # Create the state graph
    builder = StateGraph(GraphState)
    builder.add_node("tool_calling_llm", tool_calling_llm)
    builder.add_node("tools", ToolNode(tools))
    builder.add_node("download_transcripts_func", download_transcripts_func)
    builder.add_node("initialize_database", initialize_database)

    builder.add_edge(START, "tool_calling_llm")
    builder.add_conditional_edges("tool_calling_llm", tools_condition, ["tools", END])
    builder.add_conditional_edges("tools", decide_next_node)
    builder.add_edge("download_transcripts_func", "initialize_database")
    builder.add_edge("initialize_database", END)

    graph = builder.compile()

    graph.get_graph().print_ascii()

    while True:
        # Get user input
        query = input("User> ")
        if query.lower() == 'exit' or query.lower() == 'quit':
            print("Exiting the program.")
            break

        # Create the initial state
        initial_state = GraphState(query=query, messages=[HumanMessage(content=query)])

        # Invoke the graph with the initial state
        result = await graph.ainvoke(initial_state, debug=False)

        # Print the result
        print(f"Agent> {result["messages"][-1].content}")

        # Get all the blogs
        # result = await graph.ainvoke(
        #     GraphState(query="get all blogs from https://www.thecloudcast.net"), debug=False
        # )

        # result = await graph.ainvoke(
        #     GraphState(query="podcast on AI infrastructure and security"), debug=False
        # )

if __name__ == "__main__":
    asyncio.run(main())