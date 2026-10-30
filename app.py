#!/usr/bin/env python3
import hashlib
import html
import http.cookies
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from python_multipart import parse_form
from python_multipart.exceptions import FormParserError, MultipartParseError


BASE_DIR = os.environ.get("R2_DRIVE_DATA", "/opt/r2-drive/data")
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "drive.sqlite3")
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
SITE_NAME = os.environ.get("R2_DRIVE_SITE_NAME", "R2 Drive")
COOKIE_NAME = "r2_drive_session"
SESSION_SECONDS = 30 * 86400
MAX_NAME = 180
MAX_UPLOAD_BYTES = int(os.environ.get("R2_DRIVE_MAX_UPLOAD_BYTES", str(10 * 1024**3)))
MAX_JSON_BYTES = 1024 * 1024
DOWNLOAD_CHUNK_SIZE = 16 * 1024
IMAGE_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>R2 Drive</title>
  <style>
    :root{--accent:#2563eb;--success:#059669;--danger:#dc2626;--bg:#f7f7f5;--surface:#fff;--soft:#f4f4f5;--text:#18181b;--muted:#71717a;--faint:#a1a1aa;--border:#e4e4e7;font-family:Inter,"Noto Sans SC",system-ui,sans-serif;color:var(--text);background:var(--bg)}*{box-sizing:border-box}body{margin:0;background:var(--bg)}button,input{font:inherit}button{cursor:pointer}.splash,.auth{min-height:100vh;display:grid;place-items:center;padding:20px}.card{width:min(420px,100%);padding:28px;border:1px solid var(--border);border-radius:10px;background:#fff;box-shadow:0 18px 48px #18181b14}.brand{display:flex;align-items:center;gap:12px;margin-bottom:26px}.mark{width:42px;height:42px;border-radius:8px;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:900}.brand span{display:grid;gap:2px}.brand small,.muted{color:var(--muted)}h1{margin:0 0 8px;font-size:27px}.card p{margin:0 0 22px;color:var(--muted);line-height:1.65}label{display:grid;gap:8px;margin:15px 0;font-size:13px;font-weight:750}input{height:44px;border:1px solid var(--border);border-radius:8px;padding:0 12px;outline:none}input:focus{border-color:#93b4f5;box-shadow:0 0 0 3px #2563eb1a}.primary,.secondary,.icon{height:40px;border-radius:8px;border:0;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-weight:780}.primary{background:var(--accent);color:#fff;padding:0 14px}.secondary{background:#fff;border:1px solid var(--border);color:var(--text);padding:0 14px}.icon{width:38px;background:#fff;border:1px solid var(--border);color:var(--muted)}.full{width:100%;height:48px;margin-top:12px}.alert{display:flex;align-items:center;gap:8px;min-height:40px;border:1px solid #fee2e2;background:#fef2f2;color:var(--danger);border-radius:8px;padding:9px 12px;margin-bottom:14px;font-size:13px;font-weight:700}.shell{height:100vh;display:grid;grid-template-columns:220px minmax(0,1fr);overflow:hidden}aside{background:#fff;border-right:1px solid var(--border);padding:22px 14px 16px;display:flex;flex-direction:column}.nav{height:42px;border:0;border-radius:8px;background:#eff6ff;color:var(--accent);display:flex;align-items:center;gap:10px;padding:0 12px;font-weight:760}.logout{margin-top:auto;background:transparent;color:var(--muted);justify-content:flex-start}.work{min-width:0;overflow:auto;padding:26px 30px 52px}.work header{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:22px}.work h1{margin:4px 0 0}.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:16px}.crumbs{min-width:0;margin-right:auto;display:flex;gap:7px;align-items:center;overflow:auto;color:var(--faint)}.crumbs button{border:0;background:transparent;color:var(--muted);font-weight:760;padding:7px 3px;white-space:nowrap}.crumbs button:last-child{color:var(--text)}.search{width:220px;height:40px}.picker{position:relative;overflow:hidden}.picker input{position:absolute;inset:0;opacity:0}.drop{min-height:88px;border:1.5px dashed #b6c8f6;background:#ffffffb8;border-radius:8px;display:flex;align-items:center;gap:14px;padding:18px;color:var(--muted);margin-bottom:18px}.drop.drag{border-color:var(--accent);background:#eff6ff}.uploads{display:grid;gap:9px;margin-bottom:16px}.task{background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px}.task div:first-child{display:flex;justify-content:space-between;gap:14px;font-size:12px}.bar{height:7px;background:#e5e7eb;border-radius:99px;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;background:var(--accent)}.list-scroll{overflow-x:auto}.list{min-width:1140px;background:#fff;border:1px solid var(--border);border-radius:8px;overflow:hidden}.head,.row{display:grid;grid-template-columns:minmax(220px,1.8fr) 74px 92px 92px 92px 82px 150px 250px;align-items:center;gap:9px;padding:0 16px}.head{height:42px;background:var(--soft);color:var(--muted);font-size:11px;font-weight:800}.row{min-height:62px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)}.name{min-width:0;border:0;background:transparent;color:var(--text);display:flex;align-items:center;gap:12px;text-align:left;padding:8px 0}.ico{width:36px;height:36px;border-radius:8px;background:#eef2ff;color:var(--accent);display:grid;place-items:center;flex:none}.name span:last-child{min-width:0;display:grid;gap:3px}.name b{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.name small{color:var(--faint);font-size:10px}.privacy{width:72px;height:28px;border-radius:99px;border:0;font-size:11px;font-weight:800}.privacy.private{background:#f4f4f5;color:#52525b}.privacy.public{background:#ecfdf5;color:var(--success)}.limit-btn{height:28px;border:1px solid var(--border);border-radius:7px;background:#fff;color:var(--muted);font-size:11px;font-weight:800;padding:0 8px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.limit-btn:hover{border-color:#93b4f5;color:var(--accent);background:#eff6ff}.modal-backdrop{position:fixed;inset:0;background:#18181b66;display:grid;place-items:center;padding:20px;z-index:20}.modal{width:min(440px,100%);background:#fff;border:1px solid var(--border);border-radius:10px;box-shadow:0 20px 60px #18181b33;padding:24px}.modal h2{margin:0 0 8px;font-size:20px}.modal p{margin:0 0 18px;color:var(--muted);word-break:break-word}.limit-field{display:grid;grid-template-columns:minmax(0,1fr) 54px;align-items:center;border:1px solid var(--border);border-radius:8px;overflow:hidden}.limit-field input{border:0;border-radius:0}.limit-field span{height:44px;display:grid;place-items:center;background:var(--soft);color:var(--muted);font-size:12px;font-weight:800}.modal-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.actions{display:flex;justify-content:flex-end;gap:4px}.actions button{width:30px;height:30px;border:0;border-radius:7px;background:transparent;color:var(--muted)}.actions button:hover{background:#eff6ff;color:var(--accent)}.actions button:last-child:hover{background:#fef2f2;color:var(--danger)}.empty{min-height:220px;display:grid;place-items:center;color:var(--muted);font-size:13px;font-weight:700;border-top:1px solid var(--border)}.toast{position:fixed;right:24px;bottom:24px;min-height:42px;display:flex;align-items:center;background:#18181b;color:#fff;border-radius:8px;padding:0 16px;font-size:12px;font-weight:780}@media(max-width:920px){.shell{display:block;height:auto}.shell aside{display:none}.work{height:auto;min-height:100vh;padding:20px 16px 40px}.toolbar{align-items:stretch;flex-wrap:wrap}.crumbs{width:100%}.search{flex:1;min-width:160px}.head{display:none}.list-scroll{overflow:visible}.list{min-width:0;background:transparent;border:0;display:grid;gap:9px;overflow:visible}.row{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"name actions" "meta privacy";min-height:74px;background:#fff;border:1px solid var(--border);border-radius:8px;padding:10px 12px}.row .name{grid-area:name}.row .size-cell{grid-area:meta;padding-left:48px}.row .count-cell,.row .traffic-cell,.row .limit-cell,.row .updated-cell{display:none}.row .privacy-cell{grid-area:privacy}.actions{grid-area:actions;gap:3px}.actions button{display:none}.actions button:first-child,.actions button:last-child,.actions.file-actions button:nth-child(2),.actions.file-actions button:nth-child(3){display:block}.actions.file-actions button{width:28px}.modal{padding:22px}}@media(max-width:560px){.card{padding:22px}.work h1{font-size:23px}.secondary,.picker{flex:1}.modal-actions .secondary,.modal-actions .primary{flex:1}}
  </style>
  <style>
    .nav-group{display:grid;gap:6px}.nav.active{background:#eff6ff;color:var(--accent)}.nav:not(.active){background:transparent;color:var(--muted)}.mobile-nav{display:none}.image-drop{min-height:118px;border:1.5px dashed #9db6ef;background:#eff6ffb8;border-radius:10px;display:grid;place-items:center;gap:5px;padding:18px;margin-bottom:16px;color:var(--muted);text-align:center;transition:background .15s,border-color .15s}.image-drop.drag{border-color:var(--accent);background:#dbeafe;color:var(--text)}.image-drop b{color:var(--text);font-size:14px}.image-drop small{font-size:12px}.image-drop input{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}.image-toolbar{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:14px}.image-toolbar .crumbs{margin-right:auto;width:auto}.image-toolbar .secondary,.image-toolbar .primary,.image-toolbar .icon{height:36px}.view-toggle{display:flex;gap:3px;padding:3px;background:var(--soft);border-radius:8px}.view-toggle button{height:30px;padding:0 10px;border:0;border-radius:6px;background:transparent;color:var(--muted);font-size:12px;font-weight:800}.view-toggle button.active{background:#fff;color:var(--accent);box-shadow:0 1px 3px #18181b1a}.image-selection-bar{display:flex;align-items:center;gap:8px;min-height:40px;padding:8px 10px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:14px;font-size:12px;font-weight:800}.image-selection-bar .spacer{margin-right:auto}.image-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.image-card{position:relative;min-width:0;background:#fff;border:1px solid var(--border);border-radius:8px;overflow:hidden}.image-card.selected{border-color:#2563eb;box-shadow:0 0 0 2px #2563eb33}.image-thumb{display:block;width:100%;aspect-ratio:4/3;border:0;background:#f4f4f5;padding:0;overflow:hidden}.image-thumb img{width:100%;height:100%;object-fit:cover;display:block}.image-info{display:grid;gap:5px;padding:12px 13px 5px}.image-info b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.image-info small{color:var(--muted);font-size:11px}.image-actions{display:flex;flex-wrap:wrap;gap:6px;padding:8px 13px 13px}.image-actions .secondary{height:31px;padding:0 8px;font-size:11px}.image-select{position:absolute;left:10px;top:10px;z-index:2;width:26px;height:26px;border:2px solid #fff;border-radius:7px;background:#ffffffd9;box-shadow:0 1px 4px #18181b33;color:transparent;display:grid;place-items:center;font-size:15px;font-weight:900;padding:0}.image-select.selected{background:var(--accent);color:#fff;border-color:var(--accent)}.image-folder-card{min-height:180px;display:grid;align-content:center;justify-items:center;gap:8px;padding:20px;background:#fff;border:1px solid var(--border);border-radius:8px;color:var(--text)}.image-folder-card b{font-size:14px}.image-folder-card small{color:var(--muted)}.image-list .image-folder-card{min-height:64px;display:grid;grid-template-columns:42px minmax(0,1fr) auto;grid-template-areas:"icon name actions";align-content:center;justify-items:start;padding:8px 12px;text-align:left}.image-list .image-folder-card>div:first-child{grid-area:icon}.image-list .image-folder-card>b{grid-area:name}.image-list .image-folder-card>small{grid-area:name;align-self:end;margin-left:0;padding-top:22px}.image-list .image-folder-card>.image-actions{grid-area:actions;padding:0;justify-content:flex-end}.image-list{display:grid;gap:8px}.image-list-row{display:grid;grid-template-columns:32px 52px minmax(0,1fr) 100px 160px minmax(260px,auto);gap:10px;align-items:center;min-height:64px;padding:8px 12px;background:#fff;border:1px solid var(--border);border-radius:8px;font-size:12px}.image-list-row.selected{border-color:#2563eb;box-shadow:0 0 0 2px #2563eb33}.image-list-row img{width:48px;height:48px;object-fit:cover;border-radius:6px;background:var(--soft)}.image-list-row .image-list-name{min-width:0;display:grid;gap:3px}.image-list-name b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.image-list-name small{color:var(--muted)}.image-list-actions{display:flex;justify-content:flex-end;gap:4px;flex-wrap:wrap}.image-list-actions button{height:30px;padding:0 7px;font-size:11px}.image-empty{grid-column:1/-1;border:1px solid var(--border);border-radius:8px}.image-preview-modal{position:relative;width:min(960px,100%);max-height:calc(100vh - 40px);display:grid;place-items:center;gap:10px}.image-preview-modal img{max-width:100%;max-height:calc(100vh - 100px);object-fit:contain;border-radius:8px;box-shadow:0 20px 60px #0008}.image-preview-modal p{margin:0;color:#fff;font-size:13px;word-break:break-word;text-align:center}.image-close{position:absolute;right:-4px;top:-4px;z-index:1;background:#fff;color:var(--text);font-size:22px}.danger-primary{background:var(--danger)}.task-error{display:block;margin-top:7px;color:var(--danger);font-size:11px}@media(max-width:920px){.mobile-nav{display:block;min-width:0}.mobile-nav .nav-group{display:flex;gap:4px}.mobile-nav .nav{height:36px;padding:0 8px;font-size:12px}.image-drop{min-height:96px;padding:14px}.image-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.image-actions{gap:4px}.image-actions .secondary{flex:1;min-width:calc(50% - 4px)}.image-list .image-folder-card{min-height:68px}.image-list-row{grid-template-columns:32px 48px minmax(0,1fr) auto;grid-template-areas:"select thumb name actions" "select thumb meta actions";min-height:68px}.image-list-row .image-list-select{grid-area:select}.image-list-row img{grid-area:thumb}.image-list-row .image-list-name{grid-area:name}.image-list-row .image-list-meta{grid-area:meta}.image-list-row .image-list-actions{grid-area:actions;max-width:112px}.image-list-row .image-list-size,.image-list-row .image-list-date{display:none}.image-preview-modal{width:100%}}@media(max-width:560px){.image-grid{grid-template-columns:repeat(1,minmax(0,1fr));gap:9px}.image-actions .secondary{min-width:calc(50% - 4px)}.image-toolbar{align-items:stretch}.image-toolbar .crumbs{width:100%;margin-right:0}.image-toolbar .secondary,.image-toolbar .primary{flex:1}.view-toggle{width:100%}.view-toggle button{flex:1}.image-list-row .image-list-actions button{font-size:10px;padding:0 5px}}
  </style>
  <style>
    .danger-action{color:var(--danger)!important}
    /* Keep list rows bounded: only the file information column may shrink. */
    .image-list-row{grid-template-columns:32px 56px minmax(0,1fr) 84px 140px minmax(0,300px);min-width:0;overflow:hidden}
    .image-list-row .image-list-select{position:static;left:auto;top:auto;grid-column:1;width:26px;height:26px}
    .image-list-row>img{display:block;flex-shrink:0;cursor:pointer}
    .image-list-row .image-list-name{min-width:0;max-width:100%;overflow:hidden}
    .image-list-name b{display:block;min-width:0;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .image-list-actions{min-width:0;max-width:100%;overflow:hidden;flex-wrap:nowrap}
    .image-list-actions button{min-width:0;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:0 1 auto}
    @media(max-width:920px){
      .image-list-row{grid-template-columns:32px 48px minmax(0,1fr);grid-template-areas:"select thumb name" "select thumb meta" "actions actions actions";min-width:0}
      .image-list-row .image-list-name{min-width:0;max-width:100%;overflow:hidden}
      .image-list-row .image-list-actions{width:100%;max-width:none;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;overflow:hidden}
      .image-list-row .image-list-actions button{width:100%;padding:0 3px}
    }
    .image-move-modal{display:flex;flex-direction:column;max-height:min(680px,calc(100vh - 40px));overflow:hidden}
    .image-move-crumbs{display:flex;align-items:center;gap:5px;min-width:0;overflow-x:auto;margin:4px 0 14px;color:var(--faint)}
    .image-move-crumbs button{border:0;background:transparent;color:var(--muted);font-weight:760;padding:6px 2px;white-space:nowrap}
    .image-move-crumbs button:last-of-type{color:var(--text)}
    .image-move-folders{display:grid;gap:7px;min-height:120px;max-height:360px;overflow:auto;padding:1px}
    .image-move-folder{width:100%;min-width:0;height:44px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--text);display:flex;align-items:center;gap:9px;padding:0 11px;text-align:left}
    .image-move-folder span:last-child{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
    .image-move-empty{min-height:100px;display:grid;place-items:center;color:var(--muted);font-size:12px}
    .mobile-drawer-backdrop{display:none}
    .mobile-menu-button{display:none}
    .image-more-sheet{display:none}
    @media(max-width:560px){.image-selection-bar{flex-wrap:wrap}.image-selection-bar .spacer{display:none}.image-selection-bar .secondary,.image-selection-bar .primary{flex:1}.image-move-modal{max-height:calc(100vh - 24px);padding:20px}.image-move-folders{max-height:calc(100vh - 280px)}}
  </style>
  <style>
    @media(max-width:920px){
      body.drawer-open{overflow:hidden}
      .mobile-menu-button{display:inline-flex;width:40px;height:40px;flex:0 0 40px;font-size:20px}
      .mobile-header{display:flex!important;align-items:center;gap:10px;margin-bottom:10px!important;padding-top:env(safe-area-inset-top)}
      .mobile-header .mobile-title{min-width:0;flex:1}.mobile-header .mobile-title b{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:18px}.mobile-header .mobile-title small{display:block;color:var(--muted);font-size:11px;margin-top:3px}
      .mobile-header .icon{flex:0 0 38px}
      .mobile-drawer-backdrop{display:block;position:fixed;inset:0;background:#18181b66;z-index:40;opacity:0;pointer-events:none;transition:opacity .18s}
      .mobile-drawer-backdrop.open{opacity:1;pointer-events:auto}
      .mobile-drawer{position:fixed;z-index:41;inset:0 auto 0 0;width:min(290px,80vw);padding:calc(18px + env(safe-area-inset-top)) 14px calc(18px + env(safe-area-inset-bottom));background:#fff;transform:translateX(-105%);transition:transform .18s;box-shadow:18px 0 40px #18181b22;display:flex;flex-direction:column}
      .mobile-drawer.open{transform:translateX(0)}.mobile-drawer .brand{margin:0 8px 22px}.mobile-drawer .nav-group{display:grid;gap:6px}.mobile-drawer .nav{height:44px}.mobile-drawer .drawer-divider{height:1px;background:var(--border);margin:16px 0}.mobile-drawer .drawer-refresh{justify-content:flex-start;background:transparent;color:var(--muted)}.mobile-drawer .drawer-logout{margin-top:auto}
      .mobile-drawer-backdrop,.mobile-drawer{display:block}
      .work header:not(.mobile-header){display:none}
      .work{padding:14px 16px calc(34px + env(safe-area-inset-bottom))}
      .toolbar{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-bottom:12px}.toolbar .crumbs{grid-column:1/-1;grid-row:3;width:100%}.toolbar .search{grid-column:1/-1;grid-row:2;width:100%;min-width:0}.toolbar>button.secondary,.toolbar>.picker{grid-row:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .drive-toolbar>button.secondary,.drive-toolbar>.picker{width:100%;height:40px;margin:0}.drive-toolbar .picker input{width:100%;height:100%}.drive-toolbar .crumbs:has(button:only-child){display:none}.drive-drop .drive-drop-title{font-size:0}.drive-drop .drive-drop-title:after{content:'点击上方按钮选择文件上传';font-size:13px}
      .image-toolbar{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:8px;margin-bottom:12px}.image-toolbar .crumbs{grid-column:1/-1;grid-row:4;width:100%;margin:0}.image-toolbar .view-toggle{grid-column:1/-1;grid-row:2;width:100%}.image-toolbar .search{grid-column:1/-1;grid-row:3;width:100%;min-width:0}.image-toolbar>button.secondary{grid-row:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.image-toolbar .view-toggle button{height:36px}.image-drop{min-height:78px;padding:10px;margin-bottom:12px}.image-drop b{font-size:0}.image-drop b:after{content:'点击选择图片上传';font-size:13px}.image-drop small{font-size:11px}.image-card .image-actions,.image-list-row .image-list-actions{display:none}.image-card .image-actions.mobile-primary-actions,.image-list-row .image-list-actions.mobile-primary-actions{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px;padding:8px 10px 10px}.image-card .image-actions.mobile-primary-actions button,.image-list-row .image-list-actions.mobile-primary-actions button{display:block!important;width:100%;min-width:0;padding:0 3px;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.image-more-sheet{display:block;position:fixed;inset:0;z-index:30;background:#18181b66;opacity:0;pointer-events:none;transition:opacity .18s}.image-more-sheet.open{opacity:1;pointer-events:auto}.image-more-panel{position:absolute;inset:auto 0 0;background:#fff;border-radius:14px 14px 0 0;padding:16px 16px calc(16px + env(safe-area-inset-bottom));transform:translateY(105%);transition:transform .18s}.image-more-sheet.open .image-more-panel{transform:translateY(0)}.image-more-panel h3{margin:0 0 12px;font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.image-more-panel button{width:100%;height:44px;border:0;border-top:1px solid var(--border);background:#fff;text-align:left;padding:0 4px}.image-more-panel button:last-child{color:var(--muted)}.image-more-panel .danger-action{color:var(--danger)}
      .image-selection-bar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.image-selection-bar .selection-count{grid-column:1/-1}.image-selection-bar .spacer{display:none}.image-selection-bar button{min-width:0;min-height:40px;padding:0 6px}.image-folder-card{min-height:120px;padding:12px;gap:5px}.image-folder-card>div:first-child{font-size:26px!important}.image-list .image-folder-card{min-height:60px}.image-list-row .image-list-actions.mobile-primary-actions{display:grid}
    }
    @media(min-width:921px){.mobile-drawer-backdrop,.mobile-drawer,.image-more-sheet{display:none!important}.mobile-more-button{display:none!important}}
  </style>
  <style>@media(max-width:920px){.image-card .image-actions.mobile-primary-actions .mobile-hidden-action,.image-list-row .image-list-actions.mobile-primary-actions .mobile-hidden-action{display:none!important}.image-card .image-actions.mobile-primary-actions .mobile-more-button,.image-list-row .image-list-actions.mobile-primary-actions .mobile-more-button{display:block!important}.image-toolbar .crumbs:has(button:only-child){display:none!important}}</style>
  <style>
    .management-bar{display:flex;align-items:center;gap:8px;min-height:42px;padding:8px 10px;margin-bottom:14px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;font-size:12px;font-weight:800}.management-bar .spacer{margin-right:auto}.management-bar[hidden]{display:none}.item-name-cell{min-width:0;display:flex;align-items:center;gap:6px}.item-name-cell .name{min-width:0;flex:1}.item-select,.drag-handle{width:28px;height:28px;flex:0 0 28px;border:1px solid var(--border);border-radius:7px;background:#fff;color:var(--muted);display:grid;place-items:center;padding:0}.item-select.selected{background:var(--accent);border-color:var(--accent);color:#fff}.drag-handle{cursor:grab;font-size:17px;touch-action:none}.drag-handle:active{cursor:grabbing}.row.selected,.image-folder-card.selected{border-color:#2563eb;box-shadow:inset 0 0 0 1px #2563eb}.sortable-ghost{opacity:.35;background:#dbeafe!important}.sortable-chosen{box-shadow:0 8px 24px #18181b22}.list .sort-group{display:block}.image-grid .sort-group{grid-column:1/-1;display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.image-list .sort-group{display:grid;gap:8px}.image-folder-card,.image-list-row{position:relative}.image-folder-card>.item-select{position:absolute;left:10px;top:10px}.image-folder-card>.drag-handle,.image-card>.drag-handle,.image-list-row>.drag-handle{position:absolute;right:10px;top:10px;z-index:3}.move-modal{display:flex;flex-direction:column;max-height:min(700px,calc(100vh - 40px));overflow:hidden}.move-crumbs{display:flex;align-items:center;gap:5px;min-width:0;overflow-x:auto;margin:4px 0 12px;color:var(--faint)}.move-crumbs button{border:0;background:transparent;color:var(--muted);font-weight:760;padding:6px 2px;white-space:nowrap}.move-folders{display:grid;gap:7px;min-height:110px;max-height:330px;overflow:auto;padding:1px}.move-folder{width:100%;min-width:0;height:44px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--text);display:flex;align-items:center;gap:9px;padding:0 11px;text-align:left}.move-folder span:last-child{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.conflict-choice{margin:14px 0 0}.conflict-choice select{height:40px;border:1px solid var(--border);border-radius:8px;background:#fff;padding:0 10px}.empty-group{display:none}
    @media(max-width:920px){.drag-handle{display:none}.item-name-cell{grid-area:name}.item-select{width:34px;height:34px;flex-basis:34px}.actions button,.actions.file-actions button{width:34px;height:34px}.management-bar{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.management-bar .selection-count{grid-column:1/-1}.management-bar .spacer{display:none}.management-bar button{min-width:0;padding:0 6px}.list .sort-group{display:grid;gap:9px}.image-grid .sort-group{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.reorder-button{display:inline-flex!important}.move-modal{max-height:calc(100vh - 24px);padding:20px}.move-folders{max-height:calc(100vh - 310px)}}
    @media(max-width:560px){.image-grid .sort-group{grid-template-columns:minmax(0,1fr)}}
  </style>
</head>
<body><div id="app" class="splash">正在载入...</div>
<script src="/vendor/sortablejs/Sortable.min.js"></script>
<script>
const S={view:"loading",siteName:"R2 Drive",username:"",role:"",folders:[],files:[],imageFiles:[],imageFolders:[],folder:"root",imageFolder:"root",search:"",error:"",toast:"",toastPriorityUntil:0,stats:{totalFiles:0,totalBytes:0},uploads:[],uploadQueue:[],uploading:false,limitModal:null,driveModal:null,imagePreview:null,imageDeleteModal:null,imageBatchDeleteModal:false,imageMoveModal:null,imageMoreModal:null,imageFolderModal:null,imageFolderDeleteModal:null,moveModal:null,driveSelected:new Set(),selectedImageIds:new Set(),selectedImageFolderIds:new Set(),imageViewMode:localStorage.getItem("r2_image_view_mode")==="list"?"list":"grid",sortables:[]};
const $=id=>document.getElementById(id), app=$("app");
init();
async function init(){try{const st=await api("/api/status");S.siteName=st.siteName;document.title=S.siteName;if(!st.initialized){S.view="init";return render()}try{const me=await api("/api/me");S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch{S.view="login";render()}}catch(e){S.error=e.message;S.view="login";render()}}
async function refresh(){const [folders,files,stats]=await Promise.all([api("/api/drive/folders"),api(`/api/drive/files?folderId=${enc(S.folder)}`),api("/api/stats")]);S.folders=folders;S.files=files;S.stats=stats;render()}
async function refreshImageHost(preserveScroll=false){const scroll=preserveScroll?imageScrollTop():0;const [folders,files]=await Promise.all([api("/api/image-host/folders"),api(`/api/image-host/files?folderId=${enc(S.imageFolder)}`)]);S.imageFolders=folders;S.imageFiles=files;S.selectedImageIds=new Set([...S.selectedImageIds].filter(id=>files.some(f=>f.id===id)));S.selectedImageFolderIds=new Set([...S.selectedImageFolderIds].filter(id=>folders.some(f=>f.id===id&&f.parentId===S.imageFolder)));render();if(preserveScroll)requestAnimationFrame(()=>restoreImageScroll(scroll))}
function goDrive(){S.view="drive";S.search="";S.error="";clearAllSelections();refresh()}
function goImageHost(){S.view="imageHost";S.search="";S.error="";clearAllSelections();refreshImageHost()}
function render(){destroySortables();if(S.view==="init") return auth(true); if(S.view==="login") return auth(false); if(S.view==="drive") return drive(); if(S.view==="imageHost") return imageHost(); app.innerHTML="正在载入..."}
function auth(init){app.className="auth";app.innerHTML=`<form class="card" id="${init?"initForm":"loginForm"}"><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>私人网盘</small></span></div><h1>${init?"创建系统管理员":"登录网盘"}</h1><p>${init?"首次部署需要创建管理员账户。":"使用管理员账户进入私人空间。"}</p>${S.error?`<div class="alert">${esc(S.error)}</div>`:""}<label><span>用户名</span><input name="username" autocomplete="username" minlength="3" maxlength="32" required></label><label><span>密码</span><input name="password" type="password" autocomplete="${init?"new-password":"current-password"}" minlength="${init?10:1}" required></label><button class="primary full">${init?"完成初始化":"确认登录"}</button></form>`;$(init?"initForm":"loginForm").onsubmit=init?submitInit:submitLogin}
function navHtml(active){return `<nav class="nav-group"><button class="nav ${active==="drive"?"active":""}" onclick="closeDrawer();goDrive()">我的网盘</button><button class="nav ${active==="imageHost"?"active":""}" onclick="closeDrawer();goImageHost()">我的图床</button></nav>`}
function drawerHtml(active){return `<div class="mobile-drawer-backdrop" id="drawerBackdrop" onclick="closeDrawer()"></div><aside class="mobile-drawer" id="mobileDrawer"><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>${esc(S.username)}</small></span></div>${navHtml(active)}<div class="drawer-divider"></div><button type="button" class="nav drawer-refresh" onclick="closeDrawer();${active==="drive"?"refresh()":"refreshImageHost(true)"}">↻ 刷新</button><button type="button" class="secondary logout drawer-logout" onclick="logout()">退出登录</button></aside>`}
function mobileHeader(title,summary,refreshCall,active){return `<header class="mobile-header"><button type="button" class="icon mobile-menu-button" onclick="openDrawer()" aria-label="打开导航">☰</button><div class="mobile-title"><b>${esc(title)}</b><small>${esc(summary)}</small></div><button type="button" class="icon" onclick="${refreshCall}" title="刷新">↻</button></header>`}
function openDrawer(){const drawer=$("mobileDrawer"),backdrop=$("drawerBackdrop");if(!drawer||!backdrop)return;drawer.classList.add("open");backdrop.classList.add("open");document.body.classList.add("drawer-open")}
function closeDrawer(){const drawer=$("mobileDrawer"),backdrop=$("drawerBackdrop");if(drawer)drawer.classList.remove("open");if(backdrop)backdrop.classList.remove("open");document.body.classList.remove("drawer-open")}
function drive(){
  app.className="";
  const folders=S.folders.filter(x=>x.parentId===S.folder);
  const files=S.files;
  app.innerHTML=`<main class="shell"><aside><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>${esc(S.username)}</small></span></div>${navHtml("drive")}<button class="secondary logout" onclick="logout()">退出登录</button></aside><section class="work"><header><div><p class="muted">共 ${S.stats.totalFiles} 个文件 · ${fmtSize(S.stats.totalBytes)}</p><h1>我的网盘</h1></div><div class="mobile-nav">${navHtml("drive")}</div><button class="icon" onclick="refresh()" title="刷新">↻</button></header>${S.error?`<div class="alert">${esc(S.error)}<button onclick="S.error='';render()">×</button></div>`:""}<section class="toolbar drive-toolbar"><div class="crumbs">${crumbs()}</div><input class="search" id="search" placeholder="搜索当前文件夹" value="${esc(S.search)}"><button class="secondary" onclick="newFolder()">新建文件夹</button><label class="primary picker">上传文件<input id="fileInput" type="file" multiple></label></section>${managementBar("drive")}<section class="uploads" id="driveUploads"></section><section id="drop" class="drop drive-drop"><b>⇧</b><span><b class="drive-drop-title">拖放文件到这里上传</b><small>上传到当前文件夹</small></span></section><div class="list-scroll"><section class="list"><div class="head"><span>名称</span><span>下载次数</span><span>下载流量</span><span>流量限制</span><span>大小</span><span>访问</span><span>更新时间</span><span></span></div>${S.folder!=="root"?parentRow():""}<div class="sort-group drive-folder-group" data-sort-type="folder">${folders.map(folderRow).join("")}</div><div class="sort-group drive-file-group" data-sort-type="file">${files.map(fileRow).join("")}</div><div class="empty drive-empty" ${folders.length||files.length?"hidden":""}>这个文件夹是空的</div></section></div></section>${limitModal()}${driveModalHtml()}${moveModalHtml()}<div class="toast" id="appToast" ${S.toast?"":"hidden"}>${esc(S.toast)}</div></main>`;
  app.insertAdjacentHTML("afterbegin",drawerHtml("drive"));
  document.querySelector(".work").insertAdjacentHTML("afterbegin",mobileHeader("我的网盘",`共 ${S.stats.totalFiles} 个文件 · ${fmtSize(S.stats.totalBytes)}`,"refresh()","drive"));
  document.onkeydown=e=>{if(e.key==="Escape")closeDrawer()};
  updateUploadDom();
  filterVisibleItems();
  initSortables("drive");
  $("search").oninput=e=>{S.search=e.target.value;filterVisibleItems();initSortables("drive")};
  $("fileInput").onchange=e=>enqueueDriveFiles(e.target.files);
  if(S.limitModal)$("limitForm").onsubmit=saveDownloadLimit;
  if(S.driveModal&&$("driveActionForm"))$("driveActionForm").onsubmit=submitDriveModal;
  document.onkeydown=e=>{if(e.key!=="Escape")return;if(document.querySelector(".mobile-drawer.open")){closeDrawer();return}if(S.moveModal)closeMove();else if(S.driveModal)closeDriveModal()};
  const d=$("drop");d.ondragover=e=>{e.preventDefault();d.classList.add("drag")};d.ondragleave=()=>d.classList.remove("drag");d.ondrop=e=>{e.preventDefault();d.classList.remove("drag");enqueueDriveFiles(e.dataTransfer.files)};
}
function imageHost(){
  app.className="";
  const files=S.imageFiles;
  const folders=S.imageFolders.filter(x=>x.parentId===S.imageFolder);
  const visibleFiles=files.filter(x=>x.name.toLowerCase().includes(S.search.toLowerCase()));
  const allSelected=visibleFiles.length>0&&visibleFiles.every(f=>S.selectedImageIds.has(f.id));
  const view=S.imageViewMode==="list"?"list":"grid";
  app.innerHTML=`<main class="shell"><aside><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>${esc(S.username)}</small></span></div>${navHtml("imageHost")}<button type="button" class="secondary logout" onclick="logout()">退出登录</button></aside><section class="work"><header><div><p class="muted">${files.length} 张图片</p><h1>我的图床</h1></div><div class="mobile-nav">${navHtml("imageHost")}</div><button type="button" class="icon" onclick="refreshImageHost()" title="刷新">↻</button></header>${S.error?`<div class="alert">${esc(S.error)}<button type="button" onclick="S.error='';render()">×</button></div>`:""}<section class="image-toolbar"><div class="crumbs">${imageCrumbs()}</div><div class="view-toggle"><button type="button" class="${view==="grid"?"active":""}" onclick="setImageViewMode('grid')">图片模式</button><button type="button" class="${view==="list"?"active":""}" onclick="setImageViewMode('list')">列表模式</button></div><button type="button" class="secondary" onclick="openImageFolderCreate()">新建文件夹</button><button type="button" id="imageSelectAll" class="secondary" onclick="toggleSelectAll()">${allSelected?"取消全选":"全选"}</button><input class="search" id="imageSearch" placeholder="搜索当前目录" value="${esc(S.search)}"></section>${managementBar("image_host")}<section class="image-drop" id="imageDrop" tabindex="0" role="button"><b>⇧ 拖拽图片到这里上传</b><small>或点击选择图片（JPG、JPEG、PNG、WEBP、GIF）</small><input id="imageFileInput" type="file" accept=".jpg,.jpeg,.png,.webp,.gif,image/jpeg,image/png,image/webp,image/gif" multiple></section><section class="uploads image-uploads" id="imageUploads"></section><section class="${view==="list"?"image-list":"image-grid"}"><div class="sort-group image-folder-group" data-sort-type="folder">${folders.map(imageFolderCard).join("")}</div><div class="sort-group image-file-group" data-sort-type="file">${files.map(view==="list"?imageListRow:imageCard).join("")}</div><div class="empty image-empty" ${folders.length||files.length?"hidden":""}>还没有图片</div></section></section>${imagePreviewModal()}${imageDeleteModal()}${imageFolderModal()}${imageFolderDeleteModal()}${batchDeleteModal()}${moveModalHtml()}<div class="toast" id="appToast" ${S.toast?"":"hidden"}>${esc(S.toast)}</div></main>`;
  app.insertAdjacentHTML("afterbegin",drawerHtml("imageHost"));
  document.querySelector(".work").insertAdjacentHTML("afterbegin",mobileHeader("我的图床",`${files.length} 张图片`,"refreshImageHost()","imageHost"));
  if(S.imageMoreModal)app.insertAdjacentHTML("beforeend",imageMoreSheet());
  updateUploadDom();
  filterVisibleItems();
  initSortables("image_host");
  $("imageSearch").oninput=e=>{S.search=e.target.value;filterVisibleItems();updateImageSelectionDom();initSortables("image_host")};
  const drop=$("imageDrop"),input=$("imageFileInput");
  drop.onclick=()=>input.click();
  drop.onkeydown=e=>{if(e.key==="Enter"||e.key===" "){e.preventDefault();input.click()}};
  input.onchange=e=>enqueueImageFiles(e.target.files);
  drop.ondragenter=e=>{e.preventDefault();drop.classList.add("drag")};
  drop.ondragover=e=>{e.preventDefault();e.dataTransfer.dropEffect="copy";drop.classList.add("drag")};
  drop.ondragleave=e=>{e.preventDefault();drop.classList.remove("drag")};
  drop.ondrop=e=>{e.preventDefault();e.stopPropagation();drop.classList.remove("drag");enqueueImageFiles(e.dataTransfer.files)};
  bindImageModal();
}
async function submitInit(e){e.preventDefault();try{const me=await api("/api/initialize",{method:"POST",body:JSON.stringify(fd(e))});S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch(err){S.error=err.message;render()}}
async function submitLogin(e){e.preventDefault();try{const me=await api("/api/login",{method:"POST",body:JSON.stringify(fd(e))});S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch(err){S.error=err.message;render()}}
async function logout(){await api("/api/logout",{method:"POST"});S.view="login";S.folder="root";S.files=[];S.folders=[];render()}
function openDriveInput(kind,id,name){S.driveModal={mode:"input",kind,id:id||null,name:name||""};renderPreservingScroll();focusWithoutScroll("driveActionName")}
function openDriveConfirm(kind,id,name){S.driveModal={mode:"confirm",kind,id,name:name||""};renderPreservingScroll()}
function closeDriveModal(){S.driveModal=null;renderPreservingScroll()}
function driveModalHtml(){const m=S.driveModal;if(!m)return"";const title=m.kind==="newFolder"?"新建文件夹":m.kind==="renameFolder"?"重命名文件夹":m.kind==="renameFile"?"重命名文件":"确认操作";const promptText=m.kind==="deleteFolder"?`删除空文件夹「${m.name}」？`:m.kind==="deleteFile"?`永久删除「${m.name}」？此操作无法恢复。`:"";return `<div class="modal-backdrop" onclick="if(event.target===this)closeDriveModal()"><form class="modal" id="driveActionForm"><h2>${title}</h2>${m.mode==="input"?`<label><span>名称</span><input id="driveActionName" maxlength="180" value="${esc(m.name)}" required></label>`:`<p>${esc(promptText)}</p>`}<div class="modal-actions"><button type="button" class="secondary" onclick="closeDriveModal()">取消</button><button type="submit" class="primary ${m.mode==="confirm"?"danger-primary":""}">${m.mode==="confirm"?"删除":"确定"}</button></div></form></div>`}
async function submitDriveModal(e){e.preventDefault();const m=S.driveModal;if(!m)return;const name=m.mode==="input"?String($("driveActionName").value||"").trim():"";if(m.mode==="input"&&!name)return;try{if(m.kind==="newFolder")await api("/api/drive/folders",{method:"POST",body:JSON.stringify({name,parentId:S.folder})});else if(m.kind==="renameFolder")await api(`/api/drive/folders/${enc(m.id)}`,{method:"PATCH",body:JSON.stringify({name})});else if(m.kind==="renameFile")await api(`/api/drive/files/${enc(m.id)}`,{method:"PATCH",body:JSON.stringify({name})});else if(m.kind==="deleteFolder")await api(`/api/drive/folders/${enc(m.id)}`,{method:"DELETE"});else if(m.kind==="deleteFile")await api(`/api/drive/files/${enc(m.id)}`,{method:"DELETE"});S.driveModal=null;toast(m.kind.startsWith("delete")?"已删除":m.kind.startsWith("rename")?"已重命名":"文件夹已创建");await refresh()}catch(e){S.driveModal=null;S.error=e.message;render()}}
function newFolder(){openDriveInput("newFolder",null,"")}
function renameFolder(id){const f=S.folders.find(x=>x.id===id);if(f)openDriveInput("renameFolder",id,f.name)}
function deleteFolder(id){const f=S.folders.find(x=>x.id===id);if(f)openDriveConfirm("deleteFolder",id,f.name)}
function renameFile(id){const f=S.files.find(x=>x.id===id);if(f)openDriveInput("renameFile",id,f.name)}
function setDownloadLimit(id){const f=S.files.find(x=>x.id===id);if(!f)return;S.limitModal={id,value:f.downloadLimitBytes==null?"":trimNumber(f.downloadLimitBytes/1024/1024/1024)};renderPreservingScroll();focusWithoutScroll("limitInput")}
function closeDownloadLimit(){S.limitModal=null;renderPreservingScroll()}
async function saveDownloadLimit(e){e.preventDefault();const id=S.limitModal?.id;if(!id)return;const text=String($("limitInput").value||"").trim();let limit=null;if(text!==""){const gb=Number(text);if(!Number.isFinite(gb)||gb<0){S.error="流量限制必须是非负数字";return render()}limit=Math.floor(gb*1024*1024*1024)}try{const row=await api(`/api/drive/files/${enc(id)}`,{method:"PATCH",body:JSON.stringify({downloadLimitBytes:limit})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=row;S.limitModal=null;toast(limit==null?"流量限制已取消":"流量限制已设置");render()}catch(e){S.error=e.message;render()}}
function deleteFile(id){const f=S.files.find(x=>x.id===id);if(f)openDriveConfirm("deleteFile",id,f.name)}
async function togglePublic(id){const f=S.files.find(x=>x.id===id);try{await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:!f.isPublic})});toast(!f.isPublic?"公开链接已生成":"文件已设为私密");await refresh()}catch(e){S.error=e.message;render()}}
async function toggleFolderPublic(id){const f=S.folders.find(x=>x.id===id);try{await api(`/api/drive/folders/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:!f.isPublic})});toast(!f.isPublic?"文件夹已公开":"文件夹已设为私密");await refresh()}catch(e){S.error=e.message;render()}}
function downloadFile(id){const f=S.files.find(x=>x.id===id);if(!f)return;const a=document.createElement("a");a.href=f.downloadUrl;a.download=f.name;a.style.display="none";document.body.appendChild(a);a.click();a.remove()}
async function shareFile(id){let f=S.files.find(x=>x.id===id);if(!f)return;try{if(!f.isPublic){f=await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=f}const url=new URL(f.publicUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("直链已复制");render()}catch(e){S.error=e.message;render()}}
async function shareFilePage(id){let f=S.files.find(x=>x.id===id);if(!f)return;try{if(!f.isPublic){f=await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=f}const url=new URL(f.shareUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("分享页链接已复制");render()}catch(e){S.error=e.message;render()}}
async function shareFolder(id){let f=S.folders.find(x=>x.id===id);if(!f)return;try{if(!f.isPublic){f=await api(`/api/drive/folders/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.folders.findIndex(x=>x.id===id);if(i>=0)S.folders[i]=f}const url=new URL(f.shareUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("文件夹分享链接已复制");render()}catch(e){S.error=e.message;render()}}
async function copyLink(id){const f=S.files.find(x=>x.id===id);const url=new URL(f.publicUrl||f.downloadUrl,location.origin).href;await navigator.clipboard.writeText(url);toast(f.publicUrl?"公开直链已复制":"私密下载地址已复制")}
function enqueueFiles(files,kind){const targetFolderId=kind==="imageHost"?S.imageFolder:S.folder;[...files].forEach(file=>{const t={id:crypto.randomUUID(),name:file.name,size:file.size,file,kind,targetFolderId,progress:0,status:"queued",message:""};S.uploads.push(t);S.uploadQueue.push(t)});updateUploadDom();processNext()}
function enqueueDriveFiles(files){enqueueFiles(files,"drive")}
function enqueueImageFiles(files){enqueueFiles(files,"imageHost")}
async function processNext(){if(S.uploading)return;const t=S.uploadQueue.shift();if(!t)return;S.uploading=true;await uploadTask(t);S.uploading=false;processNext()}
async function uploadTask(t){t.status="uploading";t.progress=0;updateUploadDom();try{const data=new FormData();data.append("folderId",t.targetFolderId);data.append("file",t.file);const xhr=new XMLHttpRequest();await new Promise((res,rej)=>{xhr.upload.onprogress=e=>{if(e.lengthComputable){t.progress=Math.min(99,Math.round(e.loaded/e.total*100));updateUploadDom()}};xhr.onload=()=>xhr.status>=200&&xhr.status<300?res():rej(new Error(parseErr(xhr.responseText)));xhr.onerror=()=>rej(new Error("网络错误"));xhr.open("POST",t.kind==="imageHost"?"/api/image-host/upload":"/api/upload");xhr.send(data)});t.progress=100;t.status="done";updateUploadDom();toast("上传完成");await refreshUploadedTarget(t)}catch(e){t.status="failed";t.message=e.message;S.error=e.message;updateUploadDom();toast(`上传失败：${e.message}`,true)}finally{delete t.file}}
function updateUploadDom(){const drive=$("driveUploads"),images=$("imageUploads");if(drive){const tasks=S.uploads.filter(t=>t.kind!=="imageHost");drive.innerHTML=tasks.map(taskHtml).join("");drive.hidden=!tasks.length}if(images){const tasks=S.uploads.filter(t=>t.kind==="imageHost");images.innerHTML=tasks.map(imageTaskHtml).join("");images.hidden=!tasks.length}}
function filterVisibleItems(){const query=S.search.trim().toLocaleLowerCase();document.querySelectorAll(".row,.image-card,.image-list-row,.image-folder-card").forEach(node=>{const label=node.querySelector(".name b,.image-info b,.image-list-name b,.image-folder-card>b");if(label)node.hidden=!label.textContent.toLocaleLowerCase().includes(query)})}
async function refreshUploadedTarget(t){if(t.kind==="drive"&&S.view==="drive"&&S.folder===t.targetFolderId)await reloadDriveItems();else if(t.kind==="imageHost"&&S.view==="imageHost"&&S.imageFolder===t.targetFolderId)await reloadImageItems()}
async function reloadDriveItems(){const [folders,files,stats]=await Promise.all([api("/api/drive/folders"),api(`/api/drive/files?folderId=${enc(S.folder)}`),api("/api/stats")]);S.folders=folders;S.files=files;S.stats=stats;S.driveSelected=new Set([...S.driveSelected].filter(key=>{const [type,id]=key.split(":");return type==="folder"?folders.some(f=>f.id===id&&f.parentId===S.folder):files.some(f=>f.id===id)}));const folderGroup=document.querySelector(".drive-folder-group"),fileGroup=document.querySelector(".drive-file-group"),empty=document.querySelector(".drive-empty");if(folderGroup)folderGroup.innerHTML=folders.filter(x=>x.parentId===S.folder).map(folderRow).join("");if(fileGroup)fileGroup.innerHTML=files.map(fileRow).join("");if(empty)empty.hidden=folders.some(x=>x.parentId===S.folder)||files.length;filterVisibleItems();updateManagementBar("drive");initSortables("drive")}
async function reloadImageItems(){const [folders,files]=await Promise.all([api("/api/image-host/folders"),api(`/api/image-host/files?folderId=${enc(S.imageFolder)}`)]);S.imageFolders=folders;S.imageFiles=files;S.selectedImageIds=new Set([...S.selectedImageIds].filter(id=>files.some(f=>f.id===id)));S.selectedImageFolderIds=new Set([...S.selectedImageFolderIds].filter(id=>folders.some(f=>f.id===id&&f.parentId===S.imageFolder)));const folderGroup=document.querySelector(".image-folder-group"),fileGroup=document.querySelector(".image-file-group"),empty=document.querySelector(".image-empty"),renderer=S.imageViewMode==="list"?imageListRow:imageCard,currentFolders=folders.filter(x=>x.parentId===S.imageFolder);if(folderGroup)folderGroup.innerHTML=currentFolders.map(imageFolderCard).join("");if(fileGroup)fileGroup.innerHTML=files.map(renderer).join("");if(empty)empty.hidden=currentFolders.length||files.length;filterVisibleItems();updateImageSelectionDom();initSortables("image_host")}
async function api(path,opt={}){const h=new Headers(opt.headers||{});if(opt.body&&typeof opt.body==="string")h.set("content-type","application/json");const r=await fetch(path,{...opt,headers:h});const tx=await r.text();const d=tx?JSON.parse(tx):null;if(!r.ok)throw new Error(d?.error||`请求失败 (${r.status})`);return d}
function imageCard(f){const selected=S.selectedImageIds.has(f.id);return `<article class="image-card ${selected?"selected":""}" data-image-id="${esc(f.id)}" data-item-id="${esc(f.id)}" data-item-type="file"><button type="button" data-select-id="${esc(f.id)}" class="image-select ${selected?"selected":""}" onclick="event.stopPropagation();toggleImageSelection('${esc(f.id)}')" title="选择">${selected?"✓":""}</button><button type="button" class="drag-handle" title="拖动排序">⠿</button><button type="button" class="image-thumb" onclick="previewImage('${esc(f.id)}')" title="预览"><img src="${esc(f.publicUrl)}" alt="${esc(f.name)}" loading="lazy"></button><div class="image-info"><b title="${esc(f.name)}">${esc(f.name)}</b><small>${fmtSize(f.size)} · ${fmtDate(f.updatedAt)}</small></div><div class="image-actions mobile-primary-actions"><button type="button" class="secondary" onclick="previewImage('${esc(f.id)}')">预览</button><button type="button" class="secondary" onclick="copyImageFormat('${esc(f.id)}','direct')">复制直链</button><button type="button" class="secondary mobile-more-button" onclick="openImageMore('${esc(f.id)}')">更多</button><button type="button" class="secondary mobile-hidden-action" onclick="copyImageFormat('${esc(f.id)}','markdown')">复制 Markdown</button><button type="button" class="secondary mobile-hidden-action" onclick="copyImageFormat('${esc(f.id)}','html')">复制 HTML</button><button type="button" class="secondary mobile-hidden-action" onclick="openMove('image_host',[{type:'file',id:'${esc(f.id)}'}])">移动</button><button type="button" class="secondary reorder-button" onclick="moveOrder('image_host','file','${esc(f.id)}',-1)">↑</button><button type="button" class="secondary reorder-button" onclick="moveOrder('image_host','file','${esc(f.id)}',1)">↓</button><button type="button" class="secondary danger-action mobile-hidden-action" onclick="openImageDelete('${esc(f.id)}')">删除</button></div></article>`}
function imageListRow(f){const selected=S.selectedImageIds.has(f.id);return `<article class="image-list-row ${selected?"selected":""}" data-image-id="${esc(f.id)}" data-item-id="${esc(f.id)}" data-item-type="file"><button type="button" data-select-id="${esc(f.id)}" class="image-select image-list-select ${selected?"selected":""}" onclick="toggleImageSelection('${esc(f.id)}')" title="选择">${selected?"✓":""}</button><button type="button" class="drag-handle" title="拖动排序">⠿</button><img src="${esc(f.publicUrl)}" alt="${esc(f.name)}" loading="lazy" onclick="previewImage('${esc(f.id)}')"><div class="image-list-name"><b title="${esc(f.name)}">${esc(f.name)}</b><small class="image-list-meta">${esc(f.contentType||"图片")}</small></div><span class="image-list-size">${fmtSize(f.size)}</span><span class="image-list-date">${fmtDate(f.updatedAt)}</span><div class="image-list-actions mobile-primary-actions"><button type="button" class="secondary" onclick="previewImage('${esc(f.id)}')">预览</button><button type="button" class="secondary" onclick="copyImageFormat('${esc(f.id)}','direct')">直链</button><button type="button" class="secondary mobile-more-button" onclick="openImageMore('${esc(f.id)}')">更多</button><button type="button" class="secondary mobile-hidden-action" onclick="copyImageFormat('${esc(f.id)}','markdown')">Markdown</button><button type="button" class="secondary mobile-hidden-action" onclick="copyImageFormat('${esc(f.id)}','html')">HTML</button><button type="button" class="secondary mobile-hidden-action" onclick="openMove('image_host',[{type:'file',id:'${esc(f.id)}'}])">移动</button><button type="button" class="secondary reorder-button" onclick="moveOrder('image_host','file','${esc(f.id)}',-1)">↑</button><button type="button" class="secondary reorder-button" onclick="moveOrder('image_host','file','${esc(f.id)}',1)">↓</button><button type="button" class="secondary danger-action mobile-hidden-action" onclick="openImageDelete('${esc(f.id)}')">删除</button></div></article>`}
function imageFolderCard(f){const selected=S.selectedImageFolderIds.has(f.id);return `<article class="image-folder-card ${selected?"selected":""}" data-item-id="${esc(f.id)}" data-item-type="folder" onclick="enterImageFolder('${esc(f.id)}')"><button type="button" class="item-select ${selected?"selected":""}" onclick="event.stopPropagation();toggleImageFolderSelection('${esc(f.id)}')" title="选择">${selected?"✓":""}</button><button type="button" class="drag-handle" onclick="event.stopPropagation()" title="拖动排序">⠿</button><div style="font-size:34px">📁</div><b>${esc(f.name)}</b><small>${f.imageCount||0} 张图片</small><div class="image-actions"><button class="secondary" onclick="event.stopPropagation();openMove('image_host',[{type:'folder',id:'${esc(f.id)}'}])">移动</button><button class="secondary reorder-button" onclick="event.stopPropagation();moveOrder('image_host','folder','${esc(f.id)}',-1)">↑</button><button class="secondary reorder-button" onclick="event.stopPropagation();moveOrder('image_host','folder','${esc(f.id)}',1)">↓</button><button class="secondary" onclick="event.stopPropagation();openImageFolderRename('${esc(f.id)}')">重命名</button><button class="secondary danger-action" onclick="event.stopPropagation();openImageFolderDelete('${esc(f.id)}')">删除</button></div></article>`}
function imagePreviewModal(){const f=S.imageFiles.find(x=>x.id===S.imagePreview);if(!f)return"";return `<div class="modal-backdrop image-preview-backdrop" onclick="if(event.target===this)closeImagePreview()"><div class="image-preview-modal"><button class="icon image-close" onclick="closeImagePreview()" title="关闭">×</button><img src="${esc(f.publicUrl)}" alt="${esc(f.name)}"><p>${esc(f.name)}</p></div></div>`}
function imageDeleteModal(){const f=S.imageFiles.find(x=>x.id===S.imageDeleteModal);if(!f)return"";return `<div class="modal-backdrop" onclick="if(event.target===this)closeImageDelete()"><div class="modal"><h2>删除图片？</h2><p>${esc(f.name)}</p><div class="modal-actions"><button type="button" class="secondary" onclick="closeImageDelete()">取消</button><button type="button" class="primary danger-primary" onclick="confirmImageDelete()">删除</button></div></div></div>`}
function bindImageModal(){document.onkeydown=e=>{if(e.key!=="Escape")return;if(document.querySelector(".mobile-drawer.open")){closeDrawer();return}if(S.imagePreview)closeImagePreview();else if(S.imageDeleteModal)closeImageDelete();else if(S.imageBatchDeleteModal)closeBatchDelete();else if(S.moveModal)closeMove();else if(S.imageMoreModal)closeImageMore();else if(S.imageFolderModal)closeImageFolderModal();else if(S.imageFolderDeleteModal)closeImageFolderDelete()};if(S.imageFolderModal){const form=$("imageFolderForm");if(form)form.onsubmit=submitImageFolderModal}}
function previewImage(id){S.imagePreview=id;renderPreservingScroll()}
function closeImagePreview(){S.imagePreview=null;renderPreservingScroll()}
function openImageDelete(id){S.imageDeleteModal=id;renderPreservingScroll()}
function closeImageDelete(){S.imageDeleteModal=null;renderPreservingScroll()}
function openImageMore(id){S.imageMoreModal=id;renderPreservingScroll()}
function closeImageMore(){S.imageMoreModal=null;renderPreservingScroll()}
function imageMoreSheet(){const f=S.imageFiles.find(x=>x.id===S.imageMoreModal);if(!f)return"";return `<div class="image-more-sheet open" onclick="if(event.target===this)closeImageMore()"><div class="image-more-panel"><h3>${esc(f.name)}</h3><button type="button" onclick="copyImageFormat('${esc(f.id)}','markdown');closeImageMore()">复制 Markdown</button><button type="button" onclick="copyImageFormat('${esc(f.id)}','html');closeImageMore()">复制 HTML</button><button type="button" onclick="closeImageMore();openImageMove(['${esc(f.id)}'])">移动</button><button type="button" class="danger-action" onclick="closeImageMore();openImageDelete('${esc(f.id)}')">删除</button><button type="button" onclick="closeImageMore()">取消</button></div></div>`}
async function confirmImageDelete(){const id=S.imageDeleteModal;if(!id)return;try{await api(`/api/image-host/files/${enc(id)}`,{method:"DELETE"});S.imageDeleteModal=null;toast("图片已删除");await refreshImageHost()}catch(e){S.imageDeleteModal=null;toast("删除失败")}}
async function copyImageFormat(id,format){const f=S.imageFiles.find(x=>x.id===id);if(!f)return;const url=new URL(f.publicUrl,location.origin).href;const text=format==="direct"?url:format==="markdown"?`![${f.name}](${url})`:`<img src="${url}" alt="${f.name}">`;try{await navigator.clipboard.writeText(text);toast(format==="direct"?"直链已复制":format==="markdown"?"Markdown 已复制":"HTML 已复制")}catch(e){toast("复制失败")}}
function imageScrollTop(){const work=document.querySelector(".work"),mobile=matchMedia("(max-width:920px)").matches;return !mobile&&work?work.scrollTop:(document.scrollingElement?.scrollTop||window.scrollY)}
function restoreImageScroll(scroll){const work=document.querySelector(".work"),mobile=matchMedia("(max-width:920px)").matches;if(!mobile&&work)work.scrollTop=scroll;else window.scrollTo(0,scroll)}
function renderPreservingScroll(){const scroll=imageScrollTop();render();restoreImageScroll(scroll);requestAnimationFrame(()=>restoreImageScroll(scroll))}
function focusWithoutScroll(id){requestAnimationFrame(()=>$(id)?.focus({preventScroll:true}))}
function updateImageSelectionDom(){const visible=S.imageFiles.filter(x=>x.name.toLowerCase().includes(S.search.toLowerCase()));document.querySelectorAll("[data-image-id]").forEach(row=>{const id=row.dataset.imageId,selected=S.selectedImageIds.has(id);row.classList.toggle("selected",selected);const control=row.querySelector("[data-select-id]");if(control){control.classList.toggle("selected",selected);control.textContent=selected?"✓":""}});document.querySelectorAll('[data-item-type="folder"]').forEach(row=>{const selected=S.selectedImageFolderIds.has(row.dataset.itemId);row.classList.toggle("selected",selected);const control=row.querySelector(".item-select");if(control){control.classList.toggle("selected",selected);control.textContent=selected?"✓":""}});const all=visible.length>0&&visible.every(f=>S.selectedImageIds.has(f.id)),selectAll=$("imageSelectAll");if(selectAll)selectAll.textContent=all?"取消全选":"全选";updateManagementBar("image_host")}
function setImageViewMode(mode){S.imageViewMode=mode==="list"?"list":"grid";localStorage.setItem("r2_image_view_mode",S.imageViewMode);const scroll=imageScrollTop();render();requestAnimationFrame(()=>restoreImageScroll(scroll))}
function toggleImageSelection(id){if(S.selectedImageIds.has(id))S.selectedImageIds.delete(id);else S.selectedImageIds.add(id);updateImageSelectionDom()}
function toggleImageFolderSelection(id){if(S.selectedImageFolderIds.has(id))S.selectedImageFolderIds.delete(id);else S.selectedImageFolderIds.add(id);updateImageSelectionDom()}
function toggleSelectAll(){const files=S.imageFiles.filter(x=>x.name.toLowerCase().includes(S.search.toLowerCase()));const all=files.length>0&&files.every(f=>S.selectedImageIds.has(f.id));files.forEach(f=>all?S.selectedImageIds.delete(f.id):S.selectedImageIds.add(f.id));updateImageSelectionDom()}
function clearImageSelection(){S.selectedImageIds.clear();S.selectedImageFolderIds.clear();updateImageSelectionDom()}
function enterImageFolder(id){S.imageFolder=id;S.search="";clearAllSelections();refreshImageHost()}
function imageCrumbs(){const arr=[{id:"root",name:"我的图床"}];let c=S.imageFolder,chain=[];while(c!=="root"){const f=S.imageFolders.find(x=>x.id===c);if(!f)break;chain.unshift(f);c=f.parentId}arr.push(...chain);return arr.map(x=>`<button onclick="S.imageFolder='${esc(x.id)}';S.search='';clearAllSelections();refreshImageHost()">${esc(x.name)}</button>`).join("<span>/</span>")}
function openImageFolderCreate(){S.imageFolderModal={mode:"create",id:null,name:""};renderPreservingScroll();focusWithoutScroll("imageFolderName")}
function openImageFolderRename(id){const f=S.imageFolders.find(x=>x.id===id);if(f){S.imageFolderModal={mode:"rename",id,name:f.name};renderPreservingScroll();focusWithoutScroll("imageFolderName")}}
function closeImageFolderModal(){S.imageFolderModal=null;renderPreservingScroll()}
async function submitImageFolderModal(e){e.preventDefault();const m=S.imageFolderModal;if(!m)return;const name=String($("imageFolderName").value||"").trim();if(!name)return;try{if(m.mode==="create"){await api("/api/image-host/folders",{method:"POST",body:JSON.stringify({name,parentId:S.imageFolder})});toast("文件夹已创建")}else{await api(`/api/image-host/folders/${enc(m.id)}`,{method:"PATCH",body:JSON.stringify({name})});toast("文件夹已重命名")}S.imageFolderModal=null;await refreshImageHost()}catch(err){toast(err.message)}}
function imageFolderModal(){const m=S.imageFolderModal;if(!m)return"";return `<div class="modal-backdrop" onclick="if(event.target===this)closeImageFolderModal()"><form class="modal" id="imageFolderForm"><h2>${m.mode==="create"?"新建图床文件夹":"重命名图床文件夹"}</h2><label><span>文件夹名称</span><input id="imageFolderName" maxlength="80" value="${esc(m.name)}" required></label><div class="modal-actions"><button type="button" class="secondary" onclick="closeImageFolderModal()">取消</button><button class="primary">${m.mode==="create"?"创建":"保存"}</button></div></form></div>`}
function openImageFolderDelete(id){S.imageFolderDeleteModal=id;renderPreservingScroll()}
function closeImageFolderDelete(){S.imageFolderDeleteModal=null;renderPreservingScroll()}
function imageFolderDeleteModal(){const f=S.imageFolders.find(x=>x.id===S.imageFolderDeleteModal);if(!f)return"";return `<div class="modal-backdrop" onclick="if(event.target===this)closeImageFolderDelete()"><div class="modal"><h2>删除文件夹？</h2><p>${esc(f.name)}</p><div class="modal-actions"><button class="secondary" onclick="closeImageFolderDelete()">取消</button><button class="primary danger-primary" onclick="confirmImageFolderDelete()">删除</button></div></div></div>`}
async function confirmImageFolderDelete(){const id=S.imageFolderDeleteModal;if(!id)return;try{await api(`/api/image-host/folders/${enc(id)}`,{method:"DELETE"});S.imageFolderDeleteModal=null;toast("文件夹已删除");await refreshImageHost()}catch(e){toast(e.message)}}
function openBatchDelete(){if(S.selectedImageIds.size){S.imageBatchDeleteModal=true;renderPreservingScroll()}}
function closeBatchDelete(){S.imageBatchDeleteModal=false;renderPreservingScroll()}
function batchDeleteModal(){if(!S.imageBatchDeleteModal)return"";return `<div class="modal-backdrop" onclick="if(event.target===this)closeBatchDelete()"><div class="modal"><h2>确认删除选中的 ${S.selectedImageIds.size} 张图片？</h2><p>删除后无法恢复。</p><div class="modal-actions"><button class="secondary" onclick="closeBatchDelete()">取消</button><button class="primary danger-primary" onclick="confirmBatchDelete()">删除</button></div></div></div>`}
async function confirmBatchDelete(){const ids=[...S.selectedImageIds];if(!ids.length)return;try{const result=await api("/api/image-host/files/batch-delete",{method:"POST",body:JSON.stringify({ids})});S.selectedImageIds.clear();S.imageBatchDeleteModal=false;toast(result.failed?.length?`已删除 ${result.deleted.length} 项，${result.failed.length} 项失败`:"图片已删除");await refreshImageHost()}catch(e){toast("删除失败")}}
function openImageMove(ids){const items=[...new Set((ids||[]).filter(Boolean))].map(id=>({type:"file",id}));openMove("image_host",items)}
function closeImageMove(){closeMove()}
function selectedItems(category){if(category==="drive")return [...S.driveSelected].map(key=>{const [type,...parts]=key.split(":");return{type,id:parts.join(":")}});return[...S.selectedImageFolderIds].map(id=>({type:"folder",id})).concat([...S.selectedImageIds].map(id=>({type:"file",id})))}
function managementBar(category){const items=selectedItems(category),canDelete=category==="image_host"&&items.length&&items.every(x=>x.type==="file"),id=category==="image_host"?"imageSelectionBar":"managementBar";return `<section class="management-bar" id="${id}" ${items.length?"":"hidden"}><span class="selection-count">已选择 ${items.length} 项</span><span class="spacer"></span><button type="button" class="secondary" onclick="clearAllSelections();updateManagementBar('${category}')">取消选择</button><button type="button" class="primary" onclick="openMove('${category}',selectedItems('${category}'))">移动到</button>${category==="image_host"?`<button type="button" id="imageBatchDeleteButton" class="primary danger-primary" ${canDelete?"":"hidden"} onclick="openBatchDelete()">删除</button>`:""}</section>`}
function updateManagementBar(category){const bar=$(category==="image_host"?"imageSelectionBar":"managementBar");if(!bar)return;const items=selectedItems(category),count=bar.querySelector(".selection-count"),deleteButton=$("imageBatchDeleteButton");bar.hidden=!items.length;if(count)count.textContent=`已选择 ${items.length} 项`;if(deleteButton)deleteButton.hidden=!(items.length&&items.every(x=>x.type==="file"))}
function clearAllSelections(){S.driveSelected.clear();S.selectedImageIds.clear();S.selectedImageFolderIds.clear();document.querySelectorAll(".selected").forEach(node=>node.classList.remove("selected"));document.querySelectorAll(".item-select,.image-select").forEach(node=>node.textContent="")}
function toggleDriveSelection(type,id){const key=`${type}:${id}`;if(S.driveSelected.has(key))S.driveSelected.delete(key);else S.driveSelected.add(key);const row=document.querySelector(`[data-item-type="${type}"][data-item-id="${CSS.escape(id)}"]`);if(row){const selected=S.driveSelected.has(key);row.classList.toggle("selected",selected);const button=row.querySelector(".item-select");if(button){button.classList.toggle("selected",selected);button.textContent=selected?"✓":""}}updateManagementBar("drive")}
function openMove(category,items){const unique=[],seen=new Set();for(const item of items||[]){const key=`${item.type}:${item.id}`;if((item.type==="folder"||item.type==="file")&&item.id&&!seen.has(key)){seen.add(key);unique.push({type:item.type,id:item.id})}}if(!unique.length)return;S.moveModal={category,items:unique,folderId:category==="drive"?S.folder:S.imageFolder,conflictPolicy:"cancel"};renderPreservingScroll()}
function closeMove(){S.moveModal=null;renderPreservingScroll()}
function setMoveFolder(id){if(!S.moveModal)return;S.moveModal.folderId=id;renderPreservingScroll()}
function moveFolderList(){return S.moveModal?.category==="drive"?S.folders:S.imageFolders}
function moveCrumbs(folderId){const folders=moveFolderList(),rootName=S.moveModal?.category==="drive"?"我的网盘":"我的图床",arr=[{id:"root",name:rootName}];let current=folderId,chain=[];while(current!=="root"){const folder=folders.find(x=>x.id===current);if(!folder)break;chain.unshift(folder);current=folder.parentId}arr.push(...chain);return arr.map((x,i)=>`${i?"<span>/</span>":""}<button type="button" onclick="setMoveFolder('${esc(x.id)}')">${esc(x.name)}</button>`).join("")}
function folderUnderAnySelected(id){const folders=moveFolderList(),selected=new Set((S.moveModal?.items||[]).filter(x=>x.type==="folder").map(x=>x.id));let current=id,seen=new Set();while(current!=="root"&&!seen.has(current)){if(selected.has(current))return true;seen.add(current);current=folders.find(x=>x.id===current)?.parentId||"root"}return false}
function moveModalHtml(){const modal=S.moveModal;if(!modal)return"";const folders=moveFolderList().filter(x=>x.parentId===modal.folderId&&!folderUnderAnySelected(x.id));return `<div class="modal-backdrop" id="moveBackdrop" onclick="if(event.target===this)closeMove()"><div class="modal move-modal"><h2>移动项目</h2><p>选择 ${modal.items.length} 项的目标目录</p><div class="move-crumbs">${moveCrumbs(modal.folderId)}</div><div class="move-folders">${folders.map(f=>`<button type="button" class="move-folder" onclick="setMoveFolder('${esc(f.id)}')"><span>📁</span><span>${esc(f.name)}</span></button>`).join("")||`<div class="image-move-empty">这里没有可用的子文件夹</div>`}</div><label class="conflict-choice"><span>同名冲突</span><select id="conflictPolicy" onchange="S.moveModal.conflictPolicy=this.value"><option value="cancel">取消整个操作</option><option value="rename">自动重命名</option><option value="skip">跳过冲突项</option></select></label><div class="modal-actions"><button type="button" class="secondary" onclick="closeMove()">取消</button><button type="button" class="primary" onclick="confirmMove()">移动到此文件夹</button></div></div></div>`}
function moveReason(reason){return({not_found:"源项目不存在",cycle:"目标位于所选文件夹内部",name_conflict:"目标存在同名项目",covered_by_parent:"已随父文件夹移动",same_folder:"已经位于目标目录"})[reason]||reason||"未知原因"}
async function confirmMove(){const modal=S.moveModal;if(!modal)return;const button=document.querySelector(".move-modal .primary");if(button)button.disabled=true;try{const result=await api("/api/items/move",{method:"POST",body:JSON.stringify({category:modal.category,items:modal.items,folderId:modal.folderId,conflictPolicy:modal.conflictPolicy})});S.moveModal=null;clearAllSelections();$("moveBackdrop")?.remove();if(modal.category==="drive")await reloadDriveItems();else await reloadImageItems();const moved=result.moved?.length||0,skipped=result.skipped?.length||0,failed=result.failed?.length||0,detail=failed?moveReason(result.failed[0]?.reason):skipped?moveReason(result.skipped[0]?.reason):"";toast(`移动完成：成功 ${moved}，跳过 ${skipped}，失败 ${failed}${detail?`；${detail}`:""}`)}catch(e){if(button)button.disabled=false;toast(e.message||"移动失败")}}
function destroySortables(){for(const sortable of S.sortables||[])sortable.destroy();S.sortables=[]}
function initSortables(category){destroySortables();if(typeof Sortable==="undefined"||matchMedia("(max-width:920px)").matches||S.search.trim())return;const selector=category==="drive"?[".drive-folder-group",".drive-file-group"]:[".image-folder-group",".image-file-group"];for(const value of selector){const node=document.querySelector(value);if(!node||node.children.length<2)continue;const itemType=node.dataset.sortType;S.sortables.push(new Sortable(node,{animation:150,handle:".drag-handle",draggable:"[data-item-id]",ghostClass:"sortable-ghost",chosenClass:"sortable-chosen",onEnd:event=>{if(event.oldIndex===event.newIndex)return;persistOrder(category,itemType,[...node.querySelectorAll(":scope > [data-item-id]")].map(item=>item.dataset.itemId))}}))}}
async function persistOrder(category,itemType,ids){const parentId=category==="drive"?S.folder:S.imageFolder;try{await api("/api/items/reorder",{method:"POST",body:JSON.stringify({category,itemType,parentId,ids})});if(category==="drive")await reloadDriveItems();else await reloadImageItems();toast("顺序已保存")}catch(e){toast(e.message||"排序失败");if(category==="drive")await reloadDriveItems();else await reloadImageItems()}}
async function moveOrder(category,itemType,id,delta){if(S.search.trim())return toast("搜索结果中不能调整顺序");const parentId=category==="drive"?S.folder:S.imageFolder,folders=category==="drive"?S.folders:S.imageFolders,files=category==="drive"?S.files:S.imageFiles,items=itemType==="folder"?folders.filter(x=>x.parentId===parentId):files,ids=items.map(x=>x.id),index=ids.indexOf(id),next=index+delta;if(index<0||next<0||next>=ids.length)return toast(delta<0?"已经在最上方":"已经在最下方");[ids[index],ids[next]]=[ids[next],ids[index]];await persistOrder(category,itemType,ids)}
function crumbs(){const arr=[{id:"root",name:"我的网盘"}];let c=S.folder, chain=[];while(c!=="root"){const f=S.folders.find(x=>x.id===c);if(!f)break;chain.unshift(f);c=f.parentId}arr.push(...chain);return arr.map(x=>`<button onclick="S.folder='${esc(x.id)}';S.search='';clearAllSelections();refresh()">${esc(x.name)}</button>`).join("<span>/</span>")}
function parentOf(id){return S.folders.find(x=>x.id===id)?.parentId||"root"}
function parentRow(){return `<article class="row"><button class="name" onclick="S.folder='${esc(parentOf(S.folder))}';S.search='';clearAllSelections();refresh()"><span class="ico">📁</span><span><b>返回上级目录</b><small>Parent folder</small></span></button><span class="count-cell"></span><span class="traffic-cell"></span><span class="limit-cell"></span><span class="size-cell">-</span><span class="privacy-cell">-</span><span class="updated-cell">-</span><span class="actions"></span></article>`}
function folderRow(f){const key=`folder:${f.id}`,selected=S.driveSelected.has(key);return `<article class="row ${selected?"selected":""}" data-item-id="${esc(f.id)}" data-item-type="folder"><span class="item-name-cell"><button type="button" class="item-select ${selected?"selected":""}" onclick="toggleDriveSelection('folder','${esc(f.id)}')" title="选择">${selected?"✓":""}</button><button type="button" class="drag-handle" title="拖动排序">⠿</button><button class="name" onclick="S.folder='${esc(f.id)}';S.search='';clearAllSelections();refresh()"><span class="ico">📁</span><span><b>${esc(f.name)}</b><small>文件夹</small></span></button></span><span class="count-cell"></span><span class="traffic-cell"></span><span class="limit-cell"></span><span class="size-cell">-</span><span class="privacy-cell"><button class="privacy ${f.isPublic?"public":"private"}" onclick="toggleFolderPublic('${esc(f.id)}')">${f.isPublic?"公开":"私密"}</button></span><span class="updated-cell">${f.updatedAt?fmtDate(f.updatedAt):"-"}</span><span class="actions"><button onclick="openMove('drive',[{type:'folder',id:'${esc(f.id)}'}])" title="移动">↪</button><button onclick="renameFolder('${esc(f.id)}')" title="重命名">✎</button><button class="reorder-button" onclick="moveOrder('drive','folder','${esc(f.id)}',-1)" title="上移">↑</button><button class="reorder-button" onclick="moveOrder('drive','folder','${esc(f.id)}',1)" title="下移">↓</button><button onclick="shareFolder('${esc(f.id)}')" title="分享">🔗</button><button onclick="deleteFolder('${esc(f.id)}')" title="删除">🗑</button></span></article>`}
function fileRow(f){const key=`file:${f.id}`,selected=S.driveSelected.has(key);return `<article class="row ${selected?"selected":""}" data-item-id="${esc(f.id)}" data-item-type="file"><span class="item-name-cell"><button type="button" class="item-select ${selected?"selected":""}" onclick="toggleDriveSelection('file','${esc(f.id)}')" title="选择">${selected?"✓":""}</button><button type="button" class="drag-handle" title="拖动排序">⠿</button><button class="name" onclick="downloadFile('${esc(f.id)}')"><span class="ico">📄</span><span><b>${esc(f.name)}</b><small>${esc(f.contentType)}</small></span></button></span><span class="count-cell">${f.downloadCount||0}</span><span class="traffic-cell">${fmtSize(f.downloadBytes||0)}</span><span class="limit-cell"><button class="limit-btn" onclick="setDownloadLimit('${esc(f.id)}')" title="设置流量限制">${fmtLimit(f.downloadLimitBytes)}</button></span><span class="size-cell">${fmtSize(f.size)}</span><span class="privacy-cell"><button class="privacy ${f.isPublic?"public":"private"}" onclick="togglePublic('${esc(f.id)}')">${f.isPublic?"公开":"私密"}</button></span><span class="updated-cell">${fmtDate(f.updatedAt)}</span><span class="actions file-actions"><button onclick="openMove('drive',[{type:'file',id:'${esc(f.id)}'}])" title="移动">↪</button><button class="reorder-button" onclick="moveOrder('drive','file','${esc(f.id)}',-1)" title="上移">↑</button><button class="reorder-button" onclick="moveOrder('drive','file','${esc(f.id)}',1)" title="下移">↓</button><button onclick="downloadFile('${esc(f.id)}')" title="下载">⇩</button><button onclick="shareFile('${esc(f.id)}')" title="分享直链">🔗</button><button onclick="shareFilePage('${esc(f.id)}')" title="分享页">📄</button><button onclick="renameFile('${esc(f.id)}')" title="重命名">✎</button><button onclick="deleteFile('${esc(f.id)}')" title="删除">🗑</button></span></article>`}
function limitModal(){if(!S.limitModal)return"";const f=S.files.find(x=>x.id===S.limitModal.id);return `<div class="modal-backdrop" onclick="if(event.target===this)closeDownloadLimit()"><form class="modal" id="limitForm"><h2>设置下载流量限制</h2><p>${esc(f?.name||"")}</p><label><span>最大下载流量</span><span class="limit-field"><input id="limitInput" type="number" min="0" step="0.01" value="${esc(S.limitModal.value)}"><span>GB</span></span></label><div class="modal-actions"><button type="button" class="secondary" onclick="closeDownloadLimit()">取消</button><button class="primary">确定</button></div></form></div>`}
function taskHtml(t){const status=t.status==="failed"?esc(t.message||"上传失败"):t.status==="queued"?"排队中":t.status==="done"?"上传完成":`上传中 ${t.progress}%`;return `<article class="task"><div><b>${esc(t.name)}</b><span>${status}</span></div>${t.status==="uploading"?`<div class="bar"><i style="width:${t.progress}%"></i></div>`:""}</article>`}
function imageTaskHtml(t){const status=t.status==="failed"?"上传失败":t.status==="queued"?"排队中":t.status==="done"?"上传完成":`上传中 ${t.progress}%`;return `<article class="task image-task ${t.status}"><div><b>${esc(t.name)}</b><span>${fmtSize(t.size||0)} · ${status}</span></div>${t.status==="uploading"?`<div class="bar"><i style="width:${t.progress}%"></i></div>`:t.status==="failed"?`<small class="task-error">${esc(t.message||"上传失败")}</small>`:""}</article>`}
function fd(e){const d=new FormData(e.target);return {username:String(d.get("username")||""),password:String(d.get("password")||"")}}
function fmtSize(n){if(!n)return"0 B";const u=["B","KB","MB","GB","TB"];const i=Math.min(Math.floor(Math.log(n)/Math.log(1024)),u.length-1);return`${(n/1024**i).toFixed(i?1:0)} ${u[i]}`}
function fmtLimit(n){if(n==null)return"不限";const gb=1024**3, mb=1024**2;return n>=gb?`${trimNumber(n/gb)} GB`:`${trimNumber(n/mb)} MB`}
function trimNumber(n){return Number(n.toFixed(2)).toString()}
function fmtDate(v){return new Date(v*1000).toLocaleString("zh-CN",{hour12:false})}
function toast(m,priority=false){const currentTime=Date.now();if(!priority&&S.toastPriorityUntil>currentTime)return;if(priority)S.toastPriorityUntil=currentTime+4000;S.toast=m;const node=$("appToast");if(node){node.textContent=m;node.hidden=false}setTimeout(()=>{if(S.toast===m){S.toast="";const current=$("appToast");if(current)current.hidden=true}},priority?4000:2200)}
function parseErr(t){try{return JSON.parse(t).error||"请求失败"}catch{return"请求失败"}}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]))}
function enc(s){return encodeURIComponent(s)}
</script></body></html>"""


class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def init_db():
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(STORAGE_DIR, exist_ok=True)
    with db() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              salt TEXT NOT NULL,
              role TEXT NOT NULL DEFAULT 'admin',
              disabled INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              token_hash TEXT NOT NULL UNIQUE,
              expires_at INTEGER NOT NULL,
              created_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS folders (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              parent_id TEXT NOT NULL DEFAULT 'root',
              name TEXT NOT NULL,
              share_token TEXT UNIQUE,
              folder_category TEXT NOT NULL DEFAULT 'drive',
              sort_order INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_folders_user_parent ON folders(user_id, parent_id);
            CREATE TABLE IF NOT EXISTS files (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              folder_id TEXT NOT NULL DEFAULT 'root',
              name TEXT NOT NULL,
              storage_path TEXT NOT NULL,
              size INTEGER NOT NULL,
              content_type TEXT NOT NULL,
              download_count INTEGER NOT NULL DEFAULT 0,
              download_bytes INTEGER NOT NULL DEFAULT 0,
              download_limit_bytes INTEGER DEFAULT NULL,
              is_public INTEGER NOT NULL DEFAULT 0,
              share_token TEXT UNIQUE,
              file_category TEXT NOT NULL DEFAULT 'drive',
              sort_order INTEGER NOT NULL DEFAULT 0,
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_files_user_folder ON files(user_id, folder_id);
            CREATE INDEX IF NOT EXISTS idx_files_share ON files(share_token);
            """
        )
        ensure_column(conn, "folders", "share_token", "TEXT")
        ensure_column(conn, "folders", "folder_category", "TEXT NOT NULL DEFAULT 'drive'")
        ensure_column(conn, "files", "download_count", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "files", "download_bytes", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "files", "download_limit_bytes", "INTEGER DEFAULT NULL")
        ensure_column(conn, "files", "file_category", "TEXT NOT NULL DEFAULT 'drive'")
        folders_need_order = ensure_column(conn, "folders", "sort_order", "INTEGER NOT NULL DEFAULT 0")
        files_need_order = ensure_column(conn, "files", "sort_order", "INTEGER NOT NULL DEFAULT 0")
        if folders_need_order:
            initialize_sort_orders(conn, "folders")
        if files_need_order:
            initialize_sort_orders(conn, "files")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_share ON folders(share_token) WHERE share_token IS NOT NULL")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_folders_user_category ON folders(user_id, folder_category, parent_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_user_category ON files(user_id, file_category, updated_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_folders_sort ON folders(user_id, folder_category, parent_id, sort_order)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_files_sort ON files(user_id, file_category, folder_id, sort_order)")


def db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=15000")
    return conn


def ensure_column(conn, table, column, definition):
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        return True
    return False


def initialize_sort_orders(conn, table):
    parent_column = "parent_id" if table == "folders" else "folder_id"
    category_column = "folder_category" if table == "folders" else "file_category"
    legacy_order = "name COLLATE NOCASE, id" if table == "folders" else "updated_at DESC, id"
    groups = conn.execute(
        f"SELECT DISTINCT user_id, {category_column} AS category, {parent_column} AS parent_id FROM {table}"
    ).fetchall()
    for group in groups:
        rows = conn.execute(
            f"SELECT id FROM {table} WHERE user_id = ? AND {category_column} = ? AND {parent_column} = ? ORDER BY {legacy_order}",
            (group["user_id"], group["category"], group["parent_id"]),
        ).fetchall()
        for position, row in enumerate(rows):
            conn.execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?", (position, row["id"]))


def next_sort_order(conn, table, user_id, category, parent_id):
    parent_column = "parent_id" if table == "folders" else "folder_id"
    category_column = "folder_category" if table == "folders" else "file_category"
    row = conn.execute(
        f"SELECT COALESCE(MAX(sort_order), -1) + 1 AS next_order FROM {table} WHERE user_id = ? AND {category_column} = ? AND {parent_column} = ?",
        (user_id, category, parent_id),
    ).fetchone()
    return int(row["next_order"])


def compact_sort_orders(conn, table, user_id, category, parent_id):
    parent_column = "parent_id" if table == "folders" else "folder_id"
    category_column = "folder_category" if table == "folders" else "file_category"
    rows = conn.execute(
        f"SELECT id FROM {table} WHERE user_id = ? AND {category_column} = ? AND {parent_column} = ? ORDER BY sort_order, id",
        (user_id, category, parent_id),
    ).fetchall()
    for position, row in enumerate(rows):
        conn.execute(f"UPDATE {table} SET sort_order = ? WHERE id = ?", (position, row["id"]))


class Handler(BaseHTTPRequestHandler):
    server_version = "R2DriveVPS/0.1"

    def do_HEAD(self):
        self.route()

    def do_GET(self):
        self.route()

    def do_POST(self):
        self.route()

    def do_PATCH(self):
        self.route()

    def do_DELETE(self):
        self.route()

    def route(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            if path.startswith("/api/"):
                return self.api(path, parsed)
            if path.startswith("/share/folder/"):
                return self.folder_share_route(path, parsed)
            if path.startswith("/share/"):
                return self.share_page(path)
            if path.startswith("/public/"):
                return self.public_file(path)
            if path == "/vendor/sortablejs/Sortable.min.js" and self.command in ("GET", "HEAD"):
                return self.send_asset(os.path.join(SOURCE_DIR, "vendor", "sortablejs", "Sortable.min.js"), "text/javascript; charset=utf-8")
            if self.command in ("GET", "HEAD"):
                return self.html(INDEX_HTML.replace("<title>R2 Drive</title>", f"<title>{html.escape(SITE_NAME)}</title>"))
            raise HttpError(404, "Not found")
        except HttpError as exc:
            self.json({"error": exc.message}, exc.status)
        except Exception:
            self.json({"error": "服务器错误"}, 500)

    def api(self, path, parsed):
        if self.command == "GET" and path == "/api/status":
            with db() as conn:
                count = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
            return self.json({"initialized": count > 0, "siteName": SITE_NAME})
        if self.command == "POST" and path == "/api/initialize":
            return self.initialize()
        if self.command == "POST" and path == "/api/login":
            return self.login()
        if self.command == "POST" and path == "/api/logout":
            return self.logout()

        user = self.require_auth()
        if self.command == "GET" and path == "/api/me":
            return self.json({"username": user["username"], "role": user["role"]})
        if self.command == "GET" and path == "/api/stats":
            return self.stats(user)
        if self.command == "GET" and path == "/api/image-host/files":
            qs = urllib.parse.parse_qs(parsed.query)
            return self.list_image_host_files(user, qs.get("folderId", ["root"])[0])
        if self.command == "GET" and path == "/api/image-host/folders":
            return self.list_image_host_folders(user)
        if self.command == "POST" and path == "/api/image-host/folders":
            return self.create_image_host_folder(user)
        if self.command == "POST" and path == "/api/image-host/upload":
            return self.upload_image_host(user)
        if self.command == "GET" and path == "/api/drive/folders":
            return self.list_folders(user)
        if self.command == "POST" and path == "/api/drive/folders":
            return self.create_folder(user)
        if self.command == "GET" and path == "/api/drive/files":
            qs = urllib.parse.parse_qs(parsed.query)
            return self.list_files(user, qs.get("folderId", ["root"])[0])
        if self.command == "POST" and path == "/api/upload":
            return self.upload(user)
        if self.command == "POST" and path == "/api/items/reorder":
            return self.reorder_items(user)
        if self.command == "POST" and path == "/api/items/move":
            return self.move_items(user)

        match = re.match(r"^/api/image-host/files/([^/]+)$", path)
        if match and self.command == "DELETE":
            return self.delete_image_host_file(user, urllib.parse.unquote(match.group(1)))

        if self.command == "POST" and path == "/api/image-host/files/batch-delete":
            return self.batch_delete_image_host_files(user)
        if self.command == "POST" and path == "/api/image-host/files/batch-move":
            return self.batch_move_image_host_files(user)

        match = re.match(r"^/api/image-host/folders/([^/]+)$", path)
        if match and self.command == "PATCH":
            return self.rename_image_host_folder(user, urllib.parse.unquote(match.group(1)))
        if match and self.command == "DELETE":
            return self.delete_image_host_folder(user, urllib.parse.unquote(match.group(1)))

        match = re.match(r"^/api/drive/folders/([^/]+)/public$", path)
        if match and self.command == "PATCH":
            return self.set_folder_public(user, urllib.parse.unquote(match.group(1)))

        match = re.match(r"^/api/drive/folders/([^/]+)$", path)
        if match and self.command == "PATCH":
            return self.rename_folder(user, urllib.parse.unquote(match.group(1)))
        if match and self.command == "DELETE":
            return self.delete_folder(user, urllib.parse.unquote(match.group(1)))

        match = re.match(r"^/api/drive/files/([^/]+)/download$", path)
        if match and self.command in ("GET", "HEAD"):
            return self.download(user, urllib.parse.unquote(match.group(1)))
        match = re.match(r"^/api/drive/files/([^/]+)/public$", path)
        if match and self.command == "PATCH":
            return self.set_public(user, urllib.parse.unquote(match.group(1)))
        match = re.match(r"^/api/drive/files/([^/]+)$", path)
        if match and self.command == "PATCH":
            return self.rename_file(user, urllib.parse.unquote(match.group(1)))
        if match and self.command == "DELETE":
            return self.delete_file(user, urllib.parse.unquote(match.group(1)))
        raise HttpError(404, "接口不存在")

    def initialize(self):
        body = self.read_json()
        username = clean_name(body.get("username"), "用户名", 3, 32)
        password = body.get("password") or ""
        if len(password) < 10:
            raise HttpError(400, "管理员密码至少 10 位")
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]:
                raise HttpError(409, "系统已初始化")
            salt = secrets.token_hex(16)
            user_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO users (id, username, password_hash, salt, role, disabled, created_at) VALUES (?, ?, ?, ?, 'admin', 0, ?)",
                (user_id, username, hash_password(password, salt), salt, now()),
            )
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return self.create_session(user)

    def login(self):
        body = self.read_json()
        username = (body.get("username") or "").strip()
        password = body.get("password") or ""
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or user["disabled"] or hash_password(password, user["salt"]) != user["password_hash"]:
            raise HttpError(401, "用户名或密码错误")
        return self.create_session(user)

    def logout(self):
        token = self.cookie()
        if token:
            with db() as conn:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (sha256(token),))
        self.json({"ok": True}, headers={"Set-Cookie": self.cookie_header("", 0)})

    def create_session(self, user):
        token = secrets.token_urlsafe(36)
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now(),))
            conn.execute(
                "INSERT INTO sessions (id, user_id, token_hash, expires_at, created_at) VALUES (?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), user["id"], sha256(token), now() + SESSION_SECONDS, now()),
            )
        self.json(
            {"username": user["username"], "role": user["role"]},
            headers={"Set-Cookie": self.cookie_header(token, SESSION_SECONDS)},
        )

    def require_auth(self):
        token = self.cookie()
        if not token:
            raise HttpError(401, "请先登录")
        with db() as conn:
            row = conn.execute(
                "SELECT users.* FROM sessions JOIN users ON sessions.user_id = users.id WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
                (sha256(token), now()),
            ).fetchone()
        if not row or row["disabled"]:
            raise HttpError(401, "请先登录")
        return row

    def stats(self, user):
        with db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c, COALESCE(SUM(size), 0) AS b FROM files WHERE user_id = ? AND file_category = 'drive'",
                (user["id"],),
            ).fetchone()
        self.json({"totalFiles": row["c"], "totalBytes": row["b"]})

    def list_folders(self, user):
        with db() as conn:
            rows = conn.execute("SELECT * FROM folders WHERE user_id = ? AND folder_category = 'drive' ORDER BY parent_id, sort_order, id", (user["id"],)).fetchall()
        self.json([folder_dto(x, self.origin()) for x in rows])

    def create_folder(self, user):
        body = self.read_json()
        name = clean_name(body.get("name"), "文件夹名称", 1, 80)
        parent_id = body.get("parentId") or "root"
        self.assert_folder(user, parent_id)
        folder_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(24)
        ts = now()
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            sort_order = next_sort_order(conn, "folders", user["id"], "drive", parent_id)
            conn.execute(
                "INSERT INTO folders (id, user_id, parent_id, name, share_token, folder_category, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'drive', ?, ?, ?)",
                (folder_id, user["id"], parent_id, name, token, sort_order, ts, ts),
            )
        with db() as conn:
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def rename_folder(self, user, folder_id):
        name = clean_name(self.read_json().get("name"), "文件夹名称", 1, 80)
        self.assert_folder(user, folder_id)
        with db() as conn:
            conn.execute("UPDATE folders SET name = ?, updated_at = ? WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (name, now(), folder_id, user["id"]))
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def set_folder_public(self, user, folder_id):
        body = self.read_json()
        is_public = 1 if body.get("isPublic") else 0
        self.assert_folder(user, folder_id)
        token = secrets.token_urlsafe(24) if is_public else None
        with db() as conn:
            conn.execute("UPDATE folders SET share_token = ?, updated_at = ? WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (token, now(), folder_id, user["id"]))
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def delete_folder(self, user, folder_id):
        if folder_id == "root":
            raise HttpError(400, "不能删除根目录")
        self.assert_folder(user, folder_id)
        with db() as conn:
            row = conn.execute("SELECT parent_id FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"])).fetchone()
            c1 = conn.execute("SELECT COUNT(*) AS c FROM folders WHERE user_id = ? AND parent_id = ? AND folder_category = 'drive'", (user["id"], folder_id)).fetchone()["c"]
            c2 = conn.execute("SELECT COUNT(*) AS c FROM files WHERE user_id = ? AND folder_id = ? AND file_category = 'drive'", (user["id"], folder_id)).fetchone()["c"]
            if c1 or c2:
                raise HttpError(409, "只能删除空文件夹")
            conn.execute("DELETE FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"]))
            compact_sort_orders(conn, "folders", user["id"], "drive", row["parent_id"])
        self.json({"ok": True})

    def list_files(self, user, folder_id):
        self.assert_folder(user, folder_id)
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM files WHERE user_id = ? AND folder_id = ? AND file_category = 'drive' ORDER BY sort_order, id",
                (user["id"], folder_id),
            ).fetchall()
        self.json([file_dto(x, self.origin()) for x in rows])

    def upload(self, user):
        folder_id, item = self.parse_upload()
        try:
            self.assert_folder(user, folder_id)
            name = clean_name(os.path.basename(item.file_name.decode("utf-8", "replace")), "文件名", 1, MAX_NAME)
        except Exception:
            item.close()
            raise
        file_id = str(uuid.uuid4())
        user_dir = os.path.join(STORAGE_DIR, user["id"])
        os.makedirs(user_dir, exist_ok=True)
        storage_path = os.path.join(user_dir, f"{file_id}-{safe_name(name)}")
        content_type = item.content_type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        try:
            size = copy_upload(item, storage_path)
            token = secrets.token_urlsafe(24)
            ts = now()
            with db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                sort_order = next_sort_order(conn, "files", user["id"], "drive", folder_id)
                conn.execute(
                    "INSERT INTO files (id, user_id, folder_id, name, storage_path, size, content_type, is_public, share_token, file_category, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'drive', ?, ?, ?)",
                    (file_id, user["id"], folder_id, name, storage_path, size, content_type, token, sort_order, ts, ts),
                )
                row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        except Exception:
            remove_file(storage_path)
            raise
        finally:
            item.close()
        self.json(file_dto(row, self.origin()))

    def list_image_host_folders(self, user):
        with db() as conn:
            rows = conn.execute(
                "SELECT f.*, (SELECT COUNT(*) FROM files i WHERE i.user_id = f.user_id AND i.folder_id = f.id AND i.file_category = 'image_host') AS image_count FROM folders f WHERE f.user_id = ? AND f.folder_category = 'image_host' ORDER BY f.parent_id, f.sort_order, f.id",
                (user["id"],),
            ).fetchall()
        self.json([image_folder_dto(x, self.origin()) for x in rows])

    def create_image_host_folder(self, user):
        body = self.read_json()
        name = clean_name(body.get("name"), "文件夹名称", 1, 80)
        parent_id = body.get("parentId") or "root"
        self.assert_image_folder(user, parent_id)
        folder_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(24)
        ts = now()
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            sort_order = next_sort_order(conn, "folders", user["id"], "image_host", parent_id)
            conn.execute(
                "INSERT INTO folders (id, user_id, parent_id, name, share_token, folder_category, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'image_host', ?, ?, ?)",
                (folder_id, user["id"], parent_id, name, token, sort_order, ts, ts),
            )
            row = conn.execute("SELECT f.*, 0 AS image_count FROM folders f WHERE f.id = ? AND f.user_id = ?", (folder_id, user["id"])).fetchone()
        self.json(image_folder_dto(row, self.origin()))

    def rename_image_host_folder(self, user, folder_id):
        name = clean_name(self.read_json().get("name"), "文件夹名称", 1, 80)
        self.assert_image_folder(user, folder_id)
        with db() as conn:
            conn.execute("UPDATE folders SET name = ?, updated_at = ? WHERE id = ? AND user_id = ? AND folder_category = 'image_host'", (name, now(), folder_id, user["id"]))
            row = conn.execute("SELECT f.*, (SELECT COUNT(*) FROM files i WHERE i.user_id = f.user_id AND i.folder_id = f.id AND i.file_category = 'image_host') AS image_count FROM folders f WHERE f.id = ? AND f.user_id = ?", (folder_id, user["id"])).fetchone()
        self.json(image_folder_dto(row, self.origin()))

    def delete_image_host_folder(self, user, folder_id):
        if folder_id == "root":
            raise HttpError(400, "不能删除根目录")
        self.assert_image_folder(user, folder_id)
        with db() as conn:
            row = conn.execute("SELECT parent_id FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'image_host'", (folder_id, user["id"])).fetchone()
            folders = conn.execute("SELECT COUNT(*) AS c FROM folders WHERE user_id = ? AND parent_id = ? AND folder_category = 'image_host'", (user["id"], folder_id)).fetchone()["c"]
            files = conn.execute("SELECT COUNT(*) AS c FROM files WHERE user_id = ? AND folder_id = ? AND file_category = 'image_host'", (user["id"], folder_id)).fetchone()["c"]
            if folders or files:
                raise HttpError(409, "文件夹不为空")
            conn.execute("DELETE FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'image_host'", (folder_id, user["id"]))
            compact_sort_orders(conn, "folders", user["id"], "image_host", row["parent_id"])
        self.json({"ok": True})

    def list_image_host_files(self, user, folder_id):
        self.assert_image_folder(user, folder_id)
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM files WHERE user_id = ? AND folder_id = ? AND file_category = 'image_host' ORDER BY sort_order, id",
                (user["id"], folder_id),
            ).fetchall()
        self.json([file_dto(x, self.origin()) for x in rows])

    def upload_image_host(self, user):
        folder_id, item = self.parse_upload()
        try:
            self.assert_image_folder(user, folder_id)
            name = clean_name(os.path.basename(item.file_name.decode("utf-8", "replace")), "文件名", 1, MAX_NAME)
        except Exception:
            item.close()
            raise
        extension = os.path.splitext(name)[1].lower()
        expected_type = IMAGE_CONTENT_TYPES.get(extension)
        content_type = (item.content_type or "").split(";", 1)[0].strip().lower()
        if not expected_type or content_type not in {expected_type, "image/jpg" if extension in (".jpg", ".jpeg") else expected_type}:
            item.close()
            raise HttpError(400, "不支持该图片格式")
        file_id = str(uuid.uuid4())
        user_dir = os.path.join(STORAGE_DIR, user["id"])
        os.makedirs(user_dir, exist_ok=True)
        storage_path = os.path.join(user_dir, f"{file_id}-{safe_name(name)}")
        try:
            size = copy_upload(item, storage_path)
            if not valid_image_signature(storage_path, extension):
                raise HttpError(400, "不支持该图片格式")
            token = secrets.token_urlsafe(24)
            ts = now()
            with db() as conn:
                conn.execute("BEGIN IMMEDIATE")
                sort_order = next_sort_order(conn, "files", user["id"], "image_host", folder_id)
                conn.execute(
                    "INSERT INTO files (id, user_id, folder_id, name, storage_path, size, content_type, is_public, share_token, file_category, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'image_host', ?, ?, ?)",
                    (file_id, user["id"], folder_id, name, storage_path, size, expected_type, token, sort_order, ts, ts),
                )
                row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"])).fetchone()
        except Exception:
            remove_file(storage_path)
            raise
        finally:
            item.close()
        self.json(file_dto(row, self.origin()))

    def reorder_items(self, user):
        body = self.read_json()
        category = body.get("category") if isinstance(body, dict) else None
        item_type = body.get("itemType") if isinstance(body, dict) else None
        parent_id = body.get("parentId") if isinstance(body, dict) else None
        ids = body.get("ids") if isinstance(body, dict) else None
        if category not in ("drive", "image_host") or item_type not in ("folder", "file"):
            raise HttpError(400, "排序类型无效")
        if not isinstance(parent_id, str) or not parent_id:
            raise HttpError(400, "缺少父目录")
        if not isinstance(ids, list) or any(not isinstance(item, str) or not item for item in ids):
            raise HttpError(400, "ids 必须是字符串数组")
        if len(ids) != len(set(ids)) or len(ids) > 5000:
            raise HttpError(400, "排序项目重复或过多")
        table = "folders" if item_type == "folder" else "files"
        parent_column = "parent_id" if item_type == "folder" else "folder_id"
        category_column = "folder_category" if item_type == "folder" else "file_category"
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.assert_category_folder_conn(conn, user["id"], category, parent_id)
            rows = conn.execute(
                f"SELECT id FROM {table} WHERE user_id = ? AND {category_column} = ? AND {parent_column} = ? ORDER BY sort_order, id",
                (user["id"], category, parent_id),
            ).fetchall()
            current_ids = [row["id"] for row in rows]
            if len(ids) != len(current_ids) or set(ids) != set(current_ids):
                raise HttpError(409, "目录内容已变化，请刷新后重试")
            for position, item_id in enumerate(ids):
                conn.execute(
                    f"UPDATE {table} SET sort_order = ? WHERE id = ? AND user_id = ? AND {category_column} = ? AND {parent_column} = ?",
                    (position, item_id, user["id"], category, parent_id),
                )
        self.json({"ok": True, "ids": ids})

    def move_items(self, user):
        body = self.read_json()
        category = body.get("category") if isinstance(body, dict) else None
        items = body.get("items") if isinstance(body, dict) else None
        target_id = body.get("folderId") if isinstance(body, dict) else None
        conflict_policy = body.get("conflictPolicy", "cancel") if isinstance(body, dict) else None
        result = self._move_items(user, category, items, target_id, conflict_policy)
        self.json(result)

    def _move_items(self, user, category, items, target_id, conflict_policy):
        if category not in ("drive", "image_host"):
            raise HttpError(400, "分类无效")
        if not isinstance(items, list) or not items or len(items) > 1000:
            raise HttpError(400, "请选择要移动的项目")
        if not isinstance(target_id, str) or not target_id:
            raise HttpError(400, "缺少目标文件夹")
        if conflict_policy not in ("rename", "skip", "cancel"):
            raise HttpError(400, "冲突处理方式无效")
        requested = []
        seen = set()
        for item in items:
            if not isinstance(item, dict) or item.get("type") not in ("folder", "file") or not isinstance(item.get("id"), str) or not item.get("id"):
                raise HttpError(400, "移动项目格式无效")
            key = (item["type"], item["id"])
            if key not in seen:
                seen.add(key)
                requested.append(key)

        moved, skipped, failed = [], [], []
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self.assert_category_folder_conn(conn, user["id"], category, target_id)
            loaded = []
            for item_type, item_id in requested:
                table = "folders" if item_type == "folder" else "files"
                category_column = "folder_category" if item_type == "folder" else "file_category"
                row = conn.execute(
                    f"SELECT * FROM {table} WHERE id = ? AND user_id = ? AND {category_column} = ?",
                    (item_id, user["id"], category),
                ).fetchone()
                if not row:
                    failed.append({"type": item_type, "id": item_id, "reason": "not_found"})
                else:
                    loaded.append((item_type, row))

            selected_folder_ids = {row["id"] for item_type, row in loaded if item_type == "folder"}
            normalized = []
            for item_type, row in loaded:
                parent_id = row["parent_id"] if item_type == "folder" else row["folder_id"]
                if self.has_selected_ancestor(conn, user["id"], category, parent_id, selected_folder_ids):
                    skipped.append({"type": item_type, "id": row["id"], "reason": "covered_by_parent"})
                    continue
                if item_type == "folder" and (target_id == row["id"] or self.folder_is_descendant_conn(conn, user["id"], category, target_id, row["id"])):
                    failed.append({"type": item_type, "id": row["id"], "reason": "cycle"})
                    continue
                normalized.append((item_type, row))

            if conflict_policy == "cancel":
                for item_type, row in normalized:
                    source_parent = row["parent_id"] if item_type == "folder" else row["folder_id"]
                    if source_parent != target_id and self.name_exists_conn(conn, user["id"], category, target_id, row["name"], item_type, row["id"]):
                        raise HttpError(409, f"目标目录已存在同名项目：{row['name']}")

            source_groups = set()
            next_orders = {
                "folder": next_sort_order(conn, "folders", user["id"], category, target_id),
                "file": next_sort_order(conn, "files", user["id"], category, target_id),
            }
            ts = now()
            for item_type, row in normalized:
                table = "folders" if item_type == "folder" else "files"
                parent_column = "parent_id" if item_type == "folder" else "folder_id"
                source_parent = row[parent_column]
                if source_parent == target_id:
                    skipped.append({"type": item_type, "id": row["id"], "reason": "same_folder"})
                    continue
                new_name = row["name"]
                if self.name_exists_conn(conn, user["id"], category, target_id, new_name, item_type, row["id"]):
                    if conflict_policy == "skip":
                        skipped.append({"type": item_type, "id": row["id"], "reason": "name_conflict"})
                        continue
                    new_name = self.unique_name_conn(conn, user["id"], category, target_id, new_name, item_type)
                conn.execute(
                    f"UPDATE {table} SET {parent_column} = ?, name = ?, sort_order = ?, updated_at = ? WHERE id = ? AND user_id = ?",
                    (target_id, new_name, next_orders[item_type], ts, row["id"], user["id"]),
                )
                next_orders[item_type] += 1
                source_groups.add((table, source_parent))
                moved.append({"type": item_type, "id": row["id"], "name": new_name, "renamed": new_name != row["name"]})
            for table, source_parent in source_groups:
                compact_sort_orders(conn, table, user["id"], category, source_parent)
        return {"moved": moved, "skipped": skipped, "failed": failed}

    def assert_category_folder_conn(self, conn, user_id, category, folder_id):
        if folder_id == "root":
            return
        row = conn.execute(
            "SELECT id FROM folders WHERE id = ? AND user_id = ? AND folder_category = ?",
            (folder_id, user_id, category),
        ).fetchone()
        if not row:
            raise HttpError(404, "目标文件夹不存在")

    def folder_is_descendant_conn(self, conn, user_id, category, folder_id, root_id):
        if folder_id == "root":
            return False
        current = folder_id
        seen = set()
        while current != "root" and current not in seen:
            if current == root_id:
                return True
            seen.add(current)
            row = conn.execute(
                "SELECT parent_id FROM folders WHERE id = ? AND user_id = ? AND folder_category = ?",
                (current, user_id, category),
            ).fetchone()
            if not row:
                return False
            current = row["parent_id"]
        return False

    def has_selected_ancestor(self, conn, user_id, category, folder_id, selected_ids):
        current = folder_id
        seen = set()
        while current != "root" and current not in seen:
            if current in selected_ids:
                return True
            seen.add(current)
            row = conn.execute(
                "SELECT parent_id FROM folders WHERE id = ? AND user_id = ? AND folder_category = ?",
                (current, user_id, category),
            ).fetchone()
            if not row:
                return False
            current = row["parent_id"]
        return False

    def name_exists_conn(self, conn, user_id, category, parent_id, name, item_type, item_id=None):
        folder = conn.execute(
            "SELECT id FROM folders WHERE user_id = ? AND folder_category = ? AND parent_id = ? AND name = ? COLLATE NOCASE AND id != ? LIMIT 1",
            (user_id, category, parent_id, name, item_id or ""),
        ).fetchone()
        file_row = conn.execute(
            "SELECT id FROM files WHERE user_id = ? AND file_category = ? AND folder_id = ? AND name = ? COLLATE NOCASE AND id != ? LIMIT 1",
            (user_id, category, parent_id, name, item_id or ""),
        ).fetchone()
        return bool(folder or file_row)

    def unique_name_conn(self, conn, user_id, category, parent_id, name, item_type):
        stem, extension = (os.path.splitext(name) if item_type == "file" else (name, ""))
        for suffix in range(1, 10001):
            marker = f" ({suffix})"
            max_length = MAX_NAME if item_type == "file" else 80
            safe_extension = extension[: max(0, max_length - len(marker) - 1)]
            candidate_stem = stem[: max(1, max_length - len(marker) - len(safe_extension))]
            candidate = f"{candidate_stem}{marker}{safe_extension}"
            if not self.name_exists_conn(conn, user_id, category, parent_id, candidate, item_type):
                return candidate
        raise HttpError(409, "无法生成不冲突的名称")

    def delete_image_host_file(self, user, file_id):
        with db() as conn:
            row = conn.execute(
                "SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'image_host'",
                (file_id, user["id"]),
            ).fetchone()
        if not row:
            raise HttpError(404, "图片不存在")
        try:
            os.remove(row["storage_path"])
        except FileNotFoundError:
            pass
        with db() as conn:
            conn.execute(
                "DELETE FROM files WHERE id = ? AND user_id = ? AND file_category = 'image_host'",
                (file_id, user["id"]),
            )
            compact_sort_orders(conn, "files", user["id"], "image_host", row["folder_id"])
        self.json({"ok": True})

    def batch_delete_image_host_files(self, user):
        body = self.read_json()
        ids = body.get("ids") if isinstance(body, dict) else None
        if not isinstance(ids, list):
            raise HttpError(400, "ids 必须是数组")
        deleted, failed = [], []
        for file_id in dict.fromkeys(str(x) for x in ids if x):
            with db() as conn:
                row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'image_host'", (file_id, user["id"])).fetchone()
            if not row:
                failed.append({"id": file_id, "error": "图片不存在"})
                continue
            try:
                try:
                    os.remove(row["storage_path"])
                except FileNotFoundError:
                    pass
                with db() as conn:
                    conn.execute("DELETE FROM files WHERE id = ? AND user_id = ? AND file_category = 'image_host'", (file_id, user["id"]))
                    compact_sort_orders(conn, "files", user["id"], "image_host", row["folder_id"])
                deleted.append(file_id)
            except Exception:
                failed.append({"id": file_id, "error": "删除失败"})
        self.json({"deleted": deleted, "failed": failed})

    def batch_move_image_host_files(self, user):
        body = self.read_json()
        ids = body.get("ids") if isinstance(body, dict) else None
        folder_id = body.get("folderId") if isinstance(body, dict) else None
        if not isinstance(ids, list):
            raise HttpError(400, "ids 必须是数组")
        if not isinstance(folder_id, str) or not folder_id:
            raise HttpError(400, "缺少目标文件夹")
        unique_ids = list(dict.fromkeys(str(x) for x in ids if x))
        if not unique_ids:
            raise HttpError(400, "请选择图片")
        result = self._move_items(
            user,
            "image_host",
            [{"type": "file", "id": file_id} for file_id in unique_ids],
            folder_id,
            "skip",
        )
        self.json({
            "moved": [item["id"] for item in result["moved"]],
            "skipped": [item["id"] for item in result["skipped"]],
            "failed": result["failed"],
        })

    def rename_file(self, user, file_id):
        body = self.read_json()
        self.assert_file(user, file_id)
        updates = []
        params = []
        if "name" in body:
            updates.append("name = ?")
            params.append(clean_name(body.get("name"), "文件名", 1, MAX_NAME))
        if "downloadLimitBytes" in body:
            updates.append("download_limit_bytes = ?")
            params.append(parse_download_limit(body.get("downloadLimitBytes")))
        if not updates:
            raise HttpError(400, "缺少可更新字段")
        updates.append("updated_at = ?")
        params.extend([now(), file_id, user["id"]])
        with db() as conn:
            conn.execute(f"UPDATE files SET {', '.join(updates)} WHERE id = ? AND user_id = ?", params)
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'drive'", (file_id, user["id"])).fetchone()
        self.json(file_dto(row, self.origin()))

    def set_public(self, user, file_id):
        body = self.read_json()
        is_public = 1 if body.get("isPublic") else 0
        self.assert_file(user, file_id)
        token = secrets.token_urlsafe(24) if is_public else None
        with db() as conn:
            conn.execute("UPDATE files SET is_public = ?, share_token = ?, updated_at = ? WHERE id = ? AND user_id = ?", (is_public, token, now(), file_id, user["id"]))
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'drive'", (file_id, user["id"])).fetchone()
        self.json(file_dto(row, self.origin()))

    def delete_file(self, user, file_id):
        row = self.assert_file(user, file_id)
        try:
            os.remove(row["storage_path"])
        except FileNotFoundError:
            pass
        with db() as conn:
            conn.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"]))
            compact_sort_orders(conn, "files", user["id"], "drive", row["folder_id"])
        self.json({"ok": True})

    def download(self, user, file_id):
        row = self.assert_file(user, file_id)
        self.send_file(row)

    def public_file(self, path):
        token = urllib.parse.unquote(path.split("/")[2] if len(path.split("/")) > 2 else "")
        with db() as conn:
            row = conn.execute("SELECT * FROM files WHERE share_token = ? AND is_public = 1", (token,)).fetchone()
        if not row:
            raise HttpError(404, "链接不存在或已失效")
        self.send_file(row, inline=row["file_category"] == "image_host")

    def share_page(self, path):
        if self.command not in ("GET", "HEAD"):
            raise HttpError(405, "方法不允许")
        token = urllib.parse.unquote(path.split("/")[2] if len(path.split("/")) > 2 else "")
        with db() as conn:
            row = conn.execute("SELECT * FROM files WHERE share_token = ? AND is_public = 1", (token,)).fetchone()
        if not row:
            raise HttpError(404, "分享链接不存在或已失效")
        download_url = f"/public/{urllib.parse.quote(row['share_token'])}/{urllib.parse.quote(row['name'])}"
        body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(row['name'])} - {html.escape(SITE_NAME)}</title>
  <style>
    :root{{font-family:Inter,"Noto Sans SC",system-ui,sans-serif;color:#18181b;background:#f7f7f5}}
    body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:#f7f7f5}}
    main{{width:min(560px,100%);background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:28px;box-shadow:0 18px 48px rgba(24,24,27,.08)}}
    h1{{margin:0 0 8px;font-size:24px;word-break:break-word}}
    p{{margin:0 0 22px;color:#71717a}}
    dl{{display:grid;gap:12px;margin:22px 0}}
    div{{display:flex;justify-content:space-between;gap:16px;border-top:1px solid #f4f4f5;padding-top:12px}}
    dt{{color:#71717a}} dd{{margin:0;font-weight:700;text-align:right;word-break:break-word}}
    a{{height:44px;border-radius:8px;background:#2563eb;color:#fff;display:flex;align-items:center;justify-content:center;text-decoration:none;font-weight:800}}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(row['name'])}</h1>
    <p>公开分享文件</p>
    <dl>
      <div><dt>文件大小</dt><dd>{html.escape(format_size(row['size']))}</dd></div>
      <div><dt>文件类型</dt><dd>{html.escape(row['content_type'])}</dd></div>
      <div><dt>更新时间</dt><dd>{html.escape(format_time(row['updated_at']))}</dd></div>
    </dl>
    <a href="{html.escape(download_url)}" download>下载文件</a>
  </main>
</body>
</html>"""
        self.html(body)

    def folder_share_route(self, path, parsed):
        if self.command not in ("GET", "HEAD"):
            raise HttpError(405, "方法不允许")
        parts = path.split("/")
        token = urllib.parse.unquote(parts[3] if len(parts) > 3 else "")
        with db() as conn:
            root = conn.execute("SELECT * FROM folders WHERE share_token = ? AND folder_category = 'drive'", (token,)).fetchone()
            if not root:
                raise HttpError(404, "文件夹分享链接不存在或已失效")
            if len(parts) == 7 and parts[4] == "file" and parts[6] == "download":
                file_id = urllib.parse.unquote(parts[5])
                file_row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'drive'", (file_id, root["user_id"])).fetchone()
                if not file_row or not is_folder_descendant(conn, root["user_id"], file_row["folder_id"], root["id"]):
                    raise HttpError(404, "文件不存在")
                return self.send_file(file_row)
            qs = urllib.parse.parse_qs(parsed.query)
            current_id = qs.get("folderId", [root["id"]])[0]
            if not is_folder_descendant(conn, root["user_id"], current_id, root["id"]):
                raise HttpError(404, "文件夹不存在")
            current = root if current_id == root["id"] else conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (current_id, root["user_id"])).fetchone()
            folders = conn.execute("SELECT * FROM folders WHERE user_id = ? AND parent_id = ? AND folder_category = 'drive' ORDER BY sort_order, id", (root["user_id"], current_id)).fetchall()
            files = conn.execute("SELECT * FROM files WHERE user_id = ? AND folder_id = ? AND file_category = 'drive' ORDER BY sort_order, id", (root["user_id"], current_id)).fetchall()
        title = current["name"] if current else root["name"]
        parent_link = ""
        if current and current["id"] != root["id"]:
            parent_id = current["parent_id"] if is_folder_descendant_db(root["user_id"], current["parent_id"], root["id"]) else root["id"]
            parent_link = f'<a class="back" href="/share/folder/{html.escape(urllib.parse.quote(token))}?folderId={html.escape(urllib.parse.quote(parent_id))}">返回上级目录</a>'
        folder_rows = "".join(
            f'<li><a href="/share/folder/{html.escape(urllib.parse.quote(token))}?folderId={html.escape(urllib.parse.quote(row["id"]))}"><span>📁</span><b>{html.escape(row["name"])}</b><small>文件夹</small></a></li>'
            for row in folders
        )
        file_rows = "".join(
            f'<li><a href="/share/folder/{html.escape(urllib.parse.quote(token))}/file/{html.escape(urllib.parse.quote(row["id"]))}/download" download><span>📄</span><b>{html.escape(row["name"])}</b><small>{html.escape(format_size(row["size"]))} · {html.escape(row["content_type"])}</small></a></li>'
            for row in files
        )
        empty = "<p class=\"empty-share\">这个文件夹是空的</p>" if not folders and not files else ""
        body = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} - {html.escape(SITE_NAME)}</title>
  <style>
    :root{{font-family:Inter,"Noto Sans SC",system-ui,sans-serif;color:#18181b;background:#f7f7f5}}
    body{{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:#f7f7f5}}
    main{{width:min(760px,100%);background:#fff;border:1px solid #e4e4e7;border-radius:10px;padding:28px;box-shadow:0 18px 48px rgba(24,24,27,.08)}}
    h1{{margin:0 0 8px;font-size:24px;word-break:break-word}}
    p{{margin:0 0 18px;color:#71717a}}
    .back{{display:inline-flex;margin:8px 0 16px;color:#2563eb;text-decoration:none;font-weight:800}}
    ul{{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:8px}}
    li a{{display:grid;grid-template-columns:34px minmax(0,1fr);gap:10px;align-items:center;padding:12px;border:1px solid #e4e4e7;border-radius:8px;color:#18181b;text-decoration:none}}
    li span{{grid-row:span 2;width:34px;height:34px;border-radius:8px;background:#eef2ff;display:grid;place-items:center}}
    li b{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
    li small{{color:#71717a}}
    .empty-share{{padding:40px 0;text-align:center}}
  </style>
</head>
<body>
  <main>
    <h1>{html.escape(title)}</h1>
    <p>公开分享文件夹</p>
    {parent_link}
    <ul>{folder_rows}{file_rows}</ul>
    {empty}
  </main>
</body>
</html>"""
        self.html(body)

    def assert_folder(self, user, folder_id):
        if folder_id == "root":
            return
        with db() as conn:
            row = conn.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (folder_id, user["id"])).fetchone()
        if not row:
            raise HttpError(404, "文件夹不存在")

    def assert_image_folder(self, user, folder_id):
        if folder_id == "root":
            return
        with db() as conn:
            row = conn.execute("SELECT id FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'image_host'", (folder_id, user["id"])).fetchone()
        if not row:
            raise HttpError(404, "图床文件夹不存在")

    def assert_file(self, user, file_id):
        with db() as conn:
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ? AND file_category = 'drive'", (file_id, user["id"])).fetchone()
        if not row:
            raise HttpError(404, "文件不存在")
        return row

    def send_file(self, row, inline=False):
        if not os.path.exists(row["storage_path"]):
            raise HttpError(404, "文件不存在")
        size = int(row["size"] or 0)
        byte_range = None
        range_header = self.headers.get("Range")
        if range_header:
            try:
                byte_range = parse_range_header(range_header, size)
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()
                return
        start, end = byte_range if byte_range else (0, size - 1)
        content_length = max(0, end - start + 1)
        assert_download_allowed(row, content_length)
        self.send_response(206 if byte_range else 200)
        self.send_header("Content-Type", row["content_type"])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(content_length))
        if byte_range:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        disposition = "inline" if inline else "attachment; filename*=UTF-8''" + urllib.parse.quote(row["name"])
        self.send_header("Content-Disposition", disposition)
        self.send_header("Cache-Control", "public, max-age=3600" if row["is_public"] else "no-store")
        self.end_headers()
        if self.command == "HEAD":
            return
        sent = 0
        completed = False
        try:
            with open(row["storage_path"], "rb") as src:
                src.seek(start)
                remaining = content_length
                while remaining > 0:
                    chunk = src.read(min(DOWNLOAD_CHUNK_SIZE, remaining))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    sent += len(chunk)
                    remaining -= len(chunk)
                completed = sent == content_length
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            record_download(row["id"], sent, completed and not byte_range)

    def parse_upload(self):
        content_type = self.headers.get("Content-Type", "")
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise HttpError(400, "Content-Length 无效")
        if content_length <= 0:
            raise HttpError(400, "上传请求为空")
        if content_length > MAX_UPLOAD_BYTES:
            raise HttpError(413, "上传文件过大")
        if not content_type.lower().startswith("multipart/form-data;"):
            raise HttpError(415, "上传请求必须使用 multipart/form-data")

        fields = {}
        files = []

        def on_field(field):
            if field.field_name:
                fields[field.field_name.decode("utf-8", "replace")] = (field.value or b"").decode("utf-8", "replace")

        def on_file(item):
            files.append(item)

        headers = {
            "Content-Type": content_type.encode("latin-1"),
            "Content-Length": str(content_length).encode("ascii"),
        }
        try:
            parse_form(headers, self.rfile, on_field, on_file)
        except (FormParserError, MultipartParseError, ValueError):
            for item in files:
                item.close()
            raise HttpError(400, "上传请求格式无效")
        upload_files = [item for item in files if item.field_name == b"file" and item.file_name]
        for item in files:
            if item not in upload_files:
                item.close()
        if len(upload_files) != 1:
            for item in upload_files:
                item.close()
            raise HttpError(400, "必须上传一个文件")
        return fields.get("folderId") or "root", upload_files[0]

    def read_json(self):
        try:
            length = int(self.headers.get("content-length") or "0")
        except ValueError:
            raise HttpError(400, "Content-Length 无效")
        if length <= 0:
            return {}
        if length > MAX_JSON_BYTES:
            raise HttpError(413, "JSON 请求体过大")
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            raise HttpError(400, "请求体必须是 JSON")

    def cookie(self):
        raw = self.headers.get("cookie") or ""
        cookies = http.cookies.SimpleCookie(raw)
        return cookies[COOKIE_NAME].value if COOKIE_NAME in cookies else None

    def cookie_header(self, value, max_age):
        secure = "; Secure" if (self.headers.get("x-forwarded-proto") or "").lower() == "https" else ""
        return f"{COOKIE_NAME}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}{secure}"

    def origin(self):
        proto = self.headers.get("x-forwarded-proto") or "http"
        host = self.headers.get("host") or f"127.0.0.1:{self.server.server_port}"
        return f"{proto}://{host}"

    def html(self, body):
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def send_asset(self, path, content_type):
        try:
            with open(path, "rb") as src:
                data = src.read()
        except FileNotFoundError:
            raise HttpError(404, "资源不存在")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=31536000, immutable")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def json(self, body, status=200, headers=None):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass

    def log_message(self, fmt, *args):
        return


def folder_dto(row, origin=None):
    share_path = f"/share/folder/{urllib.parse.quote(row['share_token'])}" if row["share_token"] else None
    share_url = f"{origin}{share_path}" if origin and share_path else share_path
    return {
        "id": row["id"],
        "parentId": row["parent_id"],
        "name": row["name"],
        "isPublic": bool(row["share_token"]),
        "shareUrl": share_url,
        "sortOrder": row["sort_order"],
        "updatedAt": row["updated_at"],
    }


def image_folder_dto(row, origin=None):
    return {
        "id": row["id"],
        "parentId": row["parent_id"],
        "name": row["name"],
        "folderCategory": row["folder_category"],
        "imageCount": row["image_count"] if "image_count" in row.keys() else 0,
        "sortOrder": row["sort_order"],
        "updatedAt": row["updated_at"],
    }


def file_dto(row, origin=None):
    public_path = f"/public/{urllib.parse.quote(row['share_token'])}" if row["is_public"] and row["share_token"] else None
    share_path = f"/share/{urllib.parse.quote(row['share_token'])}" if row["is_public"] and row["share_token"] else None
    public_url = f"{origin}{public_path}" if origin and public_path else public_path
    share_url = f"{origin}{share_path}" if origin and share_path else share_path
    return {
        "id": row["id"],
        "folderId": row["folder_id"],
        "name": row["name"],
        "size": row["size"],
        "contentType": row["content_type"],
        "fileCategory": row["file_category"],
        "sortOrder": row["sort_order"],
        "downloadCount": row["download_count"],
        "downloadBytes": row["download_bytes"],
        "downloadLimitBytes": row["download_limit_bytes"],
        "isPublic": bool(row["is_public"]),
        "publicUrl": public_url,
        "shareUrl": share_url,
        "downloadUrl": f"/api/drive/files/{urllib.parse.quote(row['id'])}/download",
        "updatedAt": row["updated_at"],
    }


def is_folder_descendant(conn, user_id, folder_id, root_id):
    if folder_id == root_id:
        return True
    current = folder_id
    seen = set()
    while current and current != "root" and current not in seen:
        seen.add(current)
        row = conn.execute("SELECT id, parent_id FROM folders WHERE id = ? AND user_id = ? AND folder_category = 'drive'", (current, user_id)).fetchone()
        if not row:
            return False
        if row["parent_id"] == root_id:
            return True
        current = row["parent_id"]
    return False


def is_folder_descendant_db(user_id, folder_id, root_id):
    with db() as conn:
        return is_folder_descendant(conn, user_id, folder_id, root_id)


def parse_range_header(header, size):
    if size <= 0:
        raise ValueError("empty file has no satisfiable byte range")
    if not header.startswith("bytes="):
        raise ValueError("unsupported range unit")
    spec = header[6:].strip()
    if "," in spec or "-" not in spec:
        raise ValueError("unsupported range")
    start_text, end_text = spec.split("-", 1)
    if not start_text:
        if not end_text or not end_text.isdigit():
            raise ValueError("invalid suffix range")
        suffix = int(end_text)
        if suffix <= 0:
            raise ValueError("invalid suffix range")
        start = max(size - suffix, 0)
        end = size - 1
    else:
        if not start_text.isdigit() or (end_text and not end_text.isdigit()):
            raise ValueError("invalid range")
        start = int(start_text)
        end = int(end_text) if end_text else size - 1
        if start >= size or start > end:
            raise ValueError("unsatisfiable range")
        end = min(end, size - 1)
    return start, end


def record_download(file_id, sent_bytes, completed):
    sent_bytes = max(0, int(sent_bytes or 0))
    if sent_bytes <= 0 and not completed:
        return
    with db() as conn:
        conn.execute(
            "UPDATE files SET download_count = COALESCE(download_count, 0) + ?, download_bytes = COALESCE(download_bytes, 0) + ? WHERE id = ?",
            (1 if completed else 0, sent_bytes, file_id),
        )


def assert_download_allowed(row, expected_bytes=None):
    limit = row["download_limit_bytes"]
    if limit is None:
        return
    used = int(row["download_bytes"] or 0)
    limit = int(limit)
    if used >= limit:
        raise HttpError(403, "该文件下载流量已达到限制")
    if expected_bytes is not None and used + int(expected_bytes or 0) > limit:
        raise HttpError(403, "该文件下载流量已达到限制")


def parse_download_limit(value):
    if value is None:
        return None
    if isinstance(value, bool):
        raise HttpError(400, "流量限制必须是非负整数")
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        if not re.fullmatch(r"\d+", value):
            raise HttpError(400, "流量限制必须是非负整数")
        value = int(value)
    if not isinstance(value, int) or value < 0:
        raise HttpError(400, "流量限制必须是非负整数")
    return value


def clean_name(value, label, min_len, max_len):
    name = (value or "").strip()
    if len(name) < min_len:
        raise HttpError(400, f"{label}太短")
    if len(name) > max_len:
        raise HttpError(400, f"{label}不能超过 {max_len} 个字符")
    if "/" in name or "\\" in name or "\0" in name:
        raise HttpError(400, f"{label}不能包含路径分隔符")
    return name


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9._()-]+", "_", name)[:120] or "file"


def valid_image_signature(path, extension):
    with open(path, "rb") as src:
        header = src.read(16)
    if extension in (".jpg", ".jpeg"):
        return header.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return header.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == ".gif":
        return header.startswith((b"GIF87a", b"GIF89a"))
    if extension == ".webp":
        return len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    return False


def copy_upload(item, destination):
    item.file_object.seek(0)
    written = 0
    with open(destination, "xb") as out:
        while True:
            chunk = item.file_object.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            out.write(chunk)
    return written


def remove_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def format_size(size):
    size = int(size or 0)
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)
    unit = units[0]
    for unit in units:
        if value < 1024 or unit == units[-1]:
            break
        value /= 1024
    return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"


def format_time(timestamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(timestamp or 0)))


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 210000).hex()


def sha256(value):
    return hashlib.sha256(value.encode()).hexdigest()


def now():
    return int(time.time())


if __name__ == "__main__":
    init_db()
    host = os.environ.get("R2_DRIVE_HOST", "127.0.0.1")
    port = int(os.environ.get("R2_DRIVE_PORT", "8090"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
