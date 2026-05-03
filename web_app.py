#!/usr/bin/env python3
"""
Privacoin Web API + UI
纯 stdlib 实现，零外部依赖。
浏览器打开 http://localhost:5000 即可使用。
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from note import Note
from ledger import Ledger
from transaction import ShieldedTransaction, verify_transaction
from utils import random_bytes, bytes_to_hex

# 全局状态
ledger = Ledger()
name_registry: dict[str, bytes] = {}

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Privacoin · 隐私币演示</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f0e8;color:#2c2c2c;padding:2rem;max-width:960px;margin:0 auto}
h1{text-align:center;font-size:1.8rem;margin-bottom:.3rem;letter-spacing:.15em;color:#b22222}
.subtitle{text-align:center;color:#888;margin-bottom:2rem;font-size:.85rem}
.card{background:#fff;border-radius:8px;padding:1.5rem;margin-bottom:1.5rem;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.card h2{font-size:1.1rem;margin-bottom:1rem;color:#b22222;border-bottom:1px solid #eee;padding-bottom:.5rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:.8rem}
.btn{background:#b22222;color:#fff;border:none;padding:.5rem 1.2rem;border-radius:6px;cursor:pointer;font-size:.9rem}
.btn:hover{background:#8b1a1a}
input,select{padding:.5rem .8rem;border:1px solid #ddd;border-radius:6px;font-size:.9rem;width:100%;margin-bottom:.6rem}
label{font-size:.85rem;color:#666;display:block;margin-bottom:.3rem}
.row{display:flex;gap:1rem;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;font-size:.85rem}
th{text-align:left;padding:.5rem;border-bottom:2px solid #eee;color:#666;font-weight:600}
td{padding:.5rem;border-bottom:1px solid #f0f0f0;font-family:monospace;font-size:.8rem}
.status{display:inline-block;padding:.2rem .6rem;border-radius:4px;font-size:.75rem;font-weight:600}
.status.ok{background:#e8f5e9;color:#2e7d32}
.status.fail{background:#fbe9e7;color:#c62828}
.mono{font-family:monospace;font-size:.82rem;color:#555}
footer{text-align:center;color:#aaa;font-size:.75rem;margin-top:3rem}
.notice{background:#fff8e1;border:1px solid #ffe082;border-radius:6px;padding:.8rem;margin-bottom:1rem;font-size:.85rem;color:#795548}
</style>
</head>
<body>

<h1>🏛 Privacoin</h1>
<p class="subtitle">隐私保护加密货币 · Zcash 风格教学演示</p>

<div class="notice">
  ⚠️ 教学代码，非生产环境。所有数据存在内存中，重启即清零。
</div>

<div class="grid">
  <div class="card">
    <h2>👤 创建钱包</h2>
    <form onsubmit="postAPI('/api/wallet/create', this, event)">
      <label>钱包名称</label>
      <input name="name" placeholder="例: Alice" required>
      <button class="btn" type="submit">创建</button>
    </form>
  </div>
  <div class="card">
    <h2>💰 铸币</h2>
    <form onsubmit="postAPI('/api/mint', this, event)">
      <label>接收方</label>
      <select name="owner" required><option value="">-- 选择 --</option></select>
      <label>金额</label>
      <input name="value" type="number" min="1" value="100" required>
      <button class="btn" type="submit">铸造</button>
    </form>
  </div>
  <div class="card">
    <h2>📤 隐私转账</h2>
    <form onsubmit="postAPI('/api/transfer', this, event)">
      <label>发送方</label>
      <select name="from_" required><option value="">-- 选择 --</option></select>
      <label>接收方</label>
      <select name="to" required><option value="">-- 选择 --</option></select>
      <label>金额（聪）</label>
      <input name="value" type="number" min="1" value="10" required>
      <button class="btn" type="submit">发送 🛡</button>
    </form>
  </div>
  <div class="card">
    <h2>📊 全局状态</h2>
    <div id="statusDisplay"></div>
    <button class="btn" style="margin-top:.5rem" onclick="refreshAll()">🔄 刷新</button>
  </div>
</div>

<div class="card">
  <h2>👛 钱包 & 余额</h2>
  <div id="walletList">加载中...</div>
</div>

<div class="card">
  <h2>📜 链上 Note</h2>
  <div id="noteList">加载中...</div>
</div>

<div class="card">
  <h2>📋 交易日志</h2>
  <div id="txLog">暂无记录</div>
</div>

<footer>🛡 Privacoin · 教学演示 · 灵感来自 Zcash</footer>

<script>
async function api(url) {
  const r = await fetch(url);
  return r.json();
}

async function postAPI(url, form, ev) {
  ev.preventDefault();
  const fd = new FormData(form);
  const body = {};
  fd.forEach((v, k) => { body[k.replace('_', '')] = v; });
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(body)
  });
  const data = await r.json();
  log(r.ok ? '✅' : '❌', data.message || data.error);
  if (r.ok) form.reset();
  refreshAll();
}

function log(icon, msg) {
  const div = document.getElementById('txLog');
  const el = document.createElement('div');
  el.style.cssText = 'padding:.4rem 0;border-bottom:1px solid #f0f0f0;font-size:.85rem';
  el.innerHTML = `${icon} <span class="mono">${msg}</span>`;
  div.prepend(el);
}

async function refreshWallets() {
  const data = await api('/api/wallets');
  const sel = document.querySelectorAll('select');
  const ws = data.wallets || [];
  sel.forEach(s => {
    const cur = s.value;
    s.innerHTML = '<option value="">-- 选择 --</option>';
    ws.forEach(w => {
      const o = document.createElement('option');
      o.value = w.name; o.textContent = w.name + ' (' + w.balance + ' 聪)';
      s.appendChild(o);
    });
    if (cur) s.value = cur;
  });
  const html = ws.length
    ? '<table><tr><th>名称</th><th>地址</th><th>余额</th></tr>' +
      ws.map(w => '<tr><td><strong>' + w.name + '</strong></td><td class="mono">' + w.address + '</td><td><strong>' + w.balance + '</strong> 聪</td></tr>').join('') +
      '</table>'
    : '<p class="mono">暂无钱包</p>';
  document.getElementById('walletList').innerHTML = html;
}

async function refreshNotes() {
  const data = await api('/api/notes');
  const notes = data.notes || [];
  const html = notes.length
    ? '<table><tr><th>承诺 (Commitment)</th><th>拥有者</th><th>金额</th><th>已花费</th></tr>' +
      notes.map(n => '<tr><td class="mono">' + n.cm + '</td><td>' + n.owner + '</td><td>' + n.value + ' 聪</td><td>' +
        (n.spent ? '<span class="status fail">是</span>' : '<span class="status ok">否</span>') + '</td></tr>').join('') +
      '</table>'
    : '<p class="mono">链上暂无 Note</p>';
  document.getElementById('noteList').innerHTML = html;
}

async function refreshStatus() {
  const data = await api('/api/status');
  document.getElementById('statusDisplay').innerHTML =
    '<table><tr><td>钱包数</td><td><strong>' + data.wallets + '</strong></td></tr>' +
    '<tr><td>链上承诺</td><td><strong>' + data.notes + '</strong></td></tr>' +
    '<tr><td>已用 Nullifier</td><td><strong>' + data.nullifiers + '</strong></td></tr>' +
    '<tr><td>Merkle 根</td><td class="mono">' + data.root + '</td></tr></table>';
}

function refreshAll() { refreshWallets(); refreshNotes(); refreshStatus(); }
refreshAll();
</script>
</body>
</html>"""


class PrivacoinHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            return self._send_html(HTML_PAGE)

        elif path == "/api/wallets":
            wallets = []
            for name, pkh in name_registry.items():
                wallets.append({
                    "name": name,
                    "address": bytes_to_hex(pkh),
                    "balance": ledger.balance(pkh),
                })
            return self._send_json({"wallets": wallets})

        elif path == "/api/notes":
            notes = []
            for cm, note in ledger._unspent_notes.items():
                owner_name = "未知"
                for n, pkh in name_registry.items():
                    if pkh == note.owner:
                        owner_name = n
                        break
                notes.append({
                    "cm": bytes_to_hex(note.commitment()),
                    "owner": owner_name,
                    "value": note.value,
                    "spent": False,
                })
            return self._send_json({"notes": notes})

        elif path == "/api/status":
            return self._send_json({
                "wallets": len(name_registry),
                "notes": ledger.tree._leaf_count,
                "nullifiers": len(ledger.nullifiers),
                "root": bytes_to_hex(ledger.tree.root()),
            })

        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_body()

        if path == "/api/wallet/create":
            name = body.get("name", "").strip()
            if not name:
                return self._send_json({"error": "请输入名称"}, 400)
            if name in name_registry:
                return self._send_json({"error": f"'{name}' 已存在"}, 400)
            pkh = random_bytes(20)
            name_registry[name] = pkh
            return self._send_json({
                "message": f"✅ 钱包 '{name}' 创建成功",
                "address": bytes_to_hex(pkh),
            })

        elif path == "/api/mint":
            owner = body.get("owner", "").strip()
            value = int(body.get("value", 100))
            if owner not in name_registry:
                return self._send_json({"error": f"钱包 '{owner}' 不存在"}, 400)
            if value <= 0:
                return self._send_json({"error": "金额须 > 0"}, 400)
            note = Note.create(value=value, owner_pkh=name_registry[owner])
            idx = ledger.mint(note)
            return self._send_json({
                "message": f"✅ 为 {owner} 铸造 {value} 聪 (树位置 {idx})",
            })

        elif path == "/api/transfer":
            from_name = body.get("from", "").strip()
            to_name = body.get("to", "").strip()
            value = int(body.get("value", 10))

            if from_name not in name_registry:
                return self._send_json({"error": f"发送方 '{from_name}' 不存在"}, 400)
            if to_name not in name_registry:
                return self._send_json({"error": f"接收方 '{to_name}' 不存在"}, 400)
            if from_name == to_name:
                return self._send_json({"error": "不能转给自己"}, 400)
            if value <= 0:
                return self._send_json({"error": "金额须 > 0"}, 400)

            from_pkh = name_registry[from_name]
            to_pkh = name_registry[to_name]

            # 找可花费的 Note
            spendable = [
                (cm, note) for cm, note in ledger._unspent_notes.items()
                if note.owner == from_pkh
            ]
            if not spendable:
                return self._send_json({"error": f"{from_name} 没有可花的 Note"}, 400)

            sel_note = None
            for _, n in spendable:
                if n.value >= value:
                    sel_note = n
                    break
            if sel_note is None:
                return self._send_json({
                    "error": f"{from_name} 没有单个金额足够的 Note（暂不支持组合）"
                }, 400)

            cm = sel_note.commitment()
            leaf_idx = ledger._note_positions[cm]

            tx = ShieldedTransaction()
            tx.add_spend(sel_note, ledger.tree, leaf_idx)

            change_val = sel_note.value - value
            change_note = None
            if change_val > 0:
                change_note = Note.create(value=change_val, owner_pkh=from_pkh)
                tx.add_output(change_note)

            to_note = Note.create(value=value, owner_pkh=to_pkh)
            tx.add_output(to_note)

            valid, msg = verify_transaction(tx, ledger.tree, ledger.nullifiers)
            if not valid:
                return self._send_json({"error": f"交易验证失败: {msg}"}, 400)

            ledger.spend(sel_note)
            if change_note:
                ledger.mint(change_note)
            ledger.mint(to_note)

            detail = f"{from_name} → {to_name} : {value} 聪"
            if change_val > 0:
                detail += f" (找零 {change_val} 聪)"
            return self._send_json({"message": detail + " ✅"})

        else:
            self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):
        # 精简日志
        print(f"[API] {args[0]} {args[1]} {args[2]}")


def main():
    port = int(os.environ.get("PORT", 5000))
    server = HTTPServer(("0.0.0.0", port), PrivacoinHandler)
    print(f"🚀 Privacoin Web 界面启动: http://localhost:{port}")
    print(f"   打开浏览器即可使用，或通过 curl 调用 API")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务关闭")
        server.server_close()


if __name__ == "__main__":
    main()
