import urllib.request
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_KEY = 'rnd_Qn2kLsTdyIyYTEA2fqTJp4EQbutH'
SVC_ID = 'srv-dadipqn40ujc73bksugg'
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json'
}

print("1. Fetching Render Events...")
req = urllib.request.Request(f'https://api.render.com/v1/services/{SVC_ID}/events?limit=10', headers=HEADERS)
try:
    with urllib.request.urlopen(req) as resp:
        events = json.loads(resp.read().decode('utf-8'))
        for ev in events:
            event_data = ev.get('event', {})
            print(f"  [{event_data.get('timestamp')}] {event_data.get('type')}: {event_data.get('details', '')}")
except urllib.error.HTTPError as e:
    print('Events error:', e.code, e.read().decode('utf-8'))

print("\n2. Fetching Service Deploys...")
req = urllib.request.Request(f'https://api.render.com/v1/services/{SVC_ID}/deploys?limit=3', headers=HEADERS)
try:
    with urllib.request.urlopen(req) as resp:
        deploys = json.loads(resp.read().decode('utf-8'))
        for d in deploys:
            dep = d.get('deploy', {})
            print(f"  Deploy {dep.get('id')} - Status: {dep.get('status')} - Trigger: {dep.get('trigger')} - Commit: {dep.get('commit', {}).get('message')}")
except urllib.error.HTTPError as e:
    print('Deploys error:', e.code, e.read().decode('utf-8'))
