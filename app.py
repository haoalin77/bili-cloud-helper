#!/usr/bin/env python3
"""云端弹幕库轮播模拟器：只生成测试记录，不向 B 站或其他平台发送网络消息。"""
import json
import os
import random
import secrets
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(os.environ.get('PORT', '8080'))
TOKEN = os.environ.get('ADMIN_TOKEN') or secrets.token_urlsafe(18)
DATA_DIR = Path(os.environ.get('DATA_DIR', '.'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_PATH = DATA_DIR / 'settings.json'

DEFAULT_MESSAGES = [
    '测试弹幕：大家好', '测试弹幕：正在检查消息库', '测试弹幕：画面正常',
    '测试弹幕：听得到声音', '测试弹幕：欢迎来到测试房间',
    '测试弹幕：这是自动生成的模拟记录', '测试弹幕：检测随机间隔',
    '测试弹幕：记录时间戳', '测试弹幕：日志展示正常',
    '测试弹幕：只在本页面模拟，不发送至平台',
]
DEFAULT = {'interval': 3.0, 'jitter': 15, 'room': '模拟测试房间', 'messages': DEFAULT_MESSAGES}


def load_settings():
    try:
        data = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
        return validate(data)
    except Exception:
        return dict(DEFAULT)


def validate(data):
    if not isinstance(data, dict):
        raise ValueError('参数格式不正确')
    interval = float(data.get('interval', 3.0))
    jitter = float(data.get('jitter', 15))
    room = str(data.get('room', '模拟测试房间')).strip()[:80]
    messages = data.get('messages', DEFAULT_MESSAGES)
    if not 0.2 <= interval <= 3600:
        raise ValueError('基础间隔必须在 0.2～3600 秒之间')
    if not 0 <= jitter <= 100:
        raise ValueError('随机浮动必须在 0～100% 之间')
    if not isinstance(messages, list):
        raise ValueError('弹幕库必须是列表')
    messages = [str(x).strip()[:250] for x in messages if str(x).strip()]
    if not 1 <= len(messages) <= 200:
        raise ValueError('弹幕库需要包含 1～200 行非空文字')
    return {'interval': interval, 'jitter': jitter, 'room': room or '模拟测试房间', 'messages': messages}


class Engine:
    def __init__(self):
        self.lock = threading.RLock()
        self.settings = load_settings()
        self.running = False
        self.start_time = None
        self.next_at = None
        self.count = 0
        self.previous = None
        self.logs = deque(maxlen=250)
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def save(self):
        tmp = SETTINGS_PATH.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.settings, ensure_ascii=False, indent=2), encoding='utf-8')
        tmp.replace(SETTINGS_PATH)

    def select_message(self):
        pool = self.settings['messages']
        choices = [x for x in pool if x != self.previous]
        message = random.choice(choices or pool)
        self.previous = message
        return message

    def generate(self):
        message = self.select_message()
        self.count += 1
        self.logs.appendleft({
            'number': self.count,
            'time': datetime.now().astimezone().isoformat(timespec='seconds'),
            'room': self.settings['room'],
            'message': message,
            'mode': '仅模拟，未发送至 B 站',
        })

    def schedule(self):
        s = self.settings
        factor = random.uniform(1 - s['jitter'] / 100, 1 + s['jitter'] / 100)
        self.next_at = time.monotonic() + max(0.1, s['interval'] * factor)

    def loop(self):
        while True:
            with self.lock:
                if self.running and self.next_at is not None and time.monotonic() >= self.next_at:
                    self.generate()
                    self.schedule()
            time.sleep(0.08)

    def state(self):
        with self.lock:
            return {
                'running': self.running,
                'count': self.count,
                'elapsed_seconds': round(time.monotonic() - self.start_time, 1) if self.running and self.start_time else 0,
                'next_in': round(max(0, self.next_at - time.monotonic()), 2) if self.running and self.next_at else None,
                'settings': self.settings,
                'logs': list(self.logs),
                'notice': '这里的弹幕是纯模拟日志，不会发布到任何真实直播间。',
            }


