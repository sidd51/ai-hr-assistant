from sqlalchemy import (
  create_engine, Column, Integer, 
  String, Float, Date, DateTime,Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv
import os;

load_dotenv()

Base =declarative_base()
engine =create_engine(os.getenv("DATABASE_URL"))

class Employee(Base):
  __tablename__ ="employees"

  id          =Column(Integer , primary_key=True)
  name        =Column(String, nullable=False)
  email       =Column(String)
  department  =Column(String)
  role        =Column(String)
  salary      =Column(Float)
  joined_date =Column(Date)

  leave_balances =relationship("LeaveBalance", back_populates="employee")
  leave_requests = relationship("LeaveRequest", back_populates="employee")
  expense_claims = relationship("ExpenseClaim", back_populates="employee")


class LeaveBalance(Base):
  __tablename__ = "leave_balance"

  id          =Column(Integer, primary_key=True)
  employee_id = Column(Integer, ForeignKey("employees.id"))
  leave_type  = Column(String)  # annual / sick / maternity
  total_days  = Column(Integer)
  used_days   = Column(Integer)

  employee = relationship("Employee", back_populates="leave_balances")


class LeaveRequest(Base): 
  __tablename__ = "leave_requests"

  id            = Column(Integer, primary_key=True)
  employee_id   = Column(Integer, ForeignKey("employees.id"))
  leave_type    = Column(String)
  start_date    = Column(Date)
  end_date      = Column(Date)
  status        = Column( String, default="pending")
  submitted_at  = Column( DateTime, default= func.now())

  employee= relationship( "Employee" , back_populates="leave_requests")


class ExpenseClaim(Base):
    __tablename__ = "expense_claims"

    id           = Column(Integer, primary_key=True)
    employee_id  = Column(Integer, ForeignKey("employees.id"))
    category     = Column(String)  # travel / meals / equipment
    amount       = Column(Float)
    description  = Column(Text)
    status       = Column(String,   default="pending")
    submitted_at = Column(DateTime, default=func.now())

    employee = relationship("Employee", back_populates="expense_claims")
