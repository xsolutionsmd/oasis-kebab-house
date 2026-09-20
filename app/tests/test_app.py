import hashlib,json,time,uuid
from datetime import datetime,timedelta
from urllib.parse import urlparse,parse_qs
import pytest
import server

@pytest.fixture
def app(tmp_path):return server.create_app({'TESTING':True,'DATA_DIR':str(tmp_path),'OPERATOR_EMAIL':'first@example.test','GOOGLE_CLIENT_ID':'test-client','GOOGLE_CLIENT_SECRET':'test-secret'})
@pytest.fixture
def client(app):return app.test_client()
def csrf(c):return {'X-CSRF-Token':c.get('/api/config').json['csrf']}
def login(c,email='first@example.test',version=1):
    with c.session_transaction() as s:s.update(email=email,member_version=version,csrf='test-csrf')
    return {'X-CSRF-Token':'test-csrf'}
def slot(c,kind='pickup',guests=2):
    day=(datetime.now(server.NY)+timedelta(days=1)).date().isoformat()
    return c.get(f'/api/slots?kind={kind}&date={day}&guests={guests}').json['slots'][0]['value']
def order_body(c):return dict(name='Test Guest',email='guest@example.test',phone='4105550100',notes='',time=slot(c),request_key=str(uuid.uuid4()),items=[dict(id='samarkand-plov',quantity=2,price=1,choices={})])
def test_all_pages_and_media(client):
    for p in ['/','/menu','/reserve','/visit','/gallery','/checkout','/admin/','/privacy','/health','/version.json']:
        r=client.get(p);assert r.status_code==200;assert 'noindex' in r.headers['X-Robots-Tag']
    assert len(client.get('/api/menu').json['items'])>=70
    assert 'script-src \'self\'' in client.get('/').headers['Content-Security-Policy']
def test_order_price_is_server_owned_and_idempotent(client,app):
    h=csrf(client);p=order_body(client);r=client.post('/api/orders',json=p,headers=h);assert r.status_code==201
    assert client.post('/api/orders',json=p,headers=h).json['token']==r.json['token']
    status=client.get('/api/status/order/'+r.json['token']).json
    assert status['data']['total']==3600 and 'email' not in status['data']
    with app.db() as c:assert c.execute('SELECT COUNT(*) FROM orders').fetchone()[0]==1;assert c.execute('SELECT status FROM outbox').fetchone()[0]=='preview'
def test_csrf_origin_and_unauthenticated_writes(client):
    assert client.post('/api/orders',json={}).status_code==403
    h=csrf(client);assert client.post('/api/orders',json={},headers=h|{'Origin':'https://evil.test'}).status_code==403
    assert client.get('/api/admin/data').status_code==401
    assert client.put('/api/admin/settings',json={},headers=h).status_code==401
def test_unavailable_and_required_options(client,app):
    h=csrf(client);p=order_body(client);p['items']=[dict(id='manti',quantity=1,choices={})]
    assert client.post('/api/orders',json=p,headers=h).status_code==400
    p['items'][0]['choices']={'Filling':'Pumpkin'}
    assert client.post('/api/orders',json=p,headers=h).status_code==201
    with app.db() as c:
        item=json.loads(c.execute("SELECT data FROM menu WHERE id='samarkand-plov'").fetchone()[0]);item['available']=False;c.execute("UPDATE menu SET data=? WHERE id='samarkand-plov'",(json.dumps(item),))
    assert client.post('/api/orders',json=order_body(client),headers=h).status_code==400
def test_time_lead_closed_and_invalid(client):
    p=order_body(client);h=login(client)
    assert client.put('/api/admin/settings',json={'accept_orders':False},headers=h).status_code==200
    assert client.post('/api/orders',json=p,headers=h).status_code==400
    assert client.put('/api/admin/settings',json={'pickup_lead':-1},headers=h).status_code==400
    assert client.get('/api/slots?date=2020-01-01').json['slots']==[]
