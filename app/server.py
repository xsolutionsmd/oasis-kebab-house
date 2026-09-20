import base64, hashlib, html, json, os, re, secrets, sqlite3, threading, time
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode
from zoneinfo import ZoneInfo
import requests
from cryptography.fernet import Fernet
from flask import Flask, request, jsonify, session, redirect, render_template, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from seed import menu, DEFAULTS

NY=ZoneInfo('America/New_York')
BASE=Path(__file__).parent
class ClosingConnection(sqlite3.Connection):
    def __exit__(self,*args):
        try:return super().__exit__(*args)
        finally:self.close()

def create_app(test_config=None):
    app=Flask(__name__,static_folder='static')
    app.config.update(DATA_DIR=os.getenv('DATA_DIR','/data'),ORIGIN=os.getenv('PUBLIC_ORIGIN','http://127.0.0.1:8789'),OPERATOR_EMAIL=os.getenv('OPERATOR_EMAIL',''),GOOGLE_CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID',''),GOOGLE_CLIENT_SECRET=os.getenv('GOOGLE_CLIENT_SECRET',''),DEMO=os.getenv('DEMO_MODE','true')=='true',MAX_CONTENT_LENGTH=65536,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE='Lax',PERMANENT_SESSION_LIFETIME=timedelta(hours=12))
    if test_config:app.config.update(test_config)
    data=Path(app.config['DATA_DIR']);data.mkdir(parents=True,exist_ok=True)
    for filename,value in [('secret.key',secrets.token_hex(48).encode()),('encryption.key',Fernet.generate_key())]:
        p=data/filename
        try:
            with p.open('xb') as f:f.write(value)
            p.chmod(0o600)
        except FileExistsError:pass
    app.secret_key=(data/'secret.key').read_bytes()
    cipher=Fernet((data/'encryption.key').read_bytes())
    app.config['SESSION_COOKIE_SECURE']=app.config['ORIGIN'].startswith('https:')
    app.wsgi_app=ProxyFix(app.wsgi_app,x_for=1,x_proto=1)
    dbpath=data/'oasis.sqlite3'
    def db():
        c=sqlite3.connect(dbpath,timeout=20,factory=ClosingConnection);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');return c
    app.db=db
    with db() as c:
        c.executescript('''PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS menu(id TEXT PRIMARY KEY,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,token TEXT UNIQUE NOT NULL,request_key TEXT UNIQUE NOT NULL,created INTEGER NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reservations(id INTEGER PRIMARY KEY AUTOINCREMENT,token TEXT UNIQUE NOT NULL,request_key TEXT UNIQUE NOT NULL,created INTEGER NOT NULL,status TEXT NOT NULL,data TEXT NOT NULL,start INTEGER NOT NULL,end INTEGER NOT NULL,guests INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS members(email TEXT PRIMARY KEY,sub TEXT UNIQUE,role TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,version INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS invitations(hash TEXT PRIMARY KEY,email TEXT NOT NULL,role TEXT NOT NULL,expires INTEGER NOT NULL,used INTEGER NOT NULL DEFAULT 0);
        CREATE TABLE IF NOT EXISTS oauth(state TEXT PRIMARY KEY,data TEXT NOT NULL,expires INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS secrets(name TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,created INTEGER NOT NULL,recipient TEXT NOT NULL,subject TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL,error TEXT NOT NULL DEFAULT '',event_key TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY AUTOINCREMENT,created INTEGER NOT NULL,actor TEXT NOT NULL,event TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS limits(key TEXT PRIMARY KEY,count INTEGER NOT NULL,expires INTEGER NOT NULL);
        ''')
        c.execute('INSERT OR IGNORE INTO settings VALUES(1,?)',(json.dumps(DEFAULTS),))
        for item in menu():c.execute('INSERT OR IGNORE INTO menu VALUES(?,?)',(item['id'],json.dumps(item)))
        operator=app.config['OPERATOR_EMAIL'].lower().strip()
        if operator:c.execute("INSERT OR IGNORE INTO members(email,role) VALUES(?,'admin')",(operator,))
        c.execute("UPDATE outbox SET status='uncertain',error='Process restarted during send. Review before retrying.' WHERE status='sending'")
    def settings(c=None):
        if c:return json.loads(c.execute('SELECT data FROM settings WHERE id=1').fetchone()[0])
        with db() as conn:return settings(conn)
    def now():return datetime.now(timezone.utc)
    def err(msg,code=400):return jsonify(error=msg),code
    def actor():
        with db() as c:r=c.execute('SELECT * FROM members WHERE email=? AND active=1',(session.get('email',''),)).fetchone()
        return dict(r) if r and r['version']==session.get('member_version') else None
    def auth(owner=False):
        def deco(fn):
            @wraps(fn)
            def wrapped(*a,**k):
                user=actor()
                if not user:return err('Sign in to continue.',401)
                if owner and user['role']!='admin':return err('Admin access is required.',403)
                return fn(*a,**k)
            return wrapped
        return deco
    def audit(c,text):c.execute('INSERT INTO activity(created,actor,event) VALUES(?,?,?)',(int(time.time()),session.get('email','system'),text))
    @app.before_request
    def guard():
        if request.path.startswith('/api/') and request.method not in ('GET','HEAD','OPTIONS'):
            if request.headers.get('Origin') not in (None,app.config['ORIGIN']):return err('Request origin not allowed.',403)
            supplied=request.headers.get('X-CSRF-Token','')
            if not supplied or not secrets.compare_digest(supplied,session.get('csrf','')):return err('Your session expired. Refresh and try again.',403)
        if request.path in ('/api/orders','/api/reservations','/oauth/start') and request.method in ('POST','GET'):
            bucket=int(time.time())//3600;key=hashlib.sha256(f'{request.remote_addr}:{bucket}:{request.path}'.encode()).hexdigest()
            with db() as c:
                c.execute('DELETE FROM limits WHERE expires<?',(int(time.time()),))
                c.execute('INSERT INTO limits VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',(key,(bucket+1)*3600))
                if c.execute('SELECT count FROM limits WHERE key=?',(key,)).fetchone()[0]>30:return err('Too many requests. Please try again later.',429)
    @app.after_request
    def security(r):
        r.headers['X-Content-Type-Options']='nosniff';r.headers['Referrer-Policy']='same-origin';r.headers['X-Frame-Options']='SAMEORIGIN'
        r.headers['Content-Security-Policy']="default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self'; font-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'self'; base-uri 'self'; form-action 'self' https://accounts.google.com"
        r.headers['X-Robots-Tag']='noindex, nofollow'
        if not request.path.startswith('/static/'):r.headers['Cache-Control']='no-store'
        return r
    @app.errorhandler(413)
    def large(e):return err('Request is too large.',413)
    @app.errorhandler(ValueError)
    def invalid(e):return err(str(e)[:180])
    @app.errorhandler(sqlite3.IntegrityError)
    def conflict(e):return err('That request already exists. Refresh and try again.',409)
    def payload():
        p=request.get_json(silent=True)
        if not isinstance(p,dict):raise ValueError('A valid request is required.')
        return p
    def text(p,key,limit=120,required=True):
        v=p.get(key,'')
        if not isinstance(v,str) or len(v)>limit:raise ValueError(f'Check {key}.')
        v=v.strip()
        if required and not v:raise ValueError(f'Please enter {key}.')
        return v
    def contact(p):
        d={k:text(p,k,n,k!='notes') for k,n in [('name',100),('email',254),('phone',30),('notes',1000)]}
        d['email']=d['email'].lower()
        if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',d['email']):raise ValueError('Enter a valid email address.')
        if len(re.sub(r'\D','',d['phone']))<7:raise ValueError('Enter a valid phone number.')
        return d
    def integer(v,low,high,label):
        if isinstance(v,bool) or not isinstance(v,int) or not low<=v<=high:raise ValueError(f'Check {label}.')
        return v
    def rows(c,table):return [dict(r)|{'data':json.loads(r['data'])} for r in c.execute(f'SELECT * FROM {table} ORDER BY id DESC LIMIT 500')]
    def slot_list(day,kind,guests=1,c=None):
        s=settings(c)
        if not s['accept_orders' if kind=='pickup' else 'accept_reservations']:return []
        try:d=datetime.strptime(day,'%Y-%m-%d').date()
        except (ValueError,TypeError):return []
        local=now().astimezone(NY)
        if d<local.date() or d>local.date()+timedelta(days=s['advance_days']) or day in s['closures']:return []
        hours=s['hours'][d.weekday()]
        if not hours:return []
        start,end=hours;lead=s['pickup_lead' if kind=='pickup' else 'reservation_lead'];interval=s['pickup_interval' if kind=='pickup' else 'reservation_interval']
        duration=s['pickup_cutoff' if kind=='pickup' else 'reservation_duration'];output=[]
        for minute in range(start,end-duration+1,interval):
            t=datetime.combine(d,datetime.min.time(),NY)+timedelta(minutes=minute)
            if t<local+timedelta(minutes=lead):continue
            if kind=='reservation' and c:
                reserved=c.execute("SELECT COALESCE(SUM(guests),0) FROM reservations WHERE status IN ('requested','confirmed') AND start<? AND end>?",(int((t+timedelta(minutes=duration)).timestamp()),int(t.timestamp()))).fetchone()[0]
                if reserved+guests>s['capacity']:continue
            output.append({'value':t.isoformat(),'label':t.strftime('%I:%M %p').lstrip('0')})
        return output
    def validate_slot(value,kind,guests,c):
        try:t=datetime.fromisoformat(value)
        except (TypeError,ValueError):raise ValueError('Choose an available time.')
        if t.tzinfo is None:raise ValueError('Choose an available time.')
        canonical=t.astimezone(NY).isoformat()
        if canonical not in [v['value'] for v in slot_list(t.astimezone(NY).date().isoformat(),kind,guests,c)]:raise ValueError('That time is no longer available. Choose another time.')
        return t.astimezone(NY)
    def email_event(c,table,r,status,event):
        d=json.loads(r['data']);kind='order' if table=='orders' else 'reservation';label={'received':'We received your order','accepted':'Your pickup is confirmed','preparing':'Your order is being prepared','ready':'Your order is ready','collected':'Thank you for visiting Oasis','declined':'An update from Oasis','requested':'We received your table request','confirmed':'Your table is confirmed','cancelled':'Your reservation was cancelled','seated':'Welcome to Oasis'}.get(status,'An update from Oasis')
        url=app.config['ORIGIN']+('/order/' if kind=='order' else '/reservation/')+r['token']
        when=datetime.fromisoformat(d['time']).strftime('%A, %B %d at %I:%M %p')
        details=f"Hi {d['name']},\n\n{label}.\n{when}\n"
        if status in ('received','requested'):details+='Please wait for restaurant confirmation.\n'
        if kind=='order':details+='Pay in the restaurant when you pick up.\n'
        if d.get('update_note'):details+='\n'+d['update_note']+'\n'
        details+=f'\nOasis Uzbek Kebab House\n1430 Reisterstown Rd, Pikesville, MD 21208\n410-777-9700\n\nView {kind}: {url}\n'
        if app.config['DEMO']:details='WEBSITE DEMO — not a real order or reservation.\n\n'+details
        enabled=settings(c)['email_enabled'] and c.execute("SELECT 1 FROM secrets WHERE name='gmail'").fetchone()
        c.execute('INSERT OR IGNORE INTO outbox(created,recipient,subject,body,status,event_key) VALUES(?,?,?,?,?,?)',(int(time.time()),d['email'],('Demo · ' if app.config['DEMO'] else '')+label,details,'pending' if enabled else 'preview',event))
    @app.get('/health')
    def health():
        with db() as c:c.execute('SELECT 1').fetchone()
        return jsonify(status='ok')
    @app.get('/version.json')
    def version():return jsonify(revision=(BASE/'revision.txt').read_text().strip() if (BASE/'revision.txt').exists() else os.getenv('APP_REVISION','development'))
    @app.get('/api/config')
    def config():
        session.setdefault('csrf',secrets.token_urlsafe(32));s=settings()
        return jsonify(csrf=session['csrf'],demo=app.config['DEMO'],today=now().astimezone(NY).date().isoformat(),settings={k:v for k,v in s.items() if k!='email_enabled'},google_ready=bool(app.config['GOOGLE_CLIENT_ID']),email_delivery=bool(s['email_enabled']))
    @app.get('/api/menu')
    def get_menu():
        with db() as c:items=[json.loads(r[0]) for r in c.execute('SELECT data FROM menu')]
        return jsonify(items=items)
    @app.get('/api/slots')
    def slots():
        kind=request.args.get('kind','pickup');guests=int(request.args.get('guests',2));s=settings()
        if kind not in ('pickup','reservation') or not 1<=guests<=s['max_party']:return err('Choose a valid party size.')
        with db() as c:return jsonify(slots=slot_list(request.args.get('date'),kind,guests,c))
    @app.post('/api/orders')
    def order():
        p=payload();d=contact(p);key=text(p,'request_key',80);items=p.get('items')
        if not isinstance(items,list) or not 1<=len(items)<=30:raise ValueError('Add an item to your bag.')
        with db() as c:
            c.execute('BEGIN IMMEDIATE')
            prior=c.execute('SELECT token FROM orders WHERE request_key=?',(key,)).fetchone()
            if prior:return jsonify(token=prior['token'])
            t=validate_slot(p.get('time'),'pickup',1,c);total=0;clean=[]
            for line in items:
                if not isinstance(line,dict):raise ValueError('Check your bag.')
                r=c.execute('SELECT data FROM menu WHERE id=?',(line.get('id',''),)).fetchone()
                if not r:raise ValueError('An item is no longer on the menu.')
                m=json.loads(r[0]);q=integer(line.get('quantity'),1,20,'quantity')
                if not m['available']:raise ValueError(m['name']+' is unavailable.')
                choices=line.get('choices',{})
                if not isinstance(choices,dict):raise ValueError('Check item choices.')
                clean_choices={};extra=0
                for opt in m['options']:
                    value=choices.get(opt['label'])
                    if value not in opt['values']:raise ValueError('Choose '+opt['label'].lower()+' for '+m['name']+'.')
                    clean_choices[opt['label']]=value
                    if value.endswith('(+$1)'):extra+=100
                unit=m['price']+extra;total+=unit*q
                clean.append(dict(id=m['id'],name=m['name'],price=unit,quantity=q,choices=clean_choices))
            tax=(total*settings(c)['tax_bps']+5000)//10000;d.update(items=clean,subtotal=total,tax=tax,total=total+tax,time=t.isoformat(),demo=app.config['DEMO'])
            token=secrets.token_urlsafe(32);cur=c.execute('INSERT INTO orders(token,request_key,created,status,data) VALUES(?,?,?,?,?)',(token,key,int(time.time()),'received',json.dumps(d)));r=c.execute('SELECT * FROM orders WHERE id=?',(cur.lastrowid,)).fetchone();email_event(c,'orders',r,'received',f'order:{r["id"]}:received')
        return jsonify(token=token),201
    @app.post('/api/reservations')
    def reserve():
        p=payload();d=contact(p);key=text(p,'request_key',80)
        with db() as c:
            c.execute('BEGIN IMMEDIATE');prior=c.execute('SELECT token FROM reservations WHERE request_key=?',(key,)).fetchone()
            if prior:return jsonify(token=prior['token'])
            s=settings(c);guests=integer(p.get('guests'),1,s['max_party'],'party size');t=validate_slot(p.get('time'),'reservation',guests,c)
            d.update(time=t.isoformat(),guests=guests,demo=app.config['DEMO']);token=secrets.token_urlsafe(32)
            cur=c.execute('INSERT INTO reservations(token,request_key,created,status,data,start,end,guests) VALUES(?,?,?,?,?,?,?,?)',(token,key,int(time.time()),'requested',json.dumps(d),int(t.timestamp()),int((t+timedelta(minutes=s['reservation_duration'])).timestamp()),guests));r=c.execute('SELECT * FROM reservations WHERE id=?',(cur.lastrowid,)).fetchone();email_event(c,'reservations',r,'requested',f'reservation:{r["id"]}:requested')
        return jsonify(token=token),201
    @app.get('/api/status/<kind>/<token>')
    def status(kind,token):
        table={'order':'orders','reservation':'reservations'}.get(kind)
        if not table or len(token)>60:return err('Not found.',404)
        with db() as c:r=c.execute(f'SELECT id,status,data FROM {table} WHERE token=?',(token,)).fetchone()
        if not r:return err('Not found.',404)
        d=json.loads(r['data']);d.pop('email',None);d.pop('phone',None);d.pop('notes',None);d.pop('name',None)
        return jsonify(id=r['id'],status=r['status'],data=d)
    @app.get('/api/admin/session')
    def admin_session():
        session.setdefault('csrf',secrets.token_urlsafe(32));u=actor()
        return jsonify(user={k:u[k] for k in ('email','role')} if u else None,csrf=session['csrf'],google_ready=bool(app.config['GOOGLE_CLIENT_ID']))
    @app.post('/api/admin/logout')
    def logout():session.clear();return jsonify(ok=True)
    @app.get('/api/admin/data')
    @auth()
    def admin_data():
        with db() as c:
            u=actor();owner=u['role']=='admin';gmail=c.execute("SELECT value FROM secrets WHERE name='gmail'").fetchone()
            sender=json.loads(cipher.decrypt(gmail[0].encode()))['email'] if gmail else None
            return jsonify(orders=rows(c,'orders'),reservations=rows(c,'reservations'),settings=settings(c),members=[dict(r) for r in c.execute('SELECT email,role,active FROM members')] if owner else [],invitations=[dict(r) for r in c.execute('SELECT email,role,expires,used FROM invitations ORDER BY expires DESC LIMIT 100')] if owner else [],outbox=[dict(r) for r in c.execute('SELECT * FROM outbox ORDER BY id DESC LIMIT 100')] if owner else [],sender=sender,demo=app.config['DEMO'])
    transitions={'orders':{'received':['accepted','declined'],'accepted':['preparing','ready','declined'],'preparing':['ready','declined'],'ready':['collected'],'collected':[],'declined':[]},'reservations':{'requested':['confirmed','declined'],'confirmed':['seated','cancelled'],'seated':[],'declined':[],'cancelled':[]}}
    @app.patch('/api/admin/<table>/<int:ident>')
    @auth(True)
    def update_record(table,ident):
        if table not in transitions:return err('Not found.',404)
        p=payload();new=text(p,'status',25)
        with db() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute(f'SELECT * FROM {table} WHERE id=?',(ident,)).fetchone()
            if not r:return err('Not found.',404)
            if new not in transitions[table].get(r['status'],[]):return err('This status change is no longer available.',409)
            d=json.loads(r['data']);d['update_note']=text(p,'note',500,False)
            c.execute(f'UPDATE {table} SET status=?,data=? WHERE id=?',(new,json.dumps(d),ident));r=c.execute(f'SELECT * FROM {table} WHERE id=?',(ident,)).fetchone();email_event(c,table,r,new,f'{table}:{ident}:{new}');audit(c,f'{table} {ident}: {new}')
        return jsonify(ok=True)
    @app.put('/api/admin/menu/<ident>')
    @auth(True)
    def edit_menu(ident):
        p=payload()
        with db() as c:
            r=c.execute('SELECT data FROM menu WHERE id=?',(ident,)).fetchone()
            if not r:return err('Not found.',404)
            m=json.loads(r[0]);m.update(name=text(p,'name',120),description=text(p,'description',500,False),price=integer(p.get('price'),0,100000,'price'))
            if not isinstance(p.get('available'),bool):raise ValueError('Check availability.')
            m['available']=p['available'];c.execute('UPDATE menu SET data=? WHERE id=?',(json.dumps(m),ident));audit(c,'Updated menu item '+ident)
        return jsonify(ok=True)
    @app.put('/api/admin/settings')
    @auth(True)
    def save_settings():
        p=payload();s=settings()
        bounds={'pickup_lead':(5,1440),'pickup_interval':(5,60),'pickup_cutoff':(0,180),'advance_days':(1,30),'reservation_lead':(0,10080),'reservation_duration':(30,240),'reservation_interval':(15,120),'max_party':(1,30),'capacity':(1,500),'tax_bps':(0,2500)}
        for k in bounds:
            if k in p:s[k]=integer(p[k],*bounds[k],k)
        for k in ('accept_orders','accept_reservations','email_enabled'):
            if k in p:
                if not isinstance(p[k],bool):raise ValueError('Check '+k+'.')
                s[k]=p[k]
        if 'hours' in p:
            h=p['hours']
            if not isinstance(h,list) or len(h)!=7:raise ValueError('Enter hours for all seven days.')
            for row in h:
                if row is None:continue
                if not isinstance(row,list) or len(row)!=2:raise ValueError('Check opening hours.')
                integer(row[0],0,1439,'opening time');integer(row[1],1,1440,'closing time')
                if row[0]>=row[1]:raise ValueError('Closing time must follow opening time.')
            s['hours']=h
        if 'closures' in p:
            if not isinstance(p['closures'],list) or len(p['closures'])>100:raise ValueError('Check closed dates.')
            for d in p['closures']:datetime.strptime(d,'%Y-%m-%d')
            s['closures']=p['closures']
        with db() as c:
            if s['email_enabled'] and not c.execute("SELECT 1 FROM secrets WHERE name='gmail'").fetchone():raise ValueError('Connect an email sender first.')
            c.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(s),));audit(c,'Updated settings')
        return jsonify(ok=True)
    @app.post('/api/admin/invitations')
    @auth(True)
    def invite():
        p=payload();email=text(p,'email',254).lower();role=p.get('role','admin')
        if role not in ('admin','viewer') or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',email):raise ValueError('Enter a valid email and role.')
        token=secrets.token_urlsafe(32)
        with db() as c:
            if c.execute('SELECT 1 FROM members WHERE email=? AND active=1',(email,)).fetchone():raise ValueError('This person already has access.')
            c.execute('UPDATE invitations SET used=1 WHERE email=?',(email,));c.execute('INSERT INTO invitations VALUES(?,?,?,?,0)',(hashlib.sha256(token.encode()).hexdigest(),email,role,int(time.time())+86400));audit(c,'Invited '+email)
        return jsonify(url=app.config['ORIGIN']+'/admin/#invite='+token,email=email)
    @app.delete('/api/admin/invitations')
    @auth(True)
    def revoke_invite():
        email=text(payload(),'email',254).lower()
        with db() as c:c.execute('UPDATE invitations SET used=1 WHERE email=?',(email,));audit(c,'Revoked invitation '+email)
        return jsonify(ok=True)
    @app.delete('/api/admin/members')
    @auth(True)
    def remove_member():
        email=text(payload(),'email',254).lower()
        with db() as c:
            r=c.execute('SELECT role FROM members WHERE email=?',(email,)).fetchone()
            if not r or email==session['email']:raise ValueError('You can remove another account, but not your own current account.')
            c.execute('UPDATE members SET active=0,version=version+1 WHERE email=?',(email,));audit(c,'Removed member '+email)
        return jsonify(ok=True)
    @app.post('/api/invite')
    def hold_invite():
        token=text(payload(),'token',80);digest=hashlib.sha256(token.encode()).hexdigest()
        with db() as c:r=c.execute('SELECT email FROM invitations WHERE hash=? AND used=0 AND expires>?',(digest,int(time.time()))).fetchone()
        if not r:return err('This invitation expired or was revoked.',410)
        session['invite']=digest;return jsonify(email=r['email'])
    def oauth_start(purpose='login'):
        if not app.config['GOOGLE_CLIENT_ID']:return redirect('/admin/?error=Google+sign-in+is+not+configured+yet')
        u=actor()
        if purpose=='email' and (not u or u['role']!='admin'):return redirect('/admin/')
        state=secrets.token_urlsafe(32);nonce=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(64);session['oauth_state']=state
        d=dict(nonce=nonce,verifier=verifier,purpose=purpose,actor=u['email'] if u else None,invite=session.get('invite'))
        with db() as c:
            c.execute('DELETE FROM oauth WHERE expires<?',(int(time.time()),));c.execute('INSERT INTO oauth VALUES(?,?,?)',(state,json.dumps(d),int(time.time())+600))
        q=dict(client_id=app.config['GOOGLE_CLIENT_ID'],redirect_uri=app.config['ORIGIN']+'/oauth/callback',response_type='code',scope='openid email'+(' https://www.googleapis.com/auth/gmail.send' if purpose=='email' else ''),state=state,nonce=nonce,code_challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('='),code_challenge_method='S256',prompt='consent' if purpose=='email' else 'select_account')
        if purpose=='email':q.update(access_type='offline',prompt='select_account consent')
        return redirect('https://accounts.google.com/o/oauth2/v2/auth?'+urlencode(q))
    @app.get('/oauth/start')
    def start_oauth():return oauth_start('email' if request.args.get('purpose')=='email' else 'login')
    @app.get('/oauth/callback')
    def callback():
        state=request.args.get('state','')
        if not state or not secrets.compare_digest(state,session.pop('oauth_state','')):return redirect('/admin/?error=Sign-in+expired.+Try+again.')
        with db() as c:
            r=c.execute('SELECT data FROM oauth WHERE state=? AND expires>?',(state,int(time.time()))).fetchone();c.execute('DELETE FROM oauth WHERE state=?',(state,))
        if not r or request.args.get('error'):return redirect('/admin/?error=Sign-in+was+cancelled.+Try+again.')
        d=json.loads(r[0])
        try:
            resp=requests.post('https://oauth2.googleapis.com/token',data=dict(code=request.args.get('code'),client_id=app.config['GOOGLE_CLIENT_ID'],client_secret=app.config['GOOGLE_CLIENT_SECRET'],redirect_uri=app.config['ORIGIN']+'/oauth/callback',grant_type='authorization_code',code_verifier=d['verifier']),timeout=20);resp.raise_for_status();tokens=resp.json()
            identity=id_token.verify_oauth2_token(tokens['id_token'],GoogleRequest(),app.config['GOOGLE_CLIENT_ID'])
            if not identity.get('email_verified') or identity.get('nonce')!=d['nonce']:raise ValueError('Identity could not be verified.')
            email=identity['email'].lower();sub=identity['sub']
            if d['purpose']=='email':
                current=actor()
                if not current or current['email']!=d['actor'] or current['role']!='admin':raise ValueError('Your admin session changed. Reconnect from Emails.')
                if 'https://www.googleapis.com/auth/gmail.send' not in tokens.get('scope','').split():raise ValueError('Email sending permission was not granted.')
                with db() as c:
                    existing=c.execute("SELECT value FROM secrets WHERE name='gmail'").fetchone();old=json.loads(cipher.decrypt(existing[0].encode())) if existing else {}
                    if not tokens.get('refresh_token') and old.get('email')==email:tokens['refresh_token']=old.get('refresh_token')
                    if not tokens.get('refresh_token'):raise ValueError('Reconnect and allow offline email access.')
                    tokens.update(email=email,expires_at=time.time()+tokens.get('expires_in',3600));c.execute("INSERT INTO secrets VALUES('gmail',?) ON CONFLICT(name) DO UPDATE SET value=excluded.value",(cipher.encrypt(json.dumps(tokens).encode()).decode(),));audit(c,'Connected independent email sender')
                return redirect('/admin/?tab=emails')
            with db() as c:
                c.execute('BEGIN IMMEDIATE');member=c.execute('SELECT * FROM members WHERE email=? AND active=1',(email,)).fetchone()
                if not member and d.get('invite'):
                    invitation=c.execute('SELECT * FROM invitations WHERE hash=? AND used=0 AND expires>?',(d['invite'],int(time.time()))).fetchone()
                    if not invitation or invitation['email']!=email:raise ValueError('Use the email address on your invitation.')
                    c.execute('INSERT INTO members(email,sub,role) VALUES(?,?,?) ON CONFLICT(email) DO UPDATE SET sub=excluded.sub,role=excluded.role,active=1,version=version+1',(email,sub,invitation['role']));c.execute('UPDATE invitations SET used=1 WHERE hash=?',(d['invite'],));member=c.execute('SELECT * FROM members WHERE email=?',(email,)).fetchone()
                if not member or (member['sub'] and member['sub']!=sub):raise ValueError('This account has not been invited.')
                c.execute('UPDATE members SET sub=? WHERE email=?',(sub,email))
                session.clear();session.update(email=email,member_version=member['version'],csrf=secrets.token_urlsafe(32));session.permanent=True
        except (ValueError,KeyError,requests.RequestException) as e:
            msg=str(e) if isinstance(e,ValueError) else 'Google sign-in could not finish. Please try again.'
            return redirect('/admin/?'+urlencode({'error':msg[:150]}))
        return redirect('/admin/'+('?tab=emails' if d['purpose']=='email' else ''))
    @app.post('/api/admin/email-test')
    @auth(True)
    def email_test():
        with db() as c:
            if not c.execute("SELECT 1 FROM secrets WHERE name='gmail'").fetchone():raise ValueError('Connect a sender first.')
            c.execute('INSERT INTO outbox(created,recipient,subject,body,status,event_key) VALUES(?,?,?,?,?,?)',(int(time.time()),session['email'],'Oasis · email test','Your Oasis email connection is working. This test was requested from the owner workspace.','pending','test:'+secrets.token_hex(12)))
        return jsonify(ok=True)
    @app.post('/api/admin/email-disconnect')
    @auth(True)
    def disconnect():
        with db() as c:
            c.execute("DELETE FROM secrets WHERE name='gmail'");s=settings(c);s['email_enabled']=False;c.execute('UPDATE settings SET data=? WHERE id=1',(json.dumps(s),));c.execute("UPDATE outbox SET status='cancelled' WHERE status='pending'");audit(c,'Disconnected email sender locally')
        return jsonify(ok=True)
    def drain_outbox():
        with db() as c:
            c.execute('BEGIN IMMEDIATE');r=c.execute("SELECT * FROM outbox WHERE status='pending' ORDER BY id LIMIT 1").fetchone();stored=c.execute("SELECT value FROM secrets WHERE name='gmail'").fetchone()
            if not r or not stored:return
            c.execute("UPDATE outbox SET status='sending' WHERE id=?",(r['id'],))
        state='failed';error='';tokens=json.loads(cipher.decrypt(stored[0].encode()))
        try:
            if tokens.get('expires_at',0)<time.time()+90:
                result=requests.post('https://oauth2.googleapis.com/token',data=dict(client_id=app.config['GOOGLE_CLIENT_ID'],client_secret=app.config['GOOGLE_CLIENT_SECRET'],refresh_token=tokens['refresh_token'],grant_type='refresh_token'),timeout=20);result.raise_for_status();fresh=result.json();tokens.update(access_token=fresh['access_token'],expires_at=time.time()+fresh.get('expires_in',3600))
                with db() as c:c.execute("UPDATE secrets SET value=? WHERE name='gmail'",(cipher.encrypt(json.dumps(tokens).encode()).decode(),))
            message=EmailMessage();message['From']=f"Oasis Uzbek Kebab House <{tokens['email']}>";message['To']=r['recipient'];message['Subject']=r['subject'];message['Message-ID']=f'<oasis-{r["id"]}@{app.config["ORIGIN"].split("//")[-1]}>';message.set_content(r['body'])
            safe=html.escape(r['body']).replace('\n','<br>');message.add_alternative(f'<html><body style="background:#031720;padding:30px;color:#f5ecdc;font:16px Georgia"><div style="max-width:560px;margin:auto;padding:35px;border:1px solid #b28b4e;border-radius:14px"><h1 style="color:#d2af73">Oasis</h1><h2>{html.escape(r["subject"])}</h2><p style="line-height:1.8">{safe}</p></div></body></html>',subtype='html')
            try:result=requests.post('https://gmail.googleapis.com/gmail/v1/users/me/messages/send',headers={'Authorization':'Bearer '+tokens['access_token']},json={'raw':base64.urlsafe_b64encode(message.as_bytes()).decode()},timeout=20)
            except requests.RequestException:
                state='uncertain';raise
            if result.ok:state='sent'
            elif result.status_code>=500:state='uncertain';error='Provider response uncertain. Review before retrying.'
            else:error='Google rejected delivery. Reconnect the sender or check the recipient.'
        except (requests.RequestException,ValueError,KeyError):error='Email could not be delivered. Review the connection; no automatic duplicate retry.'
        with db() as c:c.execute('UPDATE outbox SET status=?,error=? WHERE id=?',(state,error,r['id']))
    app.drain_outbox=drain_outbox
    @app.get('/robots.txt')
    def robots():return 'User-agent: *\nDisallow: /\n',200,{'Content-Type':'text/plain'}
    @app.get('/')
    @app.get('/menu')
    @app.get('/gallery')
    @app.get('/visit')
    @app.get('/reserve')
    @app.get('/checkout')
    @app.get('/privacy')
    @app.get('/order/<token>')
    @app.get('/reservation/<token>')
    @app.get('/admin/')
    def page(token=None):
        titles={'/':'Oasis Uzbek Kebab House','/menu':'Menu · Oasis','/gallery':'Gallery · Oasis','/visit':'Visit · Oasis','/reserve':'Reserve a table · Oasis','/checkout':'Pickup checkout · Oasis','/privacy':'Privacy · Oasis','/admin/':'Owner workspace · Oasis'}
        return render_template('index.html',title=titles.get(request.path,'Your request · Oasis'),origin=app.config['ORIGIN'],canonical=app.config['ORIGIN']+request.path)
    return app

if __name__=='__main__':
    app=create_app()
    app.run(host='0.0.0.0',port=8080,debug=False)
