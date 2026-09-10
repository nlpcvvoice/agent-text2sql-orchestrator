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

# Create three expenses that should require approval:
# 1. Travel: $1500 (should require approval)
# 2. Meals: $150 (should require approval)  
# 3. Software: $250 (should require approval)

rapid_results = []
test_data = []

for i in range(3):
    if i == 0:
        emp, cat, amt, desc = f'User{i}', 'travel', 1500, f'Flight {i}'
    elif i == 1:
        emp, cat, amt, desc = f'User{i}', 'meals', 150, f'Meal {i}'
    else:
        emp, cat, amt, desc = f'User{i}', 'software', 250, f'Software {i}'
    
    test_data.append((emp, cat, amt, desc))
    r = hitl.submit_expense(emp, cat, amt, desc)
    rapid_results.append(r)

print(f'Created {len(rapid_results)} expense submissions, all pending approval')

# Check pending count
pending_before = hitl.get_pending_for_ui()
print(f'Pending approvals before processing: {len(pending_before)}')

# Approve the first one
if len(rapid_results) > 0:
    first_result = rapid_results[0]
    first_approval_id = first_result['approval_id']
    first_cat, first_amt = test_data[0][1], test_data[0][2]
    print(f'\nApproving first expense: {first_result["expense_id"]} ({first_cat} ${first_amt})')
    
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
    second_result = rapid_results[1]
    second_approval_id = second_result['approval_id']
    second_cat, second_amt = test_data[1][1], test_data[1][2]
    print(f'\nRejecting second expense: {second_result["expense_id"]} ({second_cat} ${second_amt})')
    
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
    third_result = rapid_results[2]
    third_approval_id = third_result['approval_id']
    third_cat, third_amt = test_data[2][1], test_data[2][2]
    print(f'\nApproving third expense: {third_result["expense_id"]} ({third_cat} ${third_amt})')
    
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
entries = mem.get_recent_entries(10)
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
