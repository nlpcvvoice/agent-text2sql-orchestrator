import sqlantra_database_v2 as db
import context_memory
import hitl_workflow

# Initialize
db.init_database()
mem = context_memory.SqlantraContextMemory()
mem.set_db_module(db)
hitl = hitl_workflow.HITLWorkflow(db, mem, llm_enabled=False)

print('Testing approval/reject workflow...')
print('=' * 40)

# Store our test data separately
test_cases = [
    ('User0', 'travel', 1500, 'Flight 0'),
    ('User1', 'meals', 150, 'Meal 1'),
    ('User2', 'software', 250, 'Software 2')
]

rapid_results = []

for i, (emp, cat, amt, desc) in enumerate(test_cases):
    r = hitl.submit_expense(emp, cat, amt, desc)
    rapid_results.append((emp, cat, amt, desc, r))  # Store original data with result
    print(f'  Submission {i}: {cat} ${amt} -> status={r["status"]}, pending={r["pending"]}')

print(f'Created {len(rapid_results)} expense submissions, all pending approval')

# Check pending count
pending_before = hitl.get_pending_for_ui()
print(f'Pending approvals before processing: {len(pending_before)}')

# Approve the first one
if len(rapid_results) > 0:
    emp0, cat0, amt0, desc0, first_result = rapid_results[0]
    first_approval_id = first_result['approval_id']
    print(f'\nApproving first expense: {first_result["expense_id"]} ({cat0} ${amt0})')
    
    confirm_result = hitl.confirm_and_notify(first_approval_id, True, 'Approved by supervisor')
    print(f'Approval result: {confirm_result["status"]}')
    print(f'Manager message: {confirm_result["manager_message"]}')
    print(f'Employee message: {confirm_result["employee_message"]}')
    
    # Check pending count after approval
    pending_after = hitl.get_pending_for_ui()
    print(f'\nPending approvals after approval: {len(pending_after)}')
    
    # Should have 2 remaining (we approved 1 of 3)
    expected_remaining = 2
    actual_remaining = len(pending_after)
    if actual_remaining == expected_remaining:
        print('✅ PASS: Correct number of approvals remaining')
    else:
        print(f'❌ FAIL: Expected {expected_remaining} remaining, got {actual_remaining}')

print()
print('Testing reject functionality...')
if len(rapid_results) > 1:
    emp1, cat1, amt1, desc1, second_result = rapid_results[1]
    second_approval_id = second_result['approval_id']
    print(f'\nRejecting second expense: {second_result["expense_id"]} ({cat1} ${amt1})')
    
    reject_result = hitl.confirm_and_notify(second_approval_id, False, 'Not compliant with policy')
    print(f'Reject result: {reject_result["status"]}')
    print(f'Manager message: {reject_result["manager_message"]}')
    print(f'Employee message: {reject_result["employee_message"]}')
    
    # Check pending count after reject
    pending_after_reject = hitl.get_pending_for_ui()
    print(f'\nPending approvals after reject: {len(pending_after_reject)}')
    
    # Should have 1 remaining (we approved 1, rejected 1 of 3)
    expected_remaining_after_reject = 1
    actual_remaining_after_reject = len(pending_after_reject)
    if actual_remaining_after_reject == expected_remaining_after_reject:
        print('✅ PASS: Correct number of approvals remaining after reject')
    else:
        print(f'❌ FAIL: Expected {expected_remaining_after_reject} remaining, got {actual_remaining_after_reject}')

print()
print('Testing that no approvals remain after processing all...')
if len(rapid_results) > 2:
    emp2, cat2, amt2, desc2, third_result = rapid_results[2]
    third_approval_id = third_result['approval_id']
    print(f'\nApproving third expense: {third_result["expense_id"]} ({cat2} ${amt2})')
    
    confirm_result3 = hitl.confirm_and_notify(third_approval_id, True, 'Approved')
    print(f'Third approval result: {confirm_result3["status"]}')
    
    # Check final pending count
    pending_final = hitl.get_pending_for_ui()
    print(f'\nFinal pending approvals: {len(pending_final)}')
    if len(pending_final) == 0:
        print('✅ PASS: No approvals remain after processing all')
    else:
        print(f'❌ FAIL: Expected 0 pending, got {len(pending_final)}')

print()
print('Testing context memory tracking...')
entries = mem.get_recent_entries(20)  # Get more to see all
submit_count = sum(1 for e in entries if e['operation_type'] == 'EXPENSE_SUBMITTED')
confirm_count = sum(1 for e in entries if e['operation_type'] == 'CONFIRMATION')
approved_count = sum(1 for e in entries if e['operation_type'] == 'EXPENSE_APPROVED')
rejected_count = sum(1 for e in entries if e['operation_type'] == 'EXPENSE_REJECTED')
print(f'Context memory entries:')
print(f'  Submissions: {submit_count}')
print(f'  Confirmations: {confirm_count}')  
print(f'  Approvals: {approved_count}')
print(f'  Rejections: {rejected_count}')

# Should have 3 submissions, 3 confirmations (1 approve, 1 reject, 1 approve), 2 approvals, 1 rejection
if submit_count == 3 and confirm_count == 3 and approved_count == 2 and rejected_count == 1:
    print('✅ PASS: Context memory tracks all operations correctly')
else:
    print(f'❌ FAIL: Expected 3 submissions, 3 confirmations, 2 approvals, 1 rejection')
    print(f'         Got {submit_count} submissions, {confirm_count} confirmations, {approved_count} approvals, {rejected_count} rejections')

print()
print('Testing reset functionality...')
# Submit another expense to test reset
hitl.submit_expense('Reset Test', 'travel', 1500, 'Should be cleared')
pending_before_reset = hitl.get_pending_for_ui()
print(f'Pending approvals before reset: {len(pending_before_reset)}')

# Reset system
db.reset_database()
mem.clear()
db.init_database()
mem = context_memory.SqlantraContextMemory()
mem.set_db_module(db)
hitl_reset = hitl_workflow.HITLWorkflow(db, mem, llm_enabled=False)

pending_after_reset = hitl_reset.get_pending_for_ui()
print(f'Pending approvals after reset: {len(pending_after_reset)}')
if len(pending_after_reset) == 0:
    print('✅ PASS: Reset cleared all state')
else:
    print(f'❌ FAIL: Reset did not clear state, {len(pending_after_reset)} approvals remaining')

print()
print('=' * 40)
print('Workflow test completed')
