import sqlantra_database_v2 as db
import context_memory
import hitl_workflow

# Initialize
db.init_database()
mem = context_memory.SqlantraContextMemory()
mem.set_db_module(db)
hitl = hitl_workflow.HITLWorkflow(db, mem, llm_enabled=False)

print('Testing rapid submissions with approval-required amounts...')
print('=' * 50)

# Test with amounts that require approval (over thresholds)
rapid_results = []
for i in range(3):
    # Use amounts that require approval:
    # - travel: over $1000 requires approval
    # - meals: over $100 requires approval  
    # - software: over $200 requires approval
    if i == 0:
        cat, amt = 'travel', 1500
    elif i == 1:
        cat, amt = 'meals', 150
    else:
        cat, amt = 'software', 250
    r = hitl.submit_expense(f'User{i}', cat, amt, f'Expense {i}')
    rapid_results.append(r)
    print(f'  Submission {i}: {cat} ${amt} -> status={r["status"]}, pending={r["pending"]}')

print()
print('Checking pending approvals after all submissions:')
pending = hitl.get_pending_for_ui()
print(f'Pending approvals count: {len(pending)}')
for p in pending:
    print(f'  - {p}')

# All three should be pending since they're over their respective thresholds
expected_pending = 3
actual_pending = len(pending)
print(f'Expected pending: {expected_pending}, Actual pending: {actual_pending}')
if actual_pending == expected_pending:
    print('✅ PASS: All high-value submissions created pending approvals')
else:
    print('❌ FAIL: Expected all submissions to require approval')

print()
print('Testing that IDs are unique...')
expense_ids = [r['expense_id'] for r in rapid_results]
approval_ids = [r.get('approval_id') for r in rapid_results if r.get('approval_id')]
print(f'Expense IDs: {len(expense_ids)} total, {len(set(expense_ids))} unique')
print(f'Approval IDs: {len(approval_ids)} total, {len(set(approval_ids))} unique')
if len(set(expense_ids)) == len(expense_ids) and len(set(approval_ids)) == len(approval_ids):
    print('✅ PASS: All IDs are unique')
else:
    print('❌ FAIL: Duplicate IDs found')
