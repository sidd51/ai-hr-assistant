from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import re

SYSTEM_PROMPT = """
You are a helpful and professional HR Assistant for our company named HarborHR.
You help employees with HR-related questions and requests.

Your capabilities:
1. Answer questions about company policies (leave, expenses, conduct)
2. Look up employee-specific data (leave balances, salary, claim history)
3. Submit leave requests on behalf of employees
4. Submit expense claims on behalf of employees

Important rules:
- Always be polite, professional, and concise
- Remember employee identity details shared earlier in the conversation, including employee ID
- When an employee ID is known, always pass that exact employee ID in tool calls instead of relying on name matching
- For `query_employee_data`, always provide both the natural-language query and the employee_id when employee_id is known
- When submitting requests, confirm the details with the employee first
- If you query employee data, present it in a clean readable format
- Never make up policy information — always use the search_hr_policy tool
- For policy questions, call search_hr_policy once and use the returned answer directly
- If you cannot help with something, say so clearly and suggest contacting HR directly
- For leave requests, always check the leave balance first before submitting
- If a leave balance check fails, do not submit the leave request
""".strip()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)


def _get_tools():
    from tools import ALL_TOOLS, query_employee_data, search_hr_policy

    return ALL_TOOLS, query_employee_data, search_hr_policy


def create_agent():
    """
    Builds and returns the LangChain agent executor.
    """
    from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
    from llm import get_llm

    all_tools, _, _ = _get_tools()
    llm = get_llm()
    agent = create_tool_calling_agent(llm, all_tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=all_tools,
        verbose=True,
        max_iterations=5,
        handle_parsing_errors=True,
    )


class HRAssistant:
    """
    Wraps the agent with in-memory conversation history.
    Each instance represents one user's session.
    """

    def __init__(self):
        self.agent = create_agent()
        self.chat_history = []
        self.employee_id = None

    def _update_employee_context(self, user_message: str) -> None:
        employee_id_match = re.search(
            r"employee\s*id\s*[:#-]?\s*(\d+)",
            user_message,
            flags=re.IGNORECASE,
        )
        if employee_id_match:
            self.employee_id = int(employee_id_match.group(1))

    def _build_agent_input(self, user_message: str) -> str:
        if self.employee_id is None:
            return user_message

        return (
            f"Known employee context: employee_id={self.employee_id}. "
            f"Always use this exact employee ID in tool calls unless the user changes it.\n"
            f"User message: {user_message}"
        )

    def _fallback_response(self, user_message: str) -> str:
        _, query_employee_data, search_hr_policy = _get_tools()
        lower_message = user_message.lower()
        contextual_message = user_message
        if self.employee_id is not None and "employee id" not in lower_message:
            contextual_message = f"{user_message} (employee ID {self.employee_id})"

        if any(
            keyword in lower_message
            for keyword in (
                "policy",
                "maternity",
                "paternity",
                "working hours",
                "reimbursable",
                "can i claim",
                "eligible",
            )
        ):
            return search_hr_policy.invoke({"query": contextual_message})

        if any(
            keyword in lower_message
            for keyword in ("leave", "salary", "expense", "claim", "balance", "history")
        ):
            return query_employee_data.invoke(
                {
                    "query": contextual_message,
                    "employee_id": self.employee_id,
                }
            )

        return (
            "I ran into a tool-calling issue while processing that request. "
            "Please try again, or contact HR directly if the problem continues."
        )

    def chat(self, user_message: str) -> str:
        self._update_employee_context(user_message)
        agent_input = self._build_agent_input(user_message)

        try:
            response = self.agent.invoke(
                {
                    "input": agent_input,
                    "chat_history": self.chat_history,
                }
            )
            answer = response["output"]
        except Exception as e:
            answer = self._fallback_response(user_message)

        self.chat_history.append(HumanMessage(content=user_message))
        self.chat_history.append(AIMessage(content=answer))
        return answer


if __name__ == "__main__":
    print("HR Assistant is starting up...\n")
    assistant = HRAssistant()

    test_conversation = [
        "Hi! I'm Alice (employee ID 1). How many annual leave days do I have left?",
        "What's the company's maternity leave policy?",
        "I'd like to apply for annual leave from 2025-03-10 to 2025-03-14.",
        
    ]

    for message in test_conversation:
        print(f"Employee: {message}")
        response = assistant.chat(message)
        print(f"Assistant: {response}")
        print("-" * 60)
