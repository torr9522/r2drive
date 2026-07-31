#!/usr/bin/env python3
import cgi
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


BASE_DIR = os.environ.get("R2_DRIVE_DATA", "/opt/r2-drive/data")
DB_PATH = os.path.join(BASE_DIR, "drive.sqlite3")
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
SITE_NAME = os.environ.get("R2_DRIVE_SITE_NAME", "R2 Drive")
COOKIE_NAME = "r2_drive_session"
SESSION_SECONDS = 30 * 86400
MAX_NAME = 180
DOWNLOAD_CHUNK_SIZE = 16 * 1024


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>R2 Drive</title>
  <style>
    :root{--accent:#2563eb;--success:#059669;--danger:#dc2626;--bg:#f7f7f5;--surface:#fff;--soft:#f4f4f5;--text:#18181b;--muted:#71717a;--faint:#a1a1aa;--border:#e4e4e7;font-family:Inter,"Noto Sans SC",system-ui,sans-serif;color:var(--text);background:var(--bg)}*{box-sizing:border-box}body{margin:0;background:var(--bg)}button,input{font:inherit}button{cursor:pointer}.splash,.auth{min-height:100vh;display:grid;place-items:center;padding:20px}.card{width:min(420px,100%);padding:28px;border:1px solid var(--border);border-radius:10px;background:#fff;box-shadow:0 18px 48px #18181b14}.brand{display:flex;align-items:center;gap:12px;margin-bottom:26px}.mark{width:42px;height:42px;border-radius:8px;background:var(--accent);color:#fff;display:grid;place-items:center;font-weight:900}.brand span{display:grid;gap:2px}.brand small,.muted{color:var(--muted)}h1{margin:0 0 8px;font-size:27px}.card p{margin:0 0 22px;color:var(--muted);line-height:1.65}label{display:grid;gap:8px;margin:15px 0;font-size:13px;font-weight:750}input{height:44px;border:1px solid var(--border);border-radius:8px;padding:0 12px;outline:none}input:focus{border-color:#93b4f5;box-shadow:0 0 0 3px #2563eb1a}.primary,.secondary,.icon{height:40px;border-radius:8px;border:0;display:inline-flex;align-items:center;justify-content:center;gap:7px;font-weight:780}.primary{background:var(--accent);color:#fff;padding:0 14px}.secondary{background:#fff;border:1px solid var(--border);color:var(--text);padding:0 14px}.icon{width:38px;background:#fff;border:1px solid var(--border);color:var(--muted)}.full{width:100%;height:48px;margin-top:12px}.alert{display:flex;align-items:center;gap:8px;min-height:40px;border:1px solid #fee2e2;background:#fef2f2;color:var(--danger);border-radius:8px;padding:9px 12px;margin-bottom:14px;font-size:13px;font-weight:700}.shell{height:100vh;display:grid;grid-template-columns:220px minmax(0,1fr);overflow:hidden}aside{background:#fff;border-right:1px solid var(--border);padding:22px 14px 16px;display:flex;flex-direction:column}.nav{height:42px;border:0;border-radius:8px;background:#eff6ff;color:var(--accent);display:flex;align-items:center;gap:10px;padding:0 12px;font-weight:760}.logout{margin-top:auto;background:transparent;color:var(--muted);justify-content:flex-start}.work{min-width:0;overflow:auto;padding:26px 30px 52px}.work header{display:flex;align-items:center;justify-content:space-between;gap:18px;margin-bottom:22px}.work h1{margin:4px 0 0}.toolbar{display:flex;align-items:center;gap:10px;margin-bottom:16px}.crumbs{min-width:0;margin-right:auto;display:flex;gap:7px;align-items:center;overflow:auto;color:var(--faint)}.crumbs button{border:0;background:transparent;color:var(--muted);font-weight:760;padding:7px 3px;white-space:nowrap}.crumbs button:last-child{color:var(--text)}.search{width:220px;height:40px}.picker{position:relative;overflow:hidden}.picker input{position:absolute;inset:0;opacity:0}.drop{min-height:88px;border:1.5px dashed #b6c8f6;background:#ffffffb8;border-radius:8px;display:flex;align-items:center;gap:14px;padding:18px;color:var(--muted);margin-bottom:18px}.drop.drag{border-color:var(--accent);background:#eff6ff}.uploads{display:grid;gap:9px;margin-bottom:16px}.task{background:#fff;border:1px solid var(--border);border-radius:8px;padding:12px}.task div:first-child{display:flex;justify-content:space-between;gap:14px;font-size:12px}.bar{height:7px;background:#e5e7eb;border-radius:99px;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;background:var(--accent)}.list-scroll{overflow-x:auto}.list{min-width:1040px;background:#fff;border:1px solid var(--border);border-radius:8px;overflow:hidden}.head,.row{display:grid;grid-template-columns:minmax(220px,1.8fr) 74px 92px 92px 92px 82px 150px 150px;align-items:center;gap:9px;padding:0 16px}.head{height:42px;background:var(--soft);color:var(--muted);font-size:11px;font-weight:800}.row{min-height:62px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)}.name{min-width:0;border:0;background:transparent;color:var(--text);display:flex;align-items:center;gap:12px;text-align:left;padding:8px 0}.ico{width:36px;height:36px;border-radius:8px;background:#eef2ff;color:var(--accent);display:grid;place-items:center;flex:none}.name span:last-child{min-width:0;display:grid;gap:3px}.name b{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.name small{color:var(--faint);font-size:10px}.privacy{width:72px;height:28px;border-radius:99px;border:0;font-size:11px;font-weight:800}.privacy.private{background:#f4f4f5;color:#52525b}.privacy.public{background:#ecfdf5;color:var(--success)}.limit-btn{height:28px;border:1px solid var(--border);border-radius:7px;background:#fff;color:var(--muted);font-size:11px;font-weight:800;padding:0 8px;max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.limit-btn:hover{border-color:#93b4f5;color:var(--accent);background:#eff6ff}.modal-backdrop{position:fixed;inset:0;background:#18181b66;display:grid;place-items:center;padding:20px;z-index:20}.modal{width:min(440px,100%);background:#fff;border:1px solid var(--border);border-radius:10px;box-shadow:0 20px 60px #18181b33;padding:24px}.modal h2{margin:0 0 8px;font-size:20px}.modal p{margin:0 0 18px;color:var(--muted);word-break:break-word}.limit-field{display:grid;grid-template-columns:minmax(0,1fr) 54px;align-items:center;border:1px solid var(--border);border-radius:8px;overflow:hidden}.limit-field input{border:0;border-radius:0}.limit-field span{height:44px;display:grid;place-items:center;background:var(--soft);color:var(--muted);font-size:12px;font-weight:800}.modal-actions{display:flex;justify-content:flex-end;gap:10px;margin-top:20px}.actions{display:flex;justify-content:flex-end;gap:4px}.actions button{width:30px;height:30px;border:0;border-radius:7px;background:transparent;color:var(--muted)}.actions button:hover{background:#eff6ff;color:var(--accent)}.actions button:last-child:hover{background:#fef2f2;color:var(--danger)}.empty{min-height:220px;display:grid;place-items:center;color:var(--muted);font-size:13px;font-weight:700;border-top:1px solid var(--border)}.toast{position:fixed;right:24px;bottom:24px;min-height:42px;display:flex;align-items:center;background:#18181b;color:#fff;border-radius:8px;padding:0 16px;font-size:12px;font-weight:780}@media(max-width:920px){.shell{display:block;height:auto}.shell aside{display:none}.work{height:auto;min-height:100vh;padding:20px 16px 40px}.toolbar{align-items:stretch;flex-wrap:wrap}.crumbs{width:100%}.search{flex:1;min-width:160px}.head{display:none}.list-scroll{overflow:visible}.list{min-width:0;background:transparent;border:0;display:grid;gap:9px;overflow:visible}.row{grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"name actions" "meta privacy";min-height:74px;background:#fff;border:1px solid var(--border);border-radius:8px;padding:10px 12px}.row .name{grid-area:name}.row .size-cell{grid-area:meta;padding-left:48px}.row .count-cell,.row .traffic-cell,.row .limit-cell,.row .updated-cell{display:none}.row .privacy-cell{grid-area:privacy}.actions{grid-area:actions;gap:3px}.actions button{display:none}.actions button:first-child,.actions button:last-child,.actions.file-actions button:nth-child(2),.actions.file-actions button:nth-child(3){display:block}.actions.file-actions button{width:28px}.modal{padding:22px}}@media(max-width:560px){.card{padding:22px}.work h1{font-size:23px}.secondary,.picker{flex:1}.modal-actions .secondary,.modal-actions .primary{flex:1}}
  </style>
</head>
<body><div id="app" class="splash">正在载入...</div>
<script>
const S={view:"loading",siteName:"R2 Drive",username:"",role:"",folders:[],files:[],folder:"root",search:"",error:"",toast:"",stats:{totalFiles:0,totalBytes:0},uploads:[],limitModal:null};
const $=id=>document.getElementById(id), app=$("app");
init();
async function init(){try{const st=await api("/api/status");S.siteName=st.siteName;document.title=S.siteName;if(!st.initialized){S.view="init";return render()}try{const me=await api("/api/me");S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch{S.view="login";render()}}catch(e){S.error=e.message;S.view="login";render()}}
async function refresh(){const [folders,files,stats]=await Promise.all([api("/api/drive/folders"),api(`/api/drive/files?folderId=${enc(S.folder)}`),api("/api/stats")]);S.folders=folders;S.files=files;S.stats=stats;render()}
function render(){if(S.view==="init") return auth(true); if(S.view==="login") return auth(false); if(S.view==="drive") return drive(); app.innerHTML="正在载入..."}
function auth(init){app.className="auth";app.innerHTML=`<form class="card" id="${init?"initForm":"loginForm"}"><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>私人网盘</small></span></div><h1>${init?"创建系统管理员":"登录网盘"}</h1><p>${init?"首次部署需要创建管理员账户。":"使用管理员账户进入私人空间。"}</p>${S.error?`<div class="alert">${esc(S.error)}</div>`:""}<label><span>用户名</span><input name="username" autocomplete="username" minlength="3" maxlength="32" required></label><label><span>密码</span><input name="password" type="password" autocomplete="${init?"new-password":"current-password"}" minlength="${init?10:1}" required></label><button class="primary full">${init?"完成初始化":"确认登录"}</button></form>`;$(init?"initForm":"loginForm").onsubmit=init?submitInit:submitLogin}
function drive(){app.className="";const folders=S.folders.filter(x=>x.parentId===S.folder&&x.name.toLowerCase().includes(S.search.toLowerCase())).sort((a,b)=>a.name.localeCompare(b.name,"zh-CN"));const files=S.files.filter(x=>x.name.toLowerCase().includes(S.search.toLowerCase()));app.innerHTML=`<main class="shell"><aside><div class="brand"><b class="mark">D</b><span><b>${esc(S.siteName)}</b><small>${esc(S.username)}</small></span></div><button class="nav">我的网盘</button><button class="secondary logout" onclick="logout()">退出登录</button></aside><section class="work"><header><div><p class="muted">共 ${S.stats.totalFiles} 个文件 · ${fmtSize(S.stats.totalBytes)}</p><h1>我的网盘</h1></div><button class="icon" onclick="refresh()" title="刷新">↻</button></header>${S.error?`<div class="alert">${esc(S.error)}<button onclick="S.error='';render()">×</button></div>`:""}<section class="toolbar"><div class="crumbs">${crumbs()}</div><input class="search" id="search" placeholder="搜索当前文件夹" value="${esc(S.search)}"><button class="secondary" onclick="newFolder()">新建文件夹</button><label class="primary picker">上传文件<input id="fileInput" type="file" multiple></label></section>${S.uploads.length?`<section class="uploads">${S.uploads.map(taskHtml).join("")}</section>`:""}<section id="drop" class="drop"><b>⇧</b><span><b>拖放文件到这里上传</b><small>上传到当前文件夹</small></span></section><div class="list-scroll"><section class="list"><div class="head"><span>名称</span><span>下载次数</span><span>下载流量</span><span>流量限制</span><span>大小</span><span>访问</span><span>更新时间</span><span></span></div>${S.folder!=="root"?parentRow():""}${folders.map(folderRow).join("")}${files.map(fileRow).join("")}${!folders.length&&!files.length?`<div class="empty">这个文件夹是空的</div>`:""}</section></div></section>${limitModal()}${S.toast?`<div class="toast">${esc(S.toast)}</div>`:""}</main>`;$("search").oninput=e=>{S.search=e.target.value;render()};$("fileInput").onchange=e=>uploadFiles(e.target.files);if(S.limitModal)$("limitForm").onsubmit=saveDownloadLimit;const d=$("drop");d.ondragover=e=>{e.preventDefault();d.classList.add("drag")};d.ondragleave=()=>d.classList.remove("drag");d.ondrop=e=>{e.preventDefault();d.classList.remove("drag");uploadFiles(e.dataTransfer.files)}}
async function submitInit(e){e.preventDefault();try{const me=await api("/api/initialize",{method:"POST",body:JSON.stringify(fd(e))});S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch(err){S.error=err.message;render()}}
async function submitLogin(e){e.preventDefault();try{const me=await api("/api/login",{method:"POST",body:JSON.stringify(fd(e))});S.username=me.username;S.role=me.role;S.view="drive";await refresh()}catch(err){S.error=err.message;render()}}
async function logout(){await api("/api/logout",{method:"POST"});S.view="login";S.folder="root";S.files=[];S.folders=[];render()}
async function newFolder(){const name=prompt("请输入文件夹名称");if(!name)return;try{await api("/api/drive/folders",{method:"POST",body:JSON.stringify({name,parentId:S.folder})});toast("文件夹已创建");await refresh()}catch(e){S.error=e.message;render()}}
async function renameFolder(id){const f=S.folders.find(x=>x.id===id);const name=prompt("新的文件夹名称",f?.name||"");if(!name||name===f?.name)return;try{await api(`/api/drive/folders/${enc(id)}`,{method:"PATCH",body:JSON.stringify({name})});toast("文件夹已重命名");await refresh()}catch(e){S.error=e.message;render()}}
async function deleteFolder(id){const f=S.folders.find(x=>x.id===id);if(!confirm(`删除空文件夹「${f?.name||""}」？`))return;try{await api(`/api/drive/folders/${enc(id)}`,{method:"DELETE"});toast("文件夹已删除");await refresh()}catch(e){S.error=e.message;render()}}
async function renameFile(id){const f=S.files.find(x=>x.id===id);const name=prompt("新的文件名",f?.name||"");if(!name||name===f?.name)return;try{await api(`/api/drive/files/${enc(id)}`,{method:"PATCH",body:JSON.stringify({name})});toast("文件已重命名");await refresh()}catch(e){S.error=e.message;render()}}
function setDownloadLimit(id){const f=S.files.find(x=>x.id===id);if(!f)return;S.limitModal={id,value:f.downloadLimitBytes==null?"":trimNumber(f.downloadLimitBytes/1024/1024/1024)};render()}
function closeDownloadLimit(){S.limitModal=null;render()}
async function saveDownloadLimit(e){e.preventDefault();const id=S.limitModal?.id;if(!id)return;const text=String($("limitInput").value||"").trim();let limit=null;if(text!==""){const gb=Number(text);if(!Number.isFinite(gb)||gb<0){S.error="流量限制必须是非负数字";return render()}limit=Math.floor(gb*1024*1024*1024)}try{const row=await api(`/api/drive/files/${enc(id)}`,{method:"PATCH",body:JSON.stringify({downloadLimitBytes:limit})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=row;S.limitModal=null;toast(limit==null?"流量限制已取消":"流量限制已设置");render()}catch(e){S.error=e.message;render()}}
async function deleteFile(id){const f=S.files.find(x=>x.id===id);if(!confirm(`永久删除「${f?.name||""}」？此操作无法恢复。`))return;try{await api(`/api/drive/files/${enc(id)}`,{method:"DELETE"});toast("文件已删除");await refresh()}catch(e){S.error=e.message;render()}}
async function togglePublic(id){const f=S.files.find(x=>x.id===id);try{await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:!f.isPublic})});toast(!f.isPublic?"公开链接已生成":"文件已设为私密");await refresh()}catch(e){S.error=e.message;render()}}
function downloadFile(id){const f=S.files.find(x=>x.id===id);if(!f)return;const a=document.createElement("a");a.href=f.downloadUrl;a.download=f.name;a.style.display="none";document.body.appendChild(a);a.click();a.remove()}
async function shareFile(id){let f=S.files.find(x=>x.id===id);if(!f)return;try{if(!f.isPublic){f=await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=f}const url=new URL(f.publicUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("直链已复制");render()}catch(e){S.error=e.message;render()}}
async function shareFilePage(id){let f=S.files.find(x=>x.id===id);if(!f)return;try{if(!f.isPublic){f=await api(`/api/drive/files/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.files.findIndex(x=>x.id===id);if(i>=0)S.files[i]=f}const url=new URL(f.shareUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("分享页链接已复制");render()}catch(e){S.error=e.message;render()}}
async function shareFolder(id){let f=S.folders.find(x=>x.id===id);if(!f)return;try{f=await api(`/api/drive/folders/${enc(id)}/public`,{method:"PATCH",body:JSON.stringify({isPublic:true})});const i=S.folders.findIndex(x=>x.id===id);if(i>=0)S.folders[i]=f;const url=new URL(f.shareUrl,location.origin).href;await navigator.clipboard.writeText(url);toast("文件夹分享链接已复制");render()}catch(e){S.error=e.message;render()}}
async function copyLink(id){const f=S.files.find(x=>x.id===id);const url=new URL(f.publicUrl||f.downloadUrl,location.origin).href;await navigator.clipboard.writeText(url);toast(f.publicUrl?"公开直链已复制":"私密下载地址已复制")}
function uploadFiles(files){[...files].forEach(uploadFile)}
async function uploadFile(file){const t={id:crypto.randomUUID(),name:file.name,progress:0,status:"uploading",message:""};S.uploads.unshift(t);render();try{const data=new FormData();data.append("folderId",S.folder);data.append("file",file);const xhr=new XMLHttpRequest();await new Promise((res,rej)=>{xhr.upload.onprogress=e=>{if(e.lengthComputable){t.progress=Math.min(99,Math.round(e.loaded/e.total*100));render()}};xhr.onload=()=>xhr.status>=200&&xhr.status<300?res():rej(new Error(parseErr(xhr.responseText)));xhr.onerror=()=>rej(new Error("网络错误"));xhr.open("POST","/api/upload");xhr.send(data)});t.progress=100;t.status="done";toast("上传完成");await refresh()}catch(e){t.status="failed";t.message=e.message;S.error=e.message;render()}}
async function api(path,opt={}){const h=new Headers(opt.headers||{});if(opt.body&&typeof opt.body==="string")h.set("content-type","application/json");const r=await fetch(path,{...opt,headers:h});const tx=await r.text();const d=tx?JSON.parse(tx):null;if(!r.ok)throw new Error(d?.error||`请求失败 (${r.status})`);return d}
function crumbs(){const arr=[{id:"root",name:"我的网盘"}];let c=S.folder, chain=[];while(c!=="root"){const f=S.folders.find(x=>x.id===c);if(!f)break;chain.unshift(f);c=f.parentId}arr.push(...chain);return arr.map(x=>`<button onclick="S.folder='${esc(x.id)}';S.search='';refresh()">${esc(x.name)}</button>`).join("<span>/</span>")}
function parentOf(id){return S.folders.find(x=>x.id===id)?.parentId||"root"}
function parentRow(){return `<article class="row"><button class="name" onclick="S.folder='${esc(parentOf(S.folder))}';S.search='';refresh()"><span class="ico">📁</span><span><b>返回上级目录</b><small>Parent folder</small></span></button><span class="count-cell"></span><span class="traffic-cell"></span><span class="limit-cell"></span><span class="size-cell">-</span><span class="privacy-cell">-</span><span class="updated-cell">-</span><span class="actions"></span></article>`}
function folderRow(f){return `<article class="row"><button class="name" onclick="S.folder='${esc(f.id)}';S.search='';refresh()"><span class="ico">📁</span><span><b>${esc(f.name)}</b><small>文件夹</small></span></button><span class="count-cell"></span><span class="traffic-cell"></span><span class="limit-cell"></span><span class="size-cell">-</span><span class="privacy-cell">${f.shareUrl?"已分享":"私密"}</span><span class="updated-cell">${f.updatedAt?fmtDate(f.updatedAt):"-"}</span><span class="actions"><button onclick="shareFolder('${esc(f.id)}')" title="分享">🔗</button><button onclick="renameFolder('${esc(f.id)}')" title="重命名">✎</button><button onclick="deleteFolder('${esc(f.id)}')" title="删除">🗑</button></span></article>`}
function fileRow(f){return `<article class="row"><button class="name" onclick="downloadFile('${esc(f.id)}')"><span class="ico">📄</span><span><b>${esc(f.name)}</b><small>${esc(f.contentType)}</small></span></button><span class="count-cell">${f.downloadCount||0}</span><span class="traffic-cell">${fmtSize(f.downloadBytes||0)}</span><span class="limit-cell"><button class="limit-btn" onclick="setDownloadLimit('${esc(f.id)}')" title="设置流量限制">${fmtLimit(f.downloadLimitBytes)}</button></span><span class="size-cell">${fmtSize(f.size)}</span><span class="privacy-cell"><button class="privacy ${f.isPublic?"public":"private"}" onclick="togglePublic('${esc(f.id)}')">${f.isPublic?"公开":"私密"}</button></span><span class="updated-cell">${fmtDate(f.updatedAt)}</span><span class="actions file-actions"><button onclick="downloadFile('${esc(f.id)}')" title="下载">↓</button><button onclick="shareFile('${esc(f.id)}')" title="分享直链">🔗</button><button onclick="shareFilePage('${esc(f.id)}')" title="分享页">📄</button><button onclick="renameFile('${esc(f.id)}')" title="重命名">✎</button><button onclick="deleteFile('${esc(f.id)}')" title="删除">🗑</button></span></article>`}
function limitModal(){if(!S.limitModal)return"";const f=S.files.find(x=>x.id===S.limitModal.id);return `<div class="modal-backdrop" onclick="if(event.target===this)closeDownloadLimit()"><form class="modal" id="limitForm"><h2>设置下载流量限制</h2><p>${esc(f?.name||"")}</p><label><span>最大下载流量</span><span class="limit-field"><input id="limitInput" type="number" min="0" step="0.01" value="${esc(S.limitModal.value)}" autofocus><span>GB</span></span></label><div class="modal-actions"><button type="button" class="secondary" onclick="closeDownloadLimit()">取消</button><button class="primary">确定</button></div></form></div>`}
function taskHtml(t){return `<article class="task"><div><b>${esc(t.name)}</b><span>${t.status==="failed"?esc(t.message):t.progress+"%"}</span></div><div class="bar"><i style="width:${t.progress}%"></i></div></article>`}
function fd(e){const d=new FormData(e.target);return {username:String(d.get("username")||""),password:String(d.get("password")||"")}}
function fmtSize(n){if(!n)return"0 B";const u=["B","KB","MB","GB","TB"];const i=Math.min(Math.floor(Math.log(n)/Math.log(1024)),u.length-1);return`${(n/1024**i).toFixed(i?1:0)} ${u[i]}`}
function fmtLimit(n){if(n==null)return"不限";const gb=1024**3, mb=1024**2;return n>=gb?`${trimNumber(n/gb)} GB`:`${trimNumber(n/mb)} MB`}
function trimNumber(n){return Number(n.toFixed(2)).toString()}
function fmtDate(v){return new Date(v*1000).toLocaleString("zh-CN",{hour12:false})}
function toast(m){S.toast=m;render();setTimeout(()=>{if(S.toast===m){S.toast="";render()}},2200)}
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
              created_at INTEGER NOT NULL,
              updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_files_user_folder ON files(user_id, folder_id);
            CREATE INDEX IF NOT EXISTS idx_files_share ON files(share_token);
            """
        )
        ensure_column(conn, "folders", "share_token", "TEXT")
        ensure_column(conn, "files", "download_count", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "files", "download_bytes", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "files", "download_limit_bytes", "INTEGER DEFAULT NULL")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_folders_share ON folders(share_token) WHERE share_token IS NOT NULL")


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column(conn, table, column, definition):
    columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
        if self.command == "GET" and path == "/api/drive/folders":
            return self.list_folders(user)
        if self.command == "POST" and path == "/api/drive/folders":
            return self.create_folder(user)
        if self.command == "GET" and path == "/api/drive/files":
            qs = urllib.parse.parse_qs(parsed.query)
            return self.list_files(user, qs.get("folderId", ["root"])[0])
        if self.command == "POST" and path == "/api/upload":
            return self.upload(user)

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
                "SELECT COUNT(*) AS c, COALESCE(SUM(size), 0) AS b FROM files WHERE user_id = ?",
                (user["id"],),
            ).fetchone()
        self.json({"totalFiles": row["c"], "totalBytes": row["b"]})

    def list_folders(self, user):
        with db() as conn:
            rows = conn.execute("SELECT * FROM folders WHERE user_id = ? ORDER BY name COLLATE NOCASE", (user["id"],)).fetchall()
        self.json([folder_dto(x, self.origin()) for x in rows])

    def create_folder(self, user):
        body = self.read_json()
        name = clean_name(body.get("name"), "文件夹名称", 1, 80)
        parent_id = body.get("parentId") or "root"
        self.assert_folder(user, parent_id)
        folder_id = str(uuid.uuid4())
        ts = now()
        with db() as conn:
            conn.execute(
                "INSERT INTO folders (id, user_id, parent_id, name, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (folder_id, user["id"], parent_id, name, ts, ts),
            )
        with db() as conn:
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ?", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def rename_folder(self, user, folder_id):
        name = clean_name(self.read_json().get("name"), "文件夹名称", 1, 80)
        self.assert_folder(user, folder_id)
        with db() as conn:
            conn.execute("UPDATE folders SET name = ?, updated_at = ? WHERE id = ? AND user_id = ?", (name, now(), folder_id, user["id"]))
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ?", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def set_folder_public(self, user, folder_id):
        body = self.read_json()
        is_public = 1 if body.get("isPublic") else 0
        self.assert_folder(user, folder_id)
        token = secrets.token_urlsafe(24) if is_public else None
        with db() as conn:
            conn.execute("UPDATE folders SET share_token = ?, updated_at = ? WHERE id = ? AND user_id = ?", (token, now(), folder_id, user["id"]))
            row = conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ?", (folder_id, user["id"])).fetchone()
        self.json(folder_dto(row, self.origin()))

    def delete_folder(self, user, folder_id):
        if folder_id == "root":
            raise HttpError(400, "不能删除根目录")
        self.assert_folder(user, folder_id)
        with db() as conn:
            c1 = conn.execute("SELECT COUNT(*) AS c FROM folders WHERE user_id = ? AND parent_id = ?", (user["id"], folder_id)).fetchone()["c"]
            c2 = conn.execute("SELECT COUNT(*) AS c FROM files WHERE user_id = ? AND folder_id = ?", (user["id"], folder_id)).fetchone()["c"]
            if c1 or c2:
                raise HttpError(409, "只能删除空文件夹")
            conn.execute("DELETE FROM folders WHERE id = ? AND user_id = ?", (folder_id, user["id"]))
        self.json({"ok": True})

    def list_files(self, user, folder_id):
        self.assert_folder(user, folder_id)
        with db() as conn:
            rows = conn.execute(
                "SELECT * FROM files WHERE user_id = ? AND folder_id = ? ORDER BY updated_at DESC",
                (user["id"], folder_id),
            ).fetchall()
        self.json([file_dto(x, self.origin()) for x in rows])

    def upload(self, user):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers, environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("content-type", "")})
        folder_id = form.getfirst("folderId") or "root"
        self.assert_folder(user, folder_id)
        item = form["file"] if "file" in form else None
        if item is None or not getattr(item, "filename", ""):
            raise HttpError(400, "缺少文件")
        name = clean_name(os.path.basename(item.filename), "文件名", 1, MAX_NAME)
        file_id = str(uuid.uuid4())
        user_dir = os.path.join(STORAGE_DIR, user["id"])
        os.makedirs(user_dir, exist_ok=True)
        storage_path = os.path.join(user_dir, f"{file_id}-{safe_name(name)}")
        size = 0
        with open(storage_path, "wb") as out:
            while True:
                chunk = item.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                out.write(chunk)
        content_type = item.type or mimetypes.guess_type(name)[0] or "application/octet-stream"
        ts = now()
        with db() as conn:
            conn.execute(
                "INSERT INTO files (id, user_id, folder_id, name, storage_path, size, content_type, is_public, share_token, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, ?)",
                (file_id, user["id"], folder_id, name, storage_path, size, content_type, ts, ts),
            )
            row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        self.json(file_dto(row, self.origin()))

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
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"])).fetchone()
        self.json(file_dto(row, self.origin()))

    def set_public(self, user, file_id):
        body = self.read_json()
        is_public = 1 if body.get("isPublic") else 0
        self.assert_file(user, file_id)
        token = secrets.token_urlsafe(24) if is_public else None
        with db() as conn:
            conn.execute("UPDATE files SET is_public = ?, share_token = ?, updated_at = ? WHERE id = ? AND user_id = ?", (is_public, token, now(), file_id, user["id"]))
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"])).fetchone()
        self.json(file_dto(row, self.origin()))

    def delete_file(self, user, file_id):
        row = self.assert_file(user, file_id)
        try:
            os.remove(row["storage_path"])
        except FileNotFoundError:
            pass
        with db() as conn:
            conn.execute("DELETE FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"]))
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
        self.send_file(row)

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
            root = conn.execute("SELECT * FROM folders WHERE share_token = ?", (token,)).fetchone()
            if not root:
                raise HttpError(404, "文件夹分享链接不存在或已失效")
            if len(parts) == 7 and parts[4] == "file" and parts[6] == "download":
                file_id = urllib.parse.unquote(parts[5])
                file_row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, root["user_id"])).fetchone()
                if not file_row or not is_folder_descendant(conn, root["user_id"], file_row["folder_id"], root["id"]):
                    raise HttpError(404, "文件不存在")
                return self.send_file(file_row)
            qs = urllib.parse.parse_qs(parsed.query)
            current_id = qs.get("folderId", [root["id"]])[0]
            if not is_folder_descendant(conn, root["user_id"], current_id, root["id"]):
                raise HttpError(404, "文件夹不存在")
            current = root if current_id == root["id"] else conn.execute("SELECT * FROM folders WHERE id = ? AND user_id = ?", (current_id, root["user_id"])).fetchone()
            folders = conn.execute("SELECT * FROM folders WHERE user_id = ? AND parent_id = ? ORDER BY name COLLATE NOCASE", (root["user_id"], current_id)).fetchall()
            files = conn.execute("SELECT * FROM files WHERE user_id = ? AND folder_id = ? ORDER BY updated_at DESC", (root["user_id"], current_id)).fetchall()
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
            row = conn.execute("SELECT id FROM folders WHERE id = ? AND user_id = ?", (folder_id, user["id"])).fetchone()
        if not row:
            raise HttpError(404, "文件夹不存在")

    def assert_file(self, user, file_id):
        with db() as conn:
            row = conn.execute("SELECT * FROM files WHERE id = ? AND user_id = ?", (file_id, user["id"])).fetchone()
        if not row:
            raise HttpError(404, "文件不存在")
        return row

    def send_file(self, row):
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
        assert_download_allowed(row, None if byte_range else content_length)
        self.send_response(206 if byte_range else 200)
        self.send_header("Content-Type", row["content_type"])
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(content_length))
        if byte_range:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Disposition", "attachment; filename*=UTF-8''" + urllib.parse.quote(row["name"]))
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

    def read_json(self):
        length = int(self.headers.get("content-length") or "0")
        if length <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            raise HttpError(400, "请求体必须是 JSON")

    def cookie(self):
        raw = self.headers.get("cookie") or ""
        cookies = http.cookies.SimpleCookie(raw)
        return cookies[COOKIE_NAME].value if COOKIE_NAME in cookies else None

    def cookie_header(self, value, max_age):
        return f"{COOKIE_NAME}={value}; Path=/; HttpOnly; SameSite=Lax; Max-Age={max_age}"

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
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        return


def folder_dto(row, origin=None):
    share_path = f"/share/folder/{urllib.parse.quote(row['share_token'])}" if row["share_token"] else None
    share_url = f"{origin}{share_path}" if origin and share_path else share_path
    return {
        "id": row["id"],
        "parentId": row["parent_id"],
        "name": row["name"],
        "shareUrl": share_url,
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
        row = conn.execute("SELECT id, parent_id FROM folders WHERE id = ? AND user_id = ?", (current, user_id)).fetchone()
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
