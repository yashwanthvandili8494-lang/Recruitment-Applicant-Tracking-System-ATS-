"""
Live End-to-End API Integration & RBAC Test Suite.
Tests live endpoints, authentication, role permissions, and full recruitment workflows.
"""

import urllib.request
import json
import sys

BASE_URL = 'http://127.0.0.1:8000/api/v1'

def api_call(path, method='GET', data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f"Bearer {token}"
    req_body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

def run_tests():
    roles = {
        'admin': ('admin@recruitflow.dev', 'Demo1234!'),
        'recruiter': ('recruiter@recruitflow.dev', 'Demo1234!'),
        'manager': ('manager@recruitflow.dev', 'Demo1234!'),
        'interviewer': ('interviewer@recruitflow.dev', 'Demo1234!'),
        'candidate': ('alex@example.com', 'Demo1234!')
    }

    tokens = {}
    print("=" * 60)
    print("1. AUTHENTICATION & LOGIN TESTS")
    print("=" * 60)
    for role, (email, pwd) in roles.items():
        code, res = api_call('/auth/login', method='POST', data={'email': email, 'password': pwd})
        assert code == 200, f"Login failed for {role}: {res}"
        tokens[role] = res['access_token']
        # Check /auth/me
        code_me, me = api_call('/auth/me', token=tokens[role])
        assert code_me == 200, f"/auth/me failed for {role}"
        assert me['email'] == email, f"Email mismatch: {me}"
        print(f"  [PASS] {role.capitalize():<12} logged in ({email}) -> verified as role: {me['role']}")

    # Test invalid login
    code_bad, _ = api_call('/auth/login', method='POST', data={'email': 'admin@recruitflow.dev', 'password': 'WrongPassword!'})
    assert code_bad == 401, f"Expected 401 for wrong password, got {code_bad}"
    print("  [PASS] Invalid password rejected with 401 Unauthorized")

    print("\n" + "=" * 60)
    print("2. PUBLIC CAREERS & JOBS API TESTS")
    print("=" * 60)
    code_pub, pub_jobs = api_call('/jobs/public')
    assert code_pub == 200, f"Public jobs failed: {pub_jobs}"
    total_jobs = pub_jobs.get('total', len(pub_jobs.get('jobs', [])))
    print(f"  [PASS] Public jobs listing returned {total_jobs} open positions")
    first_job_id = pub_jobs['jobs'][0]['id']
    code_detail, job_detail = api_call(f"/jobs/public/{first_job_id}")
    assert code_detail == 200, f"Public job detail failed: {job_detail}"
    print(f"  [PASS] Public job detail fetched: \"{job_detail['title']}\" ({job_detail['department']} - {job_detail['location']})")

    code_staff_job, staff_job = api_call(f"/jobs/{first_job_id}", token=tokens['recruiter'])
    assert code_staff_job == 200, f"Staff job detail failed: {staff_job}"
    print(f"  [PASS] Staff job details fetched with recruiter token")

    print("\n" + "=" * 60)
    print("3. ROLE-BASED ACCESS CONTROL (RBAC) TESTS")
    print("=" * 60)
    # Users endpoint: admin only
    code_admin_users, users_list = api_call('/users', token=tokens['admin'])
    assert code_admin_users == 200, f"Admin should access /users: {users_list}"
    print(f"  [PASS] Admin authorized for /users ({users_list['total']} users in organization)")

    for r in ['recruiter', 'manager', 'interviewer', 'candidate']:
        code_denied, _ = api_call('/users', token=tokens[r])
        assert code_denied == 403, f"{r} should be denied from /users, got {code_denied}"
        print(f"  [PASS] {r.capitalize():<12} correctly denied from /users (403 Forbidden)")

    # Dashboard overview: admin, recruiter, manager only
    for r in ['admin', 'recruiter', 'manager']:
        code_dash, dash = api_call('/dashboard/overview', token=tokens[r])
        assert code_dash == 200, f"{r} should access /dashboard/overview: {dash}"
        print(f"  [PASS] {r.capitalize():<12} authorized for /dashboard/overview (Open Jobs: {dash['total_open_jobs']}, Apps: {dash['total_applications']})")

    for r in ['interviewer', 'candidate']:
        code_dash_denied, _ = api_call('/dashboard/overview', token=tokens[r])
        assert code_dash_denied == 403, f"{r} should be denied from /dashboard/overview, got {code_dash_denied}"
        print(f"  [PASS] {r.capitalize():<12} correctly restricted from /dashboard/overview (403 Forbidden)")

    print("\n" + "=" * 60)
    print("4. INTERVIEWER & CANDIDATE WORKFLOW TESTS")
    print("=" * 60)
    # Interviewer can list their assigned interviews
    code_inv, inv_list = api_call('/interviews', token=tokens['interviewer'])
    assert code_inv == 200, f"Interviewer /interviews failed: {inv_list}"
    print(f"  [PASS] Interviewer accessed assigned interviews ({inv_list['total']} scheduled)")

    # Candidate can list their applications and interviews
    code_c_apps, c_apps = api_call('/applications', token=tokens['candidate'])
    assert code_c_apps == 200, f"Candidate /applications failed: {c_apps}"
    print(f"  [PASS] Candidate accessed /applications ({c_apps['total']} applications submitted)")

    code_c_inv, c_inv = api_call('/interviews', token=tokens['candidate'])
    assert code_c_inv == 200, f"Candidate /interviews failed: {c_inv}"
    print(f"  [PASS] Candidate accessed candidate interviews portal ({c_inv['total']} scheduled)")

    # Recruiter staff endpoints
    code_r_cands, r_cands = api_call('/candidates', token=tokens['recruiter'])
    assert code_r_cands == 200, f"Recruiter /candidates failed: {r_cands}"
    print(f"  [PASS] Recruiter accessed /candidates pipeline ({r_cands['total']} candidates)")

    code_r_offers, r_offers = api_call('/offers', token=tokens['recruiter'])
    assert code_r_offers == 200, f"Recruiter /offers failed: {r_offers}"
    print(f"  [PASS] Recruiter accessed /offers management ({r_offers['total']} offers)")

    print("\n" + "=" * 60)
    print("5. VITE FRONTEND PROXY ENDPOINT TESTS")
    print("=" * 60)
    # Test through Vite proxy on port 5173
    proxy_url = 'http://127.0.0.1:5173/api/v1/jobs/public'
    with urllib.request.urlopen(proxy_url) as resp:
        proxy_data = json.loads(resp.read().decode('utf-8'))
        assert resp.status == 200
        print(f"  [PASS] Frontend Vite reverse proxy (port 5173 -> 8000) active ({proxy_data['total']} jobs)")

    print("\n" + "=" * 60)
    print(">>> ALL 20+ END-TO-END INTEGRATION TESTS PASSED (100%) <<<")
    print("=" * 60)

if __name__ == '__main__':
    run_tests()
