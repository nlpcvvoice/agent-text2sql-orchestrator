#!/usr/bin/env python3
"""Sqlantra HITL Workflow - Expense Reimbursement Approval System."""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen3.5:2b"

HIGH_VALUE_THRESHOLD = 500


def call_ollama(prompt: str, timeout: int = 60) -> str:
    """Call Ollama with a prompt."""
    try:
        req = urllib.request.Request(
            OLLAMA_URL,
            data=json.dumps(
                {
                    "model": MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 512},
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result = json.loads(response.read().decode())
            return result.get("response", "")
    except Exception as e:
        return f"[Ollama Error: {e}]"


class ExpenseCategory:
    """Pre-defined expense categories with policies."""
    CATEGORIES = {
        "travel": {"threshold": 1000, "requires_receipt": True, "description": "Travel expenses"},
        "equipment": {"threshold": 500, "requires_receipt": True, "description": "Office equipment"},
        "software": {"threshold": 200, "requires_receipt": True, "description": "Software licenses"},
        "meals": {"threshold": 100, "requires_receipt": True, "description": "Client meals"},
        "training": {"threshold": 1000, "requires_receipt": True, "description": "Training fees"},
        "other": {"threshold": 200, "requires_receipt": True, "description": "Miscellaneous"},
    }

    @classmethod
    def get_threshold(cls, category: str) -> int:
        return cls.CATEGORIES.get(category, cls.CATEGORIES["other"])["threshold"]


class ExpenseReimbursement:
    """Single expense reimbursement record."""

    def __init__(self, expense_id: str, employee: str, category: str, amount: float, description: str, receipt: bool = True):
        self.expense_id = expense_id
        self.employee = employee
        self.category = category
        self.amount = amount
        self.description = description
        self.receipt = receipt
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.status = "pending"
        self.approval_id = None
        self.approver = None
        self.approver_comment = None
        self.approved_at = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expense_id": self.expense_id,
            "employee": self.employee,
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
            "receipt": self.receipt,
            "date": self.date,
            "status": self.status,
            "approval_id": self.approval_id,
            "requires_approval": self.status == "pending",
        }


class HITLWorkflow:
    """Human-In-The-Loop Workflow Manager for Expense Reimbursement."""

    def __init__(self, db_module, context_memory, llm_enabled: bool = True):
        self.db = db_module
        self.context_memory = context_memory
        self.llm_enabled = llm_enabled
        self._pending_expenses: Dict[str, ExpenseReimbursement] = {}
        self._action_log: List[Dict] = []

    def submit_expense(
        self,
        employee: str,
        category: str,
        amount: float,
        description: str,
        receipt: bool = True
    ) -> Dict[str, Any]:
        """Submit expense - Ollama decides if approval needed."""
        expense_id = f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        expense = ExpenseReimbursement(expense_id, employee, category, amount, description, receipt)

        # Ollama evaluates if approval is needed
        threshold, llm_decision = self._evaluate_approval(category, amount)

        if llm_decision == "approve":
            expense.status = "pending"
        else:
            expense.status = "auto_approved"

        notification = self._generate_notification(expense)

        approval = None
        if expense.status == "pending":
            approval = self.db.create_approval(
                action_type="expense_reimbursement",
                details=expense.to_dict(),
                requester=employee,
                notification=notification,
            )
            expense.approval_id = approval["approval_id"]
            self._pending_expenses[expense_id] = expense

        self.context_memory.store(
            f"expense_submitted_{expense_id}",
            expense.to_dict(),
            "expense_submitted",
            {"employee": employee, "category": category, "amount": amount},
        )

        self._log_action("submit", expense_id, expense.to_dict())

        return {
            "expense_id": expense_id,
            "status": expense.status,
            "requires_approval": expense.status == "pending",
            "approval_id": expense.approval_id,
            "notification": notification,
            "pending": expense.status == "pending",
            "threshold_used": threshold,
            "llm_decision": llm_decision,
        }

    def _evaluate_approval(self, category: str, amount: float) -> tuple:
        """Evaluate if approval needed - uses Ollama + rule-based fallback."""
        default_threshold = 1000
        
        threshold = ExpenseCategory.get_threshold(category) if category in ExpenseCategory.CATEGORIES else default_threshold
        needs_approval = amount > threshold
        
        if self.llm_enabled:
            try:
                prompt = f"Is ${amount} {category} over ${threshold} threshold? Answer yes or no."
                response = call_ollama(prompt, timeout=3)
                resp = response.lower().strip()
                if "no" in resp or "not" in resp:
                    needs_approval = False
                elif "yes" in resp:
                    needs_approval = True
            except:
                pass
        
        decision = "approve" if needs_approval else "auto_approve"
        return threshold, decision

    def _generate_notification(self, expense: ExpenseReimbursement) -> str:
        """Generate Slack-style notification."""
        threshold = ExpenseCategory.get_threshold(expense.category)
        return f"Sqlantra - Expense Reimbursement\n\n{expense.employee}: ${expense.amount:.2f} {expense.category}\nThreshold: ${threshold}\nAwaiting approval"

    def _log_action(self, action: str, expense_id: str, details: Dict):
        """Log action."""
        self._action_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "expense_id": expense_id,
        })

    def confirm_and_notify(self, approval_id: str, approved: bool, comment: str = "") -> Dict[str, Any]:
        """Process approval/rejection and generate confirmation messages."""
        expense = None
        for exp_id, exp in self._pending_expenses.items():
            if exp.approval_id == approval_id:
                expense = exp
                break
        
        if not expense:
            return {"error": "Expense not found"}
        
        if approved:
            self.approve(approval_id, comment)
            manager_msg = f"Approved expense {expense.expense_id} (${expense.amount:.2f})"
            employee_msg = f"Your ${expense.amount:.2f} {expense.category} expense has been APPROVED"
            status = "approved"
        else:
            self.reject(approval_id, comment)
            manager_msg = f"Rejected expense {expense.expense_id}"
            employee_msg = f"Your ${expense.amount:.2f} expense has been REJECTED. Reason: {comment or 'No reason'}"
            status = "rejected"
        
        self.context_memory.store(
            f"confirmation_{expense.expense_id}",
            {
                "status": status,
                "manager_message": manager_msg,
                "employee_message": employee_msg,
                "approval_id": approval_id,
                "comment": comment,
                "timestamp": datetime.now().isoformat(),
            },
            "confirmation",
            {"notification_sent": True},
        )
        
        return {
            "status": status,
            "manager_message": manager_msg,
            "employee_message": employee_msg,
            "expense_id": expense.expense_id,
        }

    def approve(self, approval_id: str, comment: str = "", approver: str = "manager") -> Dict[str, Any]:
        """Approve expense."""
        result = self.db.respond_approval(approval_id, True, comment)

        for expense_id, expense in self._pending_expenses.items():
            if expense.approval_id == approval_id:
                expense.status = "approved"
                expense.approver = approver
                expense.approver_comment = comment
                expense.approved_at = datetime.now().isoformat()

                self.context_memory.store(
                    f"expense_approved_{expense_id}",
                    expense.to_dict(),
                    "expense_approved",
                    {"approver": approver},
                )

                self._log_action("approve", expense_id, expense.to_dict())
                del self._pending_expenses[expense_id]

                return {"status": "approved", "expense_id": expense_id, "message": f"Approved: {expense_id}"}

        return {"status": "error", "message": f"Approval {approval_id} not found"}

    def reject(self, approval_id: str, comment: str = "", approver: str = "manager") -> Dict[str, Any]:
        """Reject expense."""
        result = self.db.respond_approval(approval_id, False, comment)

        for expense_id, expense in self._pending_expenses.items():
            if expense.approval_id == approval_id:
                expense.status = "rejected"
                expense.approver = approver
                expense.approver_comment = comment
                expense.approved_at = datetime.now().isoformat()

                self.context_memory.store(
                    f"expense_rejected_{expense_id}",
                    expense.to_dict(),
                    "expense_rejected",
                    {"reason": comment},
                )

                self._log_action("reject", expense_id, expense.to_dict())
                del self._pending_expenses[expense_id]

                return {"status": "rejected", "expense_id": expense_id, "message": f"Rejected: {expense_id}"}

        return {"status": "error", "message": f"Approval {approval_id} not found"}

    def get_pending_for_ui(self) -> List[Dict]:
        """Get pending for UI."""
        pending = []
        for expense_id, expense in self._pending_expenses.items():
            pending.append({
                "expense_id": expense.expense_id,
                "expense": expense.to_dict(),
                "approval_id": expense.approval_id,
                "notification": self._generate_notification(expense),
            })
        return pending


if __name__ == "__main__":
    print("HITL Workflow - Expense Reimbursement")
