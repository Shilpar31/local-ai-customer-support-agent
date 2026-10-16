import uuid
import streamlit as st
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver


# Demo customer/order data
# Replace these dictionaries with a database or API in production.
ORDERS = {
    "12345": {
        "status": "Out for delivery",
        "estimated_delivery": "Today by 8 PM",
        "items": ["Wireless headphones"],
        "total": "₹2,499",
    },
    "67890": {
        "status": "Shipped",
        "estimated_delivery": "October 19, 2026",
        "items": ["Laptop stand", "USB-C hub"],
        "total": "₹3,199",
    },
    "24680": {
        "status": "Processing",
        "estimated_delivery": "October 21, 2026",
        "items": ["Mechanical keyboard"],
        "total": "₹4,499",
    },
}

RETURN_POLICY = (
    "Most unused items can be returned within 10 days of delivery. "
    "Items must be in their original condition and packaging. "
    "Some categories may have different rules. This demo cannot submit a real return."
)

SHIPPING_POLICY = (
    "Standard shipping usually takes 3–5 business days after dispatch. "
    "Delivery dates are estimates and may change due to carrier delays."
)



# LangGraph state and tools

class GraphState(TypedDict):
    messages: Annotated[list, add_messages]


@tool
def check_order_status(order_id: str) -> str:
    """Look up a demo order by its order ID and return status, items, total, and estimated delivery."""
    order = ORDERS.get(order_id.strip())
    if not order:
        return (
            f"No order was found for ID {order_id}. "
            "Ask the customer to check the ID. Demo order IDs: 12345, 67890, 24680."
        )
    return (
        f"Order ID: {order_id}\n"
        f"Status: {order['status']}\n"
        f"Estimated delivery: {order['estimated_delivery']}\n"
        f"Items: {', '.join(order['items'])}\n"
        f"Order total: {order['total']}"
    )


@tool
def explain_return_policy() -> str:
    """Explain the store's return policy. Does not create or submit a return."""
    return RETURN_POLICY


@tool
def explain_shipping_policy() -> str:
    """Explain standard shipping timelines and delivery estimates."""
    return SHIPPING_POLICY


@tool
def product_information(product_name: str) -> str:
    """Return demo product information for headphones, laptop stand, USB-C hub, and mechanical keyboard."""
    products = {
        "wireless headphones": "Wireless headphones: demo price ₹2,499. Order ID 12345 contains this item.",
        "laptop stand": "Laptop stand: demo item in order 67890. Contact support for current product specifications.",
        "usb-c hub": "USB-C hub: demo item in order 67890. Contact support for compatibility and current specifications.",
        "mechanical keyboard": "Mechanical keyboard: demo price ₹4,499. Order ID 24680 contains this item.",
    }
    key = product_name.strip().lower()
    for name, info in products.items():
        if name in key or key in name:
            return info
    return (
        "I don't have details for that product in this demo. "
        "Try wireless headphones, laptop stand, USB-C hub, or mechanical keyboard."
    )


@tool
def escalate_to_human(reason: str) -> str:
    """Flag a conversation for human support when a customer asks for a person, is frustrated, or needs manual review."""
    return (
        f"ESCALATION REQUESTED: {reason}. "
        "This is a demo only; no real support ticket was created. "
        "A production app should send this request to a support queue."
    )


TOOLS = [
    check_order_status,
    explain_return_policy,
    explain_shipping_policy,
    product_information,
    escalate_to_human,
]


@st.cache_resource
def build_agent():
    model = ChatOllama(
        model="qwen3:8b",
        temperature=0,
    )
    model_with_tools = model.bind_tools(TOOLS)

    def agent_node(state: GraphState):
        system_message = (
            "You are a helpful, calm customer-support assistant for a demo online store. "
            "Use tools for order lookups, store policies, product information, and escalation. "
            "Never invent order details or claim that an actual refund, cancellation, return, or ticket "
            "has been submitted. The tools use mock data. If a customer is angry, asks for a human, "
            "or the issue needs manual review, use escalate_to_human. Ask concise clarifying questions "
            "when needed. Do not ask for passwords, payment-card numbers, or other sensitive information. "
            "Be clear that delivery dates are estimates."
        )
        # Include system guidance on each model call without storing it as a user-visible chat message.
        from langchain_core.messages import SystemMessage
        response = model_with_tools.invoke(
            [SystemMessage(content=system_message)] + state["messages"]
        )
        return {"messages": [response]}

    builder = StateGraph(GraphState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=MemorySaver())


st.set_page_config(
    page_title="Local AI Customer Support",
    page_icon="💬",
    layout="centered",
)

st.title("Local AI Customer Support")
st.caption("Powered by Qwen3 8B + Ollama + LangGraph. Uses demo order data only.")

with st.sidebar:
    st.header("Try a question")
    examples = [
        "Where is my order? My ID is 12345.",
        "Can you check order 67890?",
        "What is your return policy?",
        "How long does shipping take?",
        "Tell me about the wireless headphones.",
        "I’m frustrated. Please connect me to a human.",
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.pending_prompt = example

    st.divider()
    if st.button("➕ Start a new conversation", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.chat_history = []
        st.session_state.pending_prompt = ""
        st.rerun()

    st.caption("Demo order IDs: 12345, 67890, 24680")
    st.caption("No real orders, returns, refunds, or tickets are changed.")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = ""

# Render chat history from the UI session.
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about an order, shipping, returns, or a product…")
if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = ""

if prompt:
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            agent = build_agent()
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = agent.invoke(
                {"messages": [HumanMessage(content=prompt)]},
                config=config,
            )
            answer = ""
            for message in reversed(result["messages"]):
                if isinstance(message, AIMessage) and message.content:
                    answer = message.content
                    break
            if not answer:
                answer = "I couldn't generate a response. Please try again."
            st.markdown(answer)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": answer}
            )
        except Exception as exc:
            st.error(
                "I couldn't connect to the local model. Make sure Ollama is running "
                "and that qwen3:8b has been downloaded."
            )
            with st.expander("Technical details"):
                st.code(str(exc))