def test_capacity_and_overlapping_slots(client,app):
    h=login(client);client.put('/api/admin/settings',json={'capacity':4},headers=h)
    p=order_body(client);p.pop('items');p.update(guests=3,time=slot(client,'reservation',3))
    assert client.post('/api/reservations',json=p,headers=h).status_code==201
    p['request_key']=str(uuid.uuid4());p['guests']=2
    assert client.post('/api/reservations',json=p,headers=h).status_code==400
    p['guests']=1;assert client.post('/api/reservations',json=p,headers=h).status_code==201
    with app.db() as c:assert c.execute('SELECT SUM(guests) FROM reservations').fetchone()[0]==4
def test_employee_cannot_change_admin_configuration(client,app):
    with app.db() as c:c.execute("INSERT INTO members(email,role) VALUES('viewer@example.test','viewer')")
    h=login(client,'viewer@example.test');assert client.get('/api/admin/data').status_code==200
    for method,url,p in [('put','/api/admin/settings',{}),('post','/api/admin/invitations',{'email':'new@example.test'}),('delete','/api/admin/members',{'email':'first@example.test'}),('post','/api/admin/email-disconnect',{})]:assert getattr(client,method)(url,json=p,headers=h).status_code==403
def test_any_admin_can_remove_original_and_revokes_session(client,app):
    h=login(client);other=app.test_client()
    with app.db() as c:c.execute("INSERT INTO members(email,role) VALUES('second@example.test','admin')");c.execute("INSERT INTO secrets VALUES('gmail','independent-sender-marker')")
    h2=login(other,'second@example.test');assert other.delete('/api/admin/members',json={'email':'first@example.test'},headers=h2).status_code==200
    assert client.get('/api/admin/data').status_code==401
    with app.db() as c:assert c.execute("SELECT value FROM secrets WHERE name='gmail'").fetchone()[0]=='independent-sender-marker'
    assert other.delete('/api/admin/members',json={'email':'second@example.test'},headers=h2).status_code==400
@pytest.mark.parametrize('role',['admin','viewer'])
def test_invite_roles_expiry_and_revocation(client,app,role):
    h=login(client);r=client.post('/api/admin/invitations',json={'email':'new@example.test','role':role},headers=h);assert r.status_code==200
    token=r.json['url'].split('#invite=')[1];new=app.test_client();nh=csrf(new)
    assert new.post('/api/invite',json={'token':token},headers=nh).json['email']=='new@example.test'
    client.delete('/api/admin/invitations',json={'email':'new@example.test'},headers=h)
    assert new.post('/api/invite',json={'token':token},headers=nh).status_code==410
def mock_oauth(monkeypatch,email,nonce,scope='openid email'):
    class Response:
        def raise_for_status(self):pass
        def json(self):return dict(id_token='mock',refresh_token='refresh',access_token='access',scope=scope)
    monkeypatch.setattr(server.requests,'post',lambda *a,**k:Response())
    monkeypatch.setattr(server.id_token,'verify_oauth2_token',lambda *a,**k:dict(email=email,email_verified=True,nonce=nonce,sub='sub-'+email))
def oauth_state(c):
    r=c.get('/oauth/start');q=parse_qs(urlparse(r.location).query);return q['state'][0],q['nonce'][0]
def test_invite_must_match_email_and_accepts_correct_account(client,app,monkeypatch):
    h=login(client);r=client.post('/api/admin/invitations',json={'email':'new@example.test','role':'viewer'},headers=h);token=r.json['url'].split('#invite=')[1]
    new=app.test_client();new.post('/api/invite',json={'token':token},headers=csrf(new));state,nonce=oauth_state(new)
    mock_oauth(monkeypatch,'wrong@example.test',nonce);r=new.get('/oauth/callback?state='+state+'&code=code');assert 'error=' in r.location
    state,nonce=oauth_state(new);mock_oauth(monkeypatch,'new@example.test',nonce);assert new.get('/oauth/callback?state='+state+'&code=code').location=='/admin/'
    assert new.get('/api/admin/session').json['user']==dict(email='new@example.test',role='viewer')
