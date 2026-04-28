from datetime import date, datetime
from sqlalchemy.orm import Session
from models import Base, Employee, LeaveBalance, LeaveRequest, ExpenseClaim, engine

# Creates all tables"
Base.metadata.create_all(engine)
print("✅ Tables created")

with Session(engine) as session:

    # Clear existing data so script is safe to re-run
    session.query(ExpenseClaim).delete()
    session.query(LeaveRequest).delete()
    session.query(LeaveBalance).delete()
    session.query(Employee).delete()
    session.commit()

    # Employees
    session.add_all([
        Employee(id=1, name="Alice Johnson", email="alice@company.com",
                 department="Engineering", role="Senior Engineer",
                 salary=95000, joined_date=date(2021, 3, 15)),
        Employee(id=2, name="Bob Smith",     email="bob@company.com",
                 department="Marketing",    role="Marketing Lead",
                 salary=75000, joined_date=date(2020, 7, 1)),
        Employee(id=3, name="Carol White",   email="carol@company.com",
                 department="HR",           role="HR Manager",
                 salary=80000, joined_date=date(2019, 11, 20)),
        Employee(id=4, name="David Lee",     email="david@company.com",
                 department="Engineering",  role="Junior Engineer",
                 salary=65000, joined_date=date(2023, 1, 10)),
        Employee(id=5, name="Eva Brown",     email="eva@company.com",
                 department="Finance",      role="Finance Analyst",
                 salary=72000, joined_date=date(2022, 5, 5)),
    ])
    session.commit()

    # Leave balances
    session.add_all([
        LeaveBalance(employee_id=1, leave_type="annual",    total_days=20, used_days=5),
        LeaveBalance(employee_id=1, leave_type="sick",      total_days=10, used_days=2),
        LeaveBalance(employee_id=2, leave_type="annual",    total_days=20, used_days=12),
        LeaveBalance(employee_id=2, leave_type="sick",      total_days=10, used_days=0),
        LeaveBalance(employee_id=3, leave_type="annual",    total_days=20, used_days=8),
        LeaveBalance(employee_id=3, leave_type="maternity", total_days=90, used_days=0),
        LeaveBalance(employee_id=4, leave_type="annual",    total_days=20, used_days=3),
        LeaveBalance(employee_id=5, leave_type="annual",    total_days=20, used_days=7),
    ])
    session.commit()

    # Leave requests
    session.add_all([
        LeaveRequest(employee_id=1, leave_type="annual",
                     start_date=date(2024, 12, 23), end_date=date(2024, 12, 27),
                     status="approved", submitted_at=datetime(2024, 12, 1, 10, 0)),
        LeaveRequest(employee_id=2, leave_type="sick",
                     start_date=date(2024, 11, 5),  end_date=date(2024, 11, 6),
                     status="approved", submitted_at=datetime(2024, 11, 5, 8, 30)),
        LeaveRequest(employee_id=4, leave_type="annual",
                     start_date=date(2025, 1, 2),   end_date=date(2025, 1, 3),
                     status="pending",  submitted_at=datetime(2024, 12, 20, 14, 0)),
    ])
    session.commit()

    # Expense claims
    session.add_all([
        ExpenseClaim(employee_id=1, category="travel",
                     amount=250.00, description="Client visit to Mumbai",
                     status="approved"),
        ExpenseClaim(employee_id=2, category="meals",
                     amount=45.50,  description="Team lunch",
                     status="pending"),
        ExpenseClaim(employee_id=5, category="equipment",
                     amount=120.00, description="USB hub for home office",
                     status="approved"),
    ])
    session.commit()

    print("✅ Sample data seeded successfully!")