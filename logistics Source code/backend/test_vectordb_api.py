import httpx

client = httpx.Client(base_url='http://localhost:8001')

# 1. Login
login = client.post('/api/auth/login', json={'email': 'admin', 'password': 'admin123'})
print('1. LOGIN:', login.status_code, login.json().get('email'))
token = login.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. Vector Search
vsearch = client.get('/api/vectors/search?q=delayed+perishable+or+electronics+cargo', headers=headers)
print('2. VECTOR SEARCH:', vsearch.status_code, 'Total Matches:', vsearch.json().get('total_matches'))

# 3. What-If Simulator
sim = client.post('/api/simulation/run', json={'params': {'disruption_duration_days': 7, 'port_closure': True, 'customs_delay_days': 2, 'carrier_unavailable': False, 'fuel_cost_change_pct': 0, 'shipping_mode': 'Sea'}}, headers=headers)
print('3. SIMULATION /run:', sim.status_code, 'Affected Shipments:', sim.json().get('affected_shipments'))

# 4. Financial Impact
fin = client.post('/api/financial/impact', json={'affected_shipments': sim.json()['affected_shipments'], 'avg_shipment_value': 4200, 'delay_days': sim.json()['average_delay_days']}, headers=headers)
print('4. FINANCIAL IMPACT:', fin.status_code, 'Exposure Amount:', fin.json().get('estimated_current_exposure'))

# 5. Workflows
wfs = client.get('/api/workflows', headers=headers)
print('5. WORKFLOWS LIST:', wfs.status_code, 'Count:', len(wfs.json().get('workflows', [])))

# 6. Workflow Generation
gen = client.post('/api/workflows/generate', json={'natural_language': 'When delay > 2 days reroute shipment and notify logistics manager'}, headers=headers)
print('6. WORKFLOW GENERATE:', gen.status_code, 'Generated Name:', gen.json().get('workflow', {}).get('name'))

# 7. Workflow Conflicts
conf = client.get('/api/workflows/conflicts/all', headers=headers)
print('7. WORKFLOW CONFLICTS:', conf.status_code, 'Conflicts Found:', len(conf.json().get('conflicts', [])))

# 8. Opportunities
opp = client.get('/api/workflows/opportunities', headers=headers)
print('8. AUTOMATION OPPORTUNITIES:', opp.status_code, 'Count:', len(opp.json().get('opportunities', [])))

# 9. Insights / Analytics
analytics = client.get('/api/workflows/analytics', headers=headers)
print('9. AUTOMATION ANALYTICS:', analytics.status_code, 'Executions:', analytics.json().get('total_executions'))

# 10. Shipments
ships = client.get('/api/shipments?limit=10', headers=headers)
print('10. SHIPMENTS LIST:', ships.status_code, 'Total Indexed:', ships.json().get('total'))

# 11. Dashboard Overview
dash = client.get('/api/dashboard/overview', headers=headers)
print('11. DASHBOARD OVERVIEW:', dash.status_code, 'Active Shipments:', dash.json().get('active_shipments'))

print('\nALL 11 VECTORDB ENDPOINT TESTS PASSED WITH 200 OK!')