engine = Engine()
HTML = r'''<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>云端弹幕模拟实验室</title><style>
:root{color-scheme:dark;font-family:system-ui,-apple-system,'Microsoft YaHei',sans-serif}
*{box-sizing:border-box}body{margin:0;background:#0d111b;color:#eaf1ff}main{max-width:1080px;margin:34px auto;padding:0 16px}
h1{font-size:29px;margin:0 0 8px}.sub{color:#9caec9;line-height:1.6;margin-bottom:22px}
.pill{display:inline-block;border:1px solid #3d5975;color:#a6cafa;border-radius:50px;padding:4px 10px;font-size:12px;margin-bottom:10px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:#171f2d;border:1px solid #29374e;border-radius:14px;padding:20px;margin-bottom:16px}
h2{font-size:17px;margin:0 0 14px}.inputrow{display:grid;grid-template-columns:1fr 1fr;gap:12px}
label{display:block;color:#afbed4;font-size:13px;margin-bottom:13px}input,textarea{display:block;margin-top:6px;width:100%;padding:11px;border:1px solid #40516b;border-radius:8px;color:white;background:#0c1422;font:inherit}
textarea{resize:vertical;min-height:210px;line-height:1.6}button{background:#427bf5;border:0;border-radius:8px;color:white;padding:11px 16px;cursor:pointer;font:inherit;font-weight:600}
button.secondary{background:#344154}button.danger{background:#b4505b}button:disabled{opacity:.45;cursor:not-allowed}
.actions{display:flex;flex-wrap:wrap;gap:8px}.stats{display:flex;gap:25px;flex-wrap:wrap;margin:8px 0 15px}.stat b{font-size:27px;display:block}.stat small{color:#aebed2}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:#8792a4;margin-right:7px}.dot.active{background:#3ddd9e}
.log{max-height:320px;overflow:auto}.item{padding:10px 0;border-bottom:1px solid #304052}.item small{color:#93a6c3}.item p{margin:6px 0}.msg{font-size:13px;color:#aac0db;min-height:22px}
.warn{border:1px solid #8b6437;background:#3b2e20;padding:13px 14px;border-radius:10px;color:#ffdca9;margin:12px 0 22px}
@media(max-width:740px){.grid,.inputrow{grid-template-columns:1fr}main{margin:20px auto}h1{font-size:23px}}
</style></head><body><main><span class="pill">云端部署 · 演示环境</span>
<h1>🎛️ 云端弹幕模拟实验室</h1><p class="sub">从本地弹幕库随机抽取文本、按间隔生成记录，并通过网页远程控制。网页关闭后，只要云端进程持续运行，模拟任务仍可继续。</p>
<div class="warn">⚠️ 这是<strong>模拟器</strong>：只在本站生成日志，不连接 B 站、不登录账号、不发送真实弹幕，也不计入任何红包或互动活动。</div>
<div class="grid"><div class="card"><h2>⚙️ 参数设置</h2>
<label>管理口令（设置云平台环境变量 ADMIN_TOKEN）<input id="token" type="password" placeholder="输入管理口令" autocomplete="off"/></label>
<label>模拟房间名<input id="room" value="模拟测试房间" maxlength="80"/></label>
<div class="inputrow"><label>基础间隔（秒）<input id="interval" type="number" min="0.2" max="3600" step="0.1" value="3"/></label>
<label>随机浮动（%）<input id="jitter" type="number" min="0" max="100" step="1" value="15"/></label></div>
<label>弹幕库（每行一条，最多 200 条）<textarea id="messages"></textarea></label>
<div class="actions"><button onclick="save()">保存设置</button><button class="secondary" onclick="copyRandom()">随机抽一条并复制</button></div></div>
<div class="card"><h2>▶️ 模拟任务</h2><p><span id="dot" class="dot"></span><span id="state">未运行</span></p>
<div class="stats"><div class="stat"><b id="count">0</b><small>模拟生成条数</small></div><div class="stat"><b id="elapsed">0</b><small>本次运行秒数</small></div><div class="stat"><b id="next">—</b><small>距离下次生成（秒）</small></div></div>
<div class="actions"><button onclick="action('start')">开始自动模拟</button><button class="danger" onclick="action('stop')">停止</button><button class="secondary" onclick="action('once')">模拟一条</button></div>
<p class="msg" id="result"></p><h2>🧾 最近模拟记录</h2><div class="log" id="logs">尚无记录</div>
<div class="actions" style="margin-top:15px"><button class="secondary" onclick="exportCSV()">导出 CSV</button></div></div></div>
<p class="sub" style="font-size:12px">提示：若服务器重启，运行状态和计数清零。可设置 DATA_DIR 为挂载磁盘路径，以便持久化保存参数；免费云服务可能休眠或重启。</p>
</main><script>
let initialized=false;let latest={logs:[]};document.getElementById('token').value=sessionStorage.getItem('demo_admin_token')||'';
function secret(){const v=document.getElementById('token').value.trim();sessionStorage.setItem('demo_admin_token',v);return v}
function fail(e){document.getElementById('result').textContent=String(e.message||e)}
async function request(path,data){const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Admin-Token':secret()},body:JSON.stringify(data||{})});const j=await r.json();if(!r.ok)throw Error(j.error||'请求失败');return j}
function settings(){return {room:document.getElementById('room').value,interval:parseFloat(document.getElementById('interval').value),jitter:parseFloat(document.getElementById('jitter').value),messages:document.getElementById('messages').value.split('\n').map(s=>s.trim()).filter(Boolean)}}
async function save(){try{await request('/api/settings',settings());document.getElementById('result').textContent='✅ 设置已保存';await refresh()}catch(e){fail(e)}}
async function action(name){try{await request('/api/'+name);document.getElementById('result').textContent='✅ 操作成功（仅模拟）';await refresh()}catch(e){fail(e)}}
function escapeHTML(v){return String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function refresh(){try{const r=await fetch('/api/status');const v=await r.json();latest=v;document.getElementById('count').textContent=v.count;document.getElementById('elapsed').textContent=v.elapsed_seconds;document.getElementById('next').textContent=v.next_in??'—';document.getElementById('state').textContent=v.running?'正在自动模拟':'已停止';document.getElementById('dot').className='dot'+(v.running?' active':'');
if(!initialized){initialized=true;document.getElementById('interval').value=v.settings.interval;document.getElementById('jitter').value=v.settings.jitter;document.getElementById('room').value=v.settings.room;document.getElementById('messages').value=v.settings.messages.join('\n')}
document.getElementById('logs').innerHTML=v.logs.length?v.logs.map(x=>`<div class="item"><small>#${x.number} · ${escapeHTML(x.time)} · 模拟</small><p>${escapeHTML(x.message)}</p></div>`).join(''):'尚无记录';}catch(e){fail(e)}}
async function copyRandom(){const p=settings().messages;if(!p.length){fail(new Error('弹幕库不能为空'));return}const m=p[Math.floor(Math.random()*p.length)];try{await navigator.clipboard.writeText(m);document.getElementById('result').textContent='✅ 已复制：'+m}catch(e){document.getElementById('result').textContent='抽到的文本：'+m}}
function exportCSV(){const lines=[['序号','时间','房间','消息','模式'],...latest.logs.map(x=>[x.number,x.time,x.room,x.message,x.mode])];const csv='\uFEFF'+lines.map(row=>row.map(x=>'"'+String(x).replace(/"/g,'""')+'"').join(',')).join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='模拟弹幕日志.csv';a.click();URL.revokeObjectURL(url)}
refresh();setInterval(refresh,1200);
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _send(self, data, status=200, content_type='application/json; charset=utf-8'):
        payload = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == '/':
            return self._send(HTML.encode('utf-8'), content_type='text/html; charset=utf-8')
        if self.path == '/api/status':
            return self._send(engine.state())
        if self.path == '/health':
            return self._send({'ok': True})
        self._send({'error': '未找到'}, 404)

    def do_POST(self):
        if not secrets.compare_digest(self.headers.get('X-Admin-Token', ''), TOKEN):
            return self._send({'error': '管理口令不正确，请检查 ADMIN_TOKEN'}, 401)
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if length > 100_000:
                return self._send({'error': '请求内容过大'}, 413)
            body = json.loads(self.rfile.read(length) or b'{}')
            with engine.lock:
                if self.path == '/api/settings':
                    engine.settings = validate(body)
                    engine.save()
                    if engine.running:
                        engine.schedule()
                elif self.path == '/api/start':
                    if not engine.running:
                        engine.running = True
                        engine.start_time = time.monotonic()
                        engine.schedule()
                elif self.path == '/api/stop':
                    engine.running = False
                    engine.next_at = None
                elif self.path == '/api/once':
                    engine.generate()
                else:
                    return self._send({'error': '未找到'}, 404)
            return self._send({'ok': True})
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._send({'error': str(exc)}, 400)
        except Exception:
            return self._send({'error': '服务器内部错误'}, 500)

    def log_message(self, fmt, *args):
        if not self.path.startswith('/api/status'):
            super().log_message(fmt, *args)


if __name__ == '__main__':
    print('云端弹幕模拟器（不向 B 站发送消息）', flush=True)
    print('管理员口令 ADMIN_TOKEN =', TOKEN, flush=True)
    print('请在云平台环境变量设置 ADMIN_TOKEN，勿将口令写入公开仓库。', flush=True)
    print(f'监听地址：http://0.0.0.0:{PORT}', flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
