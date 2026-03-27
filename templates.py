# -*- coding: utf-8 -*-
# ================== templates.py ==================
# Load HTML templates - đọc từ file mỗi lần để /iframegame có hiệu lực ngay

import os

_root = os.path.dirname(os.path.abspath(__file__))

def _load(filename):
    """Load file HTML từ thư mục gốc."""
    path = os.path.join(_root, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Không tìm thấy template: {filename}")
    with open(path, encoding='utf-8') as f:
        return f.read()

# ── Page templates (load 1 lần lúc khởi động - không đổi) ──────────────────
HTML_REGISTER      = _load('register.html')
HTML_LOGIN         = _load('login.html')
HTML_MENU          = _load('menu.html')
HTML_ACCOUNT       = _load('account.html')
HTML_BUY_KEY       = _load('buy_key.html')
HTML_DEPOSIT       = _load('deposit.html')
HTML_DEPOSIT_SEPAY = HTML_DEPOSIT
HTML_ENTER_KEY     = _load('enter_key.html')

# ── Game templates - đọc từ file mỗi lần (để /iframegame có hiệu lực ngay) ─
GAME_FILES = {
    'sun':   'game_sun.html',
    'hit':   'game_hit.html',
    'b52':   'game_b52.html',
    'sicbo': 'game_sicbo.html',
    '789':   'game_789.html',
    '68gb':  'game_68gb.html',
    'luck8': 'game_luck8.html',
    'lc79':  'game_lc79.html',
    'sexy':  'game_sexy.html',
}

class _LazyGameTemplates(dict):
    """Dict đặc biệt - mỗi lần .get() đọc lại file từ disk"""
    def get(self, key, default=None):
        fname = GAME_FILES.get(key)
        if not fname:
            return default
        try:
            return _load(fname)
        except Exception:
            return default

    def __getitem__(self, key):
        result = self.get(key)
        if result is None:
            raise KeyError(key)
        return result

    def __contains__(self, key):
        return key in GAME_FILES

GAME_TEMPLATES = _LazyGameTemplates()
