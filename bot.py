import os, requests, re, sys, time as t, json, uuid, hashlib, random, string, threading, base64, sqlite3
from flask import Flask, render_template_string, send_file, jsonify, request
from datetime import datetime
from queue import Queue

app_web = Flask(__name__)

RESET = '\033[0m'
YELLOW = '\033[93m'
RED = '\033[91m'
GREEN = '\033[92m'
CYAN = '\033[96m'
C1 = "\033[1;97;40m"

# TELEGRAM BOT BİLGİLERİ
BOT_TOKEN = "8606497087:AAGk_Q6I_iooMZO3PmmLdCNQnTk-o1QYYVo"
BOT_CHAT_ID = "8188931353"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RINEX Scanner</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0a0a; color: #00ff00; font-family: 'Courier New', monospace; padding: 10px; }
        .container { max-width: 1000px; margin: 0 auto; background: #111; border: 1px solid #00ff00; border-radius: 10px; padding: 15px; }
        .header { text-align: center; border-bottom: 1px solid #00ff00; padding-bottom: 15px; margin-bottom: 15px; }
        .header h1 { color: #ffd700; font-size: 2em; }
        .header p { color: #ff6b6b; font-size: 0.9em; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0; }
        .stat-card { background: #1a1a1a; border: 1px solid #333; border-radius: 5px; padding: 10px; text-align: center; }
        .stat-card .number { font-size: 1.8em; color: #00ff00; font-weight: bold; }
        .stat-card .label { color: #888; font-size: 0.8em; }
        .controls { display: flex; gap: 10px; margin: 15px 0; flex-wrap: wrap; justify-content: center; }
        .btn { background: #00ff00; color: #0a0a0a; border: none; padding: 8px 20px; border-radius: 5px; font-weight: bold; cursor: pointer; text-decoration: none; display: inline-block; font-size: 0.9em; }
        .btn:hover { background: #00cc00; transform: scale(1.02); }
        .btn-download { background: #ffd700; }
        .btn-download:hover { background: #ffcc00; }
        .btn-hide { background: #ff4444; }
        .btn-hide:hover { background: #cc0000; }
        .btn-bot { background: #0088cc; color: white; }
        .btn-bot:hover { background: #006699; }
        .hits-container { margin: 15px 0; max-height: 500px; overflow-y: auto; background: #0a0a0a; border: 1px solid #333; border-radius: 5px; padding: 10px; }
        .hits-container::-webkit-scrollbar { width: 6px; }
        .hits-container::-webkit-scrollbar-track { background: #1a1a1a; }
        .hits-container::-webkit-scrollbar-thumb { background: #00ff00; border-radius: 3px; }
        .hit-item { background: #1a1a1a; border: 1px solid #333; border-radius: 3px; padding: 8px; margin: 3px 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9em; }
        .hit-item:hover { border-color: #00ff00; background: #1f1f1f; }
        .hit-item .username { color: #00ff00; font-weight: bold; }
        .hit-item .year { color: #ffd700; }
        .hit-item .email { color: #4fc3f7; }
        .hit-item .from-bot { color: #0088cc; font-size: 0.7em; margin-left: 5px; }
        .hidden { display: none; }
        .bot-status { background: #1a1a1a; border: 1px solid #0088cc; border-radius: 5px; padding: 10px; margin: 10px 0; color: #0088cc; text-align: center; }
        .bot-status .online { color: #00ff00; }
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
        <div class="bot-status">
            🤖 Bot Status: <span class="online">🟢 ONLINE</span>
            <span style="margin-left:20px;">📨 Bot Hits: <span id="botHits">0</span></span>
        </div>
        <div class="stats">
            <div class="stat-card"><div class="number" id="hits">0</div><div class="label">🎯 Total Hits</div></div>
            <div class="stat-card"><div class="number" id="botHitsCount">0</div><div class="label">🤖 Bot Hits</div></div>
            <div class="stat-card"><div class="number" id="checked">0</div><div class="label">🔍 Checked</div></div>
            <div class="stat-card"><div class="number" id="bad">0</div><div class="label">❌ Bad</div></div>
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
                    <div>
                        <span class="username">@{{ hit.username }}</span>
                        <span class="email">{{ hit.email }}</span>
                        {% if hit.from_bot %}<span class="from-bot">🤖</span>{% endif %}
                    </div>
                    <div>
                        <span class="year">📅 {{ hit.year }}</span>
                        👥 {{ hit.followers }}
                        <a href="https://instagram.com/{{ hit.username }}" target="_blank" style="color:#00ff00;">🔗</a>
                    </div>
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
                    document.getElementById('hits').textContent = data.total_hits || 0;
                    document.getElementById('botHitsCount').textContent = data.bot_hits || 0;
                    document.getElementById('checked').textContent = data.checked || 0;
                    document.getElementById('bad').textContent = data.bad || 0;
                    document.getElementById('botHits').textContent = data.bot_hits || 0;
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
        self._bot_hits = 0
        self._C = 0
        self._BI = 0
        self._BE = 0
        self._found = set()
        self._db_file = "hits.db"
        self._hits_file = "_dabb_hits.log"
        self._token = BOT_TOKEN
        self._cid = BOT_CHAT_ID
        self._running = True
        self._init_db()
        
        # Bot listener başlat
        threading.Thread(target=self._bot_listener, daemon=True).start()
    
    def _init_db(self):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS hits (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         username TEXT,
                         email TEXT,
                         year TEXT,
                         followers INTEGER,
                         posts INTEGER,
                         reset_link TEXT,
                         from_bot INTEGER DEFAULT 0,
                         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
            conn.commit()
            conn.close()
        except:
            pass
    
    def _save_hit(self, username, email, year, followers, from_bot=False):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('''INSERT INTO hits (username, email, year, followers, posts, reset_link, from_bot)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (username, email, year, followers, 0, '', 1 if from_bot else 0))
            conn.commit()
            conn.close()
            
            if from_bot:
                self._bot_hits += 1
            self._H += 1
            
            # TXT'ye kaydet
            with open(self._hits_file, 'a', encoding='utf-8') as f:
                f.write(f"{'BOT' if from_bot else 'SCAN'}: @{username} | {email} | {year}\n")
            
            print(f"{GREEN}[{'BOT' if from_bot else 'HIT'}]{RESET} @{username} | {year}")
            return True
        except:
            return False
    
    def _get_recent_hits(self, limit=100):
        try:
            conn = sqlite3.connect(self._db_file)
            c = conn.cursor()
            c.execute('''SELECT username, email, year, followers, posts, reset_link, from_bot 
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
            c.execute('SELECT username, email, year, followers, posts, reset_link, from_bot FROM hits ORDER BY timestamp DESC')
            rows = c.fetchall()
            conn.close()
            return rows
        except:
            return []
    
    def _get_stats(self):
        return {
            'total_hits': self._H,
            'bot_hits': self._bot_hits,
            'checked': self._C,
            'bad': self._BE + self._BI
        }
    
    def _bot_listener(self):
        """Telegram bot mesajlarını dinle"""
        last_update_id = 0
        print(f"{GREEN}[+] Bot listener başladı{RESET}")
        
        while self._running:
            try:
                url = f"https://api.telegram.org/bot{self._token}/getUpdates"
                r = requests.get(url, params={'offset': last_update_id + 1, 'timeout': 30}, timeout=35)
                data = r.json()
                
                if data.get('ok'):
                    for update in data.get('result', []):
                        last_update_id = update['update_id']
                        msg = update.get('message', {})
                        text = msg.get('text', '')
                        
                        # Hit mesajlarını parse et
                        if text and ('@' in text or 'HIT' in text):
                            self._parse_hit(text)
                        
                        # Komutlar
                        if text == '/stats':
                            self._send_stats(msg)
            except Exception as e:
                print(f"Bot error: {e}")
                t.sleep(5)
    
    def _parse_hit(self, text):
        """Bot mesajından hit bilgilerini çıkar"""
        try:
            lines = text.split('\n')
            username = None
            email = None
            year = None
            followers = 0
            
            for line in lines:
                if '👤' in line:
                    match = re.search(r'@(\w+)', line)
                    if match:
                        username = match.group(1)
                elif '📧' in line:
                    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', line)
                    if match:
                        email = match.group(0)
                elif '📅' in line:
                    match = re.search(r'(\d{4})', line)
                    if match:
                        year = match.group(1)
                elif '👥' in line:
                    match = re.search(r'(\d+)', line)
                    if match:
                        followers = int(match.group(1))
            
            if username and email:
                self._save_hit(username, email, year or 'N/A', followers, from_bot=True)
                print(f"{GREEN}[BOT HIT]{RESET} @{username} | {email}")
        except:
            pass
    
    def _send_stats(self, msg):
        """İstatistik gönder"""
        chat_id = msg.get('chat', {}).get('id')
        stats = self._get_stats()
        response = f"""📊 STATS
━━━━━━━━━━
🎯 Total Hits: {stats['total_hits']}
🤖 Bot Hits: {stats['bot_hits']}
🔍 Checked: {stats['checked']}
❌ Bad: {stats['bad']}
━━━━━━━━━━
@rinexdestek"""
        try:
            requests.post(
                f"https://api.telegram.org/bot{self._token}/sendMessage",
                json={'chat_id': chat_id, 'text': response}
            )
        except:
            pass
    
    def _scan_loop(self):
        """Scanner - user ID çeker"""
        while self._running:
            try:
                # Rastgele ID
                Id = str(random.randint(2500000000, 8597939245))
                
                headers = {
                    'accept': '*/*',
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'content-type': 'application/x-www-form-urlencoded',
                }
                d = {
                    'fb_api_caller_class': 'RelayModern',
                    'fb_api_req_friendly_name': 'PolarisUserHoverCardContentV2Query',
                    'variables': '{"userID":"'+Id+'","username":"cristiano"}',
                    'doc_id': '7717269488336001',
                }
                
                r = requests.post('https://www.instagram.com/api/graphql', headers=headers, data=d, timeout=8)
                
                try:
                    j = r.json()
                    ud = j.get('data', {}).get('user', {})
                    if ud:
                        u = ud.get('username', '')
                        if u and u not in self._found and len(u) >= 8 and '_' not in u:
                            self._found.add(u)
                            self._C += 1
                            # Gmail kontrolü
                            email = u + '@gmail.com'
                            if self._check_gmail(u):
                                self._save_hit(u, email, 'N/A', 0, from_bot=False)
                except:
                    pass
            except:
                pass
    
    def _check_gmail(self, username):
        """Gmail kontrolü - basit"""
        try:
            # Google'a ping at
            r = requests.get(
                f"https://mail.google.com/mail/gxlu?email={username}@gmail.com",
                timeout=5
            )
            if 'gf.uar' in r.text:
                return True
            return False
        except:
            return False
    
    def _stats_loop(self):
        while self._running:
            try:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(f"""{YELLOW}
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
   █                                      
   █    {YELLOW}★BY RİNEX ★ {RESET}
   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
""")
                stats = self._get_stats()
                print(f"""
 ╔══════════════════════════════════════════════╗
 ║  {YELLOW} BY RİNEX LIVE STATS ⚡{C1}              ║
 ╠══════════════════════════════════════════════╣
 ║  🎯 Total Hits   : {RED}{stats['total_hits']}{C1}
 ║  🤖 Bot Hits     : {CYAN}{stats['bot_hits']}{C1}
 ║  🔍 Checked      : {YELLOW}{stats['checked']}{C1}
 ║  ❌ Bad          : {RED}{stats['bad']}{C1}
 ╠══════════════════════════════════════════════╣
 ║  👨 @rinexdestek | ⛓️ @rinexsorgux           ║
 ╚══════════════════════════════════════════════╝
""")
                t.sleep(3)
            except:
                pass
    
    def run(self):
        print(f"{GREEN}[+] Başlatılıyor...{RESET}")
        print(f"{GREEN}[+] Bot Token: {self._token[:10]}...{RESET}")
        print(f"{GREEN}[+] Chat ID: {self._cid}{RESET}")
        
        # Web sunucusu
        threading.Thread(target=self._start_web, daemon=True).start()
        
        # Stats
        threading.Thread(target=self._stats_loop, daemon=True).start()
        
        # Scanner
        for _ in range(20):
            threading.Thread(target=self._scan_loop, daemon=True).start()
        
        print(f"{GREEN}[+] Web: http://0.0.0.0:{os.environ.get('PORT', 5000)}{RESET}")
        print(f"{GREEN}[+] Bot aktif! Hit'leri dinliyor...{RESET}")
        
        while True:
            t.sleep(10)
    
    def _start_web(self):
        port = int(os.environ.get('PORT', 5000))
        app_web.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# Flask Routes
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
            'reset_link': hit[5],
            'from_bot': bool(hit[6]) if len(hit) > 6 else False
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
            'from_bot': bool(hit[6]) if len(hit) > 6 else False
        })
    return jsonify({'hits': hits_list, 'total': len(hits_list)})

@app_web.route('/download/txt')
def download_txt():
    hits = app._get_all_hits()
    content = "RINEX HITS\n" + "="*40 + "\n"
    content += f"Total: {len(hits)}\n\n"
    for hit in hits:
        bot_tag = " [BOT]" if (len(hit) > 6 and hit[6]) else ""
        content += f"@{hit[0]}{bot_tag} | {hit[1]} | {hit[2]} | {hit[3]}\n"
    
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
    .bot{color:#0088cc}
    </style></head><body><h1>HITS</h1><table><tr><th>#</th><th>User</th><th>Email</th><th>Year</th><th>Followers</th><th>Source</th></tr>"""
    for i, h in enumerate(hits, 1):
        source = "🤖 Bot" if (len(h) > 6 and h[6]) else "🔄 Scanner"
        html += f"<tr><td>{i}</td><td>@{h[0]}</td><td>{h[1]}</td><td>{h[2]}</td><td>{h[3]}</td><td>{source}</td></tr>"
    html += "</table></body></html>"
    return html

app = _Core()

if __name__ == '__main__':
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit()
