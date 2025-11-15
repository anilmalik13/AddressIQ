#!/usr/bin/env python3
"""Check why files weren't cleaned up"""

from database.job_manager import job_manager
from datetime import datetime

print("=" * 60)
print("CLEANUP INVESTIGATION")
print("=" * 60)

# Get all jobs
all_jobs = job_manager.get_jobs(limit=1000)
print(f"\n📊 Total jobs in database: {len(all_jobs)}")

# Get expired jobs
expired_jobs = job_manager.get_expired_jobs()
print(f"⏰ Expired jobs: {len(expired_jobs)}")

# Check retention days
print(f"📅 Retention days: {job_manager.retention_days}")

# Show all jobs with their expiration status
print("\n" + "=" * 60)
print("ALL JOBS IN DATABASE:")
print("=" * 60)

if all_jobs:
    for job in all_jobs:
        job_id = job['job_id']
        output_file = job.get('output_file', 'N/A')
        expires_at = job.get('expires_at', 'Never')
        status = job.get('status', 'unknown')
        created_at = job.get('created_at', 'unknown')
        
        # Parse expiration
        is_expired = False
        if expires_at and expires_at != 'Never':
            try:
                exp_time = datetime.fromisoformat(expires_at)
                now = datetime.utcnow()
                is_expired = exp_time < now
                days_diff = (now - exp_time).days if is_expired else (exp_time - now).days
                exp_status = f"{'EXPIRED' if is_expired else 'Valid'} ({days_diff}d {'ago' if is_expired else 'left'})"
            except:
                exp_status = expires_at
        else:
            exp_status = "No expiration"
        
        print(f"\nJob: {job_id}")
        print(f"  File: {output_file}")
        print(f"  Status: {status}")
        print(f"  Created: {created_at}")
        print(f"  Expires: {exp_status}")
        print(f"  {'🔴 SHOULD BE DELETED' if is_expired else '🟢 STILL VALID'}")
else:
    print("No jobs found in database!")

print("\n" + "=" * 60)
print("EXPIRED JOBS DETAILS:")
print("=" * 60)

if expired_jobs:
    for job in expired_jobs:
        print(f"\nJob: {job['job_id']}")
        print(f"  Output: {job.get('output_file', 'N/A')}")
        print(f"  Expires: {job.get('expires_at', 'N/A')}")
else:
    print("No expired jobs found!")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)

if len(expired_jobs) == 0:
    print("✅ No expired jobs in database")
    print("⚠️  Files in outbound/ may be orphaned (no database records)")
    print("   These files exist but have no job records pointing to them")
else:
    print(f"⚠️  {len(expired_jobs)} expired jobs found but files still exist")
    print("   Cleanup job may not have run yet or failed")
