#This file defines the 3 tools the agent can use. 
# Each tool is just a Python function wrapped with a @tool decorator 
# — LangChain reads the docstring to understand when to call it.


from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from sqlalchemy.orm import Session
from datetime import datetime
import os
from dotenv import load_dotenv

from models import engine, LeaveRequest, ExpenseClaim
from rag import get_query_engine

load_dotenv()

# ── SQL Database connection for LangChain ────────────────────────────────────
# LangChain's SQLDatabase wraps SQLAlchemy and gives the agent
# a safe interface to query — it auto-reads the schema too

db = SQLDatabase.from_uri(
    os.getenv("DATABAE_URL"),
    include_tables=[
      "employees",
      "leave_balance",
      "leave_requests",
      "expense_claims"
    ],
    sample_row_in_table_info =2

)

# ── RAG query engine from Phase 2 ────────────────────────────────────────────
rag_engine = get_query_engine()

# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1 — Policy Search
# Called when employee asks about company policies, rules, entitlements
# ─────────────────────────────────────────────────────────────────────────────

@tool
def search_hr_policy(query :str) ->str:
  """
  Search the HR policy documents to answer questions about company
    policies, rules, and entitlements.
    Use this for questions like:
    - What is the maternity leave policy?
    - How do I submit an expense claim?
    - What are the working hours?
    - What expenses are reimbursable?
    
  """
  response =rag_engine.query(query)
  return str(response)

# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2 — Employee Data Query
# Called when employee asks about their personal data
# ─────────────────────────────────────────────────────────────────────────────

@tool
def query_employee_data(query: str) ->str:
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
  # LangChain's db.run() takes natural language,
  # generates SQL internally, and returns results as a string

  try: 
        result = db.run(query)
        return result if result else "No data found for your query."
  
  except Exception as e:
        return f"Could not retrieve data: {str(e)}"
  

# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3a — Submit Leave Request
# Called when employee wants to apply for leave
# ─────────────────────────────────────────────────────────────────────────────
  
@tool
def submit_leave_request(
    employee_id: int,
    leave_type: str,
    start_date: str,
    end_date: str
) ->str :
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
                employee_id = employee_id,
                leave_type  = leave_type,
                start_date  = datetime.strptime(start_date, "%Y-%m-%d").date(),
                end_date     = datetime.strptime(end_date,   "%Y-%m-%d").date(),
                status       = "pending",
                submitted_at = datetime.now()
             )
             session.add(request)
             session.commit()
             session.refresh(request)
             return (
                f"   Leave request submitted successfully!\n"
                f"   Request ID : {request.id}\n"
                f"   Type       : {leave_type}\n"
                f"   From       : {start_date} → {end_date}\n"
                f"   Status     : pending (HR will review within 2 working days)"
            )
         
  except Exception as e:
        return f"❌ Failed to submit leave request: {str(e)}"

# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3b — Submit Expense Claim
# Called when employee wants to file an expense
# ─────────────────────────────────────────────────────────────────────────────

@tool
def submit_expense_claim(
    employee_id : int,
    category : str,
    amount   : float,
    description : str

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
                employee_id  = employee_id,
                category     = category,
                amount       = amount,
                description  = description,
                status       = "pending",
                submitted_at = datetime.now()
            )
            session.add(claim)
            session.commit()
            session.refresh(claim)

            return (
                f"Expense claim submitted successfully!\n"
                f"   Claim ID    : {claim.id}\n"
                f"   Category    : {category}\n"
                f"   Amount      : Rs. {amount}\n"
                f"   Description : {description}\n"
                f"   Status      : pending (processed in 5-7 working days)"
            )
    except Exception as e:
        return f"❌ Failed to submit expense claim: {str(e)}"
    

# Export all tools as a list — agent.py imports this
ALL_TOOLS = [
    search_hr_policy,
    query_employee_data,
    submit_leave_request,
    submit_expense_claim,
]



