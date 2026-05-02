import re
from datetime import datetime

from dotenv import load_dotenv
from langchain_core.tools import tool
from sqlalchemy import text
from sqlalchemy.orm import Session

from langchain_classic.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import PromptTemplate

from llm import get_llm
from models import ExpenseClaim, LeaveRequest, engine
from rag import retrieve_policy_context

load_dotenv()

ALLOWED_TABLES = {
    "employees",
    "leave_balance",
    "leave_requests",
    "expense_claims",
}

SQL_KEYWORDS_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|commit|rollback)\b",
    re.IGNORECASE,
)

SQL_DB = SQLDatabase(
    engine,
    schema="public",
    include_tables=sorted(ALLOWED_TABLES),
    sample_rows_in_table_info=0,
)

SQL_QUERY_PROMPT = PromptTemplate.from_template(
    """
You convert HR employee data questions into a single PostgreSQL read-only query.

Rules:
- Return exactly one SQL statement and nothing else.
- Only use SELECT or WITH queries.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, REVOKE, COMMIT, or ROLLBACK.
- Use only the tables shown in the schema below.
- If the user asks how many leave days are left, calculate remaining_days as total_days - used_days.
- If a leave type is implied, filter by leave_type.
- If the user asks for history or claims, include the most relevant fields and order recent items first.
- Unless the user asks for a count or a single balance row, limit list-style queries to at most {top_k} rows.
- Prefer explicit column names and aliases.
- Use only columns that exist in the schema below.
- Return SQL only. Do not add explanations, prose, or markdown fences.

Available schema:
{table_info}

Question: {input}
""".strip()
)

SQL_QUERY_CHAIN = None


def _get_sql_query_chain():
    global SQL_QUERY_CHAIN
    if SQL_QUERY_CHAIN is None:
        SQL_QUERY_CHAIN = create_sql_query_chain(
            llm=get_llm(),
            db=SQL_DB,
            prompt=SQL_QUERY_PROMPT,
            k=10,
        )
    return SQL_QUERY_CHAIN


def _extract_text(response) -> str:
    """Normalizes chat model responses into plain text."""
    if hasattr(response, "content"):
        content = response.content
    else:
        content = response

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "\n".join(part for part in parts if part).strip()

    return str(content).strip()


def _strip_code_fences(text_value: str) -> str:
    cleaned = text_value.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_+-]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)

    return cleaned.strip()


def _generate_select_sql(question: str) -> str:
    sql = _get_sql_query_chain().invoke(
        {
            "question": question,
            "table_names_to_use": sorted(ALLOWED_TABLES),
        }
    )
    sql = _strip_code_fences(_extract_text(sql))
    normalized = re.sub(r"\s+", " ", sql).strip().lower()

    if not normalized.startswith(("select", "with")):
        raise ValueError(f"Expected a read-only SQL query, got: {sql}")

    if SQL_KEYWORDS_PATTERN.search(sql):
        raise ValueError("Generated SQL contained a non-read-only statement.")

    sql_no_trailing_semicolon = sql.rstrip().rstrip(";")
    if ";" in sql_no_trailing_semicolon:
        raise ValueError("Generated SQL contained multiple statements.")

    referenced_tables = set(
        re.findall(
            r'\b(?:from|join)\s+(?:[a-zA-Z_][a-zA-Z0-9_]*\.)?"?([a-zA-Z_][a-zA-Z0-9_]*)"?',
            sql_no_trailing_semicolon,
            flags=re.IGNORECASE,
        )
    )
    disallowed_tables = referenced_tables - ALLOWED_TABLES
    if disallowed_tables:
        raise ValueError(
            f"Generated SQL referenced unsupported tables: {sorted(disallowed_tables)}"
        )

    return sql_no_trailing_semicolon


def _execute_select_sql(sql: str) -> str:
    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = result.mappings().all()

    if not rows:
        return f"SQL: {sql}\nResult: No matching records found."

    rendered_rows = [
        {key: str(value) if value is not None else None for key, value in row.items()}
        for row in rows
    ]
    return f"SQL: {sql}\nResult: {rendered_rows}"