def test_email_sender_does_not_change_login_or_create_member(client,app,monkeypatch):
    h=login(client);q=parse_qs(urlparse(client.get('/oauth/start?purpose=email').location).query)
    mock_oauth(monkeypatch,'sender@example.test',q['nonce'][0],'openid email https://www.googleapis.com/auth/gmail.send')
    r=client.get('/oauth/callback?state='+q['state'][0]+'&code=code');assert r.location=='/admin/?tab=emails'
    assert client.get('/api/admin/session').json['user']['email']=='first@example.test'
    d=client.get('/api/admin/data').json;assert d['sender']=='sender@example.test';assert len(d['members'])==1
    assert client.post('/api/admin/email-disconnect',json={},headers=h).status_code==200
    assert client.get('/api/admin/session').json['user']['email']=='first@example.test'
def test_no_sending_without_connection_and_status_updates(client,app):
    h=csrf(client);r=client.post('/api/orders',json=order_body(client),headers=h)
    h=login(client);assert client.put('/api/admin/settings',json={'email_enabled':True},headers=h).status_code==400
    ident=client.get('/api/status/order/'+r.json['token']).json['id']
    assert client.patch('/api/admin/orders/'+str(ident),json={'status':'ready'},headers=h).status_code==409
    assert client.patch('/api/admin/orders/'+str(ident),json={'status':'accepted','note':'See you soon'},headers=h).status_code==200
    with app.db() as c:assert c.execute('SELECT COUNT(*) FROM outbox').fetchone()[0]==2
def test_oauth_wrong_state_rejected(client):assert 'error=' in client.get('/oauth/callback?state=forged&code=fake').location
def test_persistence(tmp_path):
    a=server.create_app({'TESTING':True,'DATA_DIR':str(tmp_path),'OPERATOR_EMAIL':'first@example.test'});c=a.test_client();p=order_body(c);r=c.post('/api/orders',json=p,headers=csrf(c));a2=server.create_app({'TESTING':True,'DATA_DIR':str(tmp_path)});assert a2.test_client().get('/api/status/order/'+r.json['token']).status_code==200


def test_employee_manages_customer_requests_only(client,app):
    h=csrf(client);p=order_body(client)
    token=client.post('/api/orders',json=p,headers=h).json['token']
    r=dict(p);r.pop('items');r.update(request_key=str(uuid.uuid4()),guests=2,time=slot(client,'reservation'))
    reservation=client.post('/api/reservations',json=r,headers=h).json['token']
    with app.db() as c:c.execute("INSERT INTO members(email,role) VALUES('employee@example.test','viewer')")
    employee=app.test_client();eh=login(employee,'employee@example.test')
    for table,kind,tok,statuses in [('orders','order',token,['accepted','preparing','ready','collected']),('reservations','reservation',reservation,['confirmed','seated'])]:
        ident=client.get('/api/status/'+kind+'/'+tok).json['id']
        assert client.patch(f'/api/admin/{table}/{ident}',json={'status':statuses[0]},headers=h).status_code==401
        for status in statuses:
            result=employee.patch(f'/api/admin/{table}/{ident}',json={'status':status,'note':'Employee customer update'},headers=eh)
            assert result.status_code==200
            assert client.get('/api/status/'+kind+'/'+tok).json['status']==status
        assert employee.patch(f'/api/admin/{table}/{ident}',json={'status':statuses[0]},headers=eh).status_code==409
    data=employee.get('/api/admin/data').json
    assert data['members']==[] and data['invitations']==[] and data['outbox']==[]
    assert employee.put('/api/admin/menu/samarkand-plov',json={},headers=eh).status_code==403
    with app.db() as c:
        assert c.execute("SELECT count(*) FROM activity WHERE actor='employee@example.test'").fetchone()[0]==6
        assert c.execute('SELECT count(*) FROM outbox').fetchone()[0]==8

def test_admin_is_direct_access_only(client):
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):super().__init__();self.hrefs=[]
        def handle_starttag(self,tag,attrs):
            if tag=='a':self.hrefs.extend(v for k,v in attrs if k=='href')
    for route in ['/','/menu','/gallery','/visit','/reserve','/checkout','/privacy']:
        links=Links();links.feed(client.get(route).text)
        assert not any(h.startswith('/admin') for h in links.hrefs)
    assert client.get('/admin',follow_redirects=True).status_code==200
