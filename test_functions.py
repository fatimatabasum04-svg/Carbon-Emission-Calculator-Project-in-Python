# test_functions.py - Test all database functions

import database as db

print("=" * 50)
print("TESTING DATABASE FUNCTIONS")
print("=" * 50)

# Test 1: Get activity types
print("\n1. Getting activity types...")
activities = db.get_activity_types()
for act in activities[:3]:  # Show first 3
    print(f"   - {act['type_name']} ({act['default_unit']})")

# Test 2: Get user's group (user_id = 1)
print("\n2. Getting user's group...")
group = db.get_user_group(1)
if group:
    print(f"   User is in group: {group['group_name']}")
else:
    print("   User is not in any group")

# Test 3: Calculate weekly emissions for user 1
print("\n3. Calculating weekly emissions...")
weekly_total = db.calculate_total_emissions(1, 'week')
print(f"   User 1 weekly emissions: {weekly_total} kg CO₂")

# Test 4: Get goal status
print("\n4. Getting goal status...")
status = db.get_goal_status(1)
print(f"   Status: {status['message']}")
if 'current' in status:
    print(f"   Current: {status['current']} kg / Goal: {status['goal']} kg")

# Test 5: Get group leaderboard
print("\n5. Getting group leaderboard...")
leaderboard = db.get_group_leaderboard()
if leaderboard:
    for group in leaderboard:
        print(f"   Rank {group['rank']}: {group['group_name']} - {group['success_percentage']}%")

print("\n" + "=" * 50)
print("✅ All tests completed!")
print("=" * 50)