def _handle_leave_balance_query(query: str) -> str | None:
    lower_query = query.lower()
    is_leave_balance_question = any(
        phrase in lower_query
        for phrase in ("leave days", "leave balance", "days left", "leave left")
    )
    if not is_leave_balance_question:
        return None

    leave_type = next(
        (
            value
            for value in ("annual", "sick", "maternity", "paternity")
            if value in lower_query
        ),
        None,
    )
    if not leave_type:
        return None

    employee_id_match = re.search(
        r"employee\s*(?:id)?\s*[:#-]?\s*(\d+)",
        query,
        flags=re.IGNORECASE,
    )
    name_match = (
        re.search(r"does\s+([A-Za-z][A-Za-z\s]+?)\s+have", query, flags=re.IGNORECASE)
        or re.search(r"([A-Za-z][A-Za-z\s]+?)'s\s+.*leave", query, flags=re.IGNORECASE)
    )

    sql = """
SELECT
    e.id AS employee_id,
    e.name AS employee_name,
    lb.leave_type,
    lb.total_days,
    lb.used_days,
    lb.total_days - lb.used_days AS remaining_days
FROM leave_balance lb
JOIN employees e ON e.id = lb.employee_id
WHERE lb.leave_type = :leave_type
"""
    params = {"leave_type": leave_type}

    if employee_id_match:
        sql += " AND e.id = :employee_id"
        params["employee_id"] = int(employee_id_match.group(1))
    elif name_match:
        name_pattern = name_match.group(1).strip()
        sql += " AND e.name ILIKE :employee_name"
        params["employee_name"] = f"%{name_pattern}%"
    else:
        return None

    sql += " LIMIT 1"

    with engine.connect() as connection:
        row = connection.execute(text(sql), params).mappings().first()

    if not row:
        return None

    rendered_row = {
        key: str(value) if value is not None else None for key, value in row.items()
    }
    return f"Result: {[rendered_row]}"


@tool(return_direct=True)
def search_hr_policy(query: str) -> str:
    """
    Search HR policy documents and answer questions about company rules,
    entitlements, and procedures.
    Use this for questions like:
    - What is the maternity leave policy?
    - How do I submit an expense claim?
    - What are the working hours?
    - What expenses are reimbursable?
    """
    try:
        context_chunks = retrieve_policy_context(query, top_k=3)
        if not context_chunks:
            return "I couldn't find a matching policy section for that question."

        formatted_context = "\n\n".join(
            f"Policy excerpt {index + 1}:\n{chunk}"
            for index, chunk in enumerate(context_chunks)
        )
        prompt = f"""
        You are an HR policy assistant. Answer the employee's question using only the
        policy excerpts below. If the excerpts do not contain the answer, say that the
        policy context is insufficient. Keep the answer concise and professional.

        Employee question:
        {query}

        Policy excerpts:
        {formatted_context}
        """.strip()

        return _extract_text(get_llm().invoke(prompt))
    except Exception as exc:
        return f"Could not retrieve policy information: {exc}"


@tool
def query_employee_data(query: str) -> str:
    """
    Query the HR database to get employee-specific information.
    Use this for questions like:
    - How many leave days do I have left?
    - What is my salary?
    - Show me my pending expense claims
    - How many sick days have I used?
    - What is my leave history?
    The query should be a plain English question about employee data.
    """
    try:
        leave_balance_result = _handle_leave_balance_query(query)
        if leave_balance_result:
            return leave_balance_result

        sql = _generate_select_sql(query)
        return _execute_select_sql(sql)
    except Exception as exc:
        return f"Could not retrieve data: {exc}"


@tool
def submit_leave_request(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str,
) -> str:
    """
    Submit a leave request for an employee.
    Use this when an employee wants to apply for leave.
    Parameters:
    - employee_id: the employee's ID number
    - leave_type: 'annual', 'sick', or 'maternity'
    - start_date: in YYYY-MM-DD format
    - end_date: in YYYY-MM-DD format
    Example: employee 1 wants annual leave from 2025-02-10 to 2025-02-14
    """
    try:
        with Session(engine) as session:
            request = LeaveRequest(
                employee_id=employee_id,
                leave_type=leave_type,
                start_date=datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date=datetime.strptime(end_date, "%Y-%m-%d").date(),
                status="pending",
                submitted_at=datetime.now(),
            )
            session.add(request)
            session.commit()
            session.refresh(request)

        return (
            f"Leave request submitted successfully!\n"
            f"Request ID : {request.id}\n"
            f"Type       : {leave_type}\n"
            f"From       : {start_date} to {end_date}\n"
            f"Status     : pending (HR will review within 2 working days)"
        )
    except Exception as exc:
        return f"Failed to submit leave request: {exc}"


@tool
def submit_expense_claim(
    employee_id: int,
    category: str,
    amount: float,
    description: str,
) -> str:
    """
    Submit an expense reimbursement claim for an employee.
    Use this when an employee wants to claim a business expense.
    Parameters:
    - employee_id: the employee's ID number
    - category: 'travel', 'meals', 'equipment', or 'training'
    - amount: the expense amount in rupees
    - description: brief description of the expense
    Example: employee 2 wants to claim Rs.450 for a team meal
    """
    try:
        with Session(engine) as session:
            claim = ExpenseClaim(
                employee_id=employee_id,
                category=category,
                amount=amount,
                description=description,
                status="pending",
                submitted_at=datetime.now(),
            )
            session.add(claim)
            session.commit()
            session.refresh(claim)

        return (
            f"Expense claim submitted successfully!\n"
            f"Claim ID    : {claim.id}\n"
            f"Category    : {category}\n"
            f"Amount      : Rs. {amount}\n"
            f"Description : {description}\n"
            f"Status      : pending (processed in 5-7 working days)"
        )
    except Exception as exc:
        return f"Failed to submit expense claim: {exc}"


ALL_TOOLS = [
    search_hr_policy,
    query_employee_data,
    submit_leave_request,
    submit_expense_claim,
]
