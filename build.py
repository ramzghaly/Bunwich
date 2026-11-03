#!/usr/bin/env python3
"""Build the Firebase version of Bunwich from the claude.ai artifact page.

Usage:  python3 tools/build.py <artifact-index.html> public/index.html

The artifact page is body-only HTML that talks to window.claude.use(...).
This script wraps it in a full document (PWA meta, Firebase SDK, config,
shim) and applies the small patches the Firebase login needs.
Every patch must match exactly once, so a changed source fails loudly
instead of producing a half-patched app.
"""
import sys, re

SDK = "10.14.1"
src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()


def R(old, new, count=1):
    global s
    n = s.count(old)
    if n != count:
        sys.exit(f"patch failed ({n} matches, expected {count}): {old[:90]!r}")
    s = s.replace(old, new)


# ---- 0. receipt images -> Firebase Storage URL
R("""'/_blob/'+id""", """blobSrc(id)""")
R("""'/_blob/'+x.imageId""", """blobSrc(x.imageId)""")

# ---- 1. login: Firebase replaces claude.ai identity --------------------------------
R("""  async function resolveRole(){
    const m=$('lockMsg');""", """  async function resolveRole(){
    if(window.FB)return fbBoot();
    const m=$('lockMsg');""")

R("""  $('lockForm').addEventListener('submit',async e=>{
    e.preventDefault();""", """  $('lockForm').addEventListener('submit',async e=>{
    e.preventDefault();if(window.FB)return fbLogin();""")

FB_LOGIN = r"""
  // ---------- Firebase login (Firebase build only) ----------
  let fbSetup=false;
  const FBMSG={bad_login:'اسم المستخدم أو الباسورد غلط',inactive:'المستخدم ده مقفول. كلم OWNER.',not_member:'الحساب ده مقفول أو مش متسجل في السيستم. كلم OWNER.',network:'مفيش إنترنت. اتأكد من الاتصال وجرب تاني.',too_many:'محاولات كتير غلط. استنى شوية وجرب تاني.',owner_taken:'السيستم ده متعمله إعداد من حساب تاني.',rules:'قواعد Firestore مش متركبة صح (firestore.rules).',no_owner_email:'لسه OWNER_EMAIL مش مكتوب في firebase-config.js',weak:'الباسورد ضعيف، خليه 8 حروف أو أكتر',exists:'الإيميل ده عليه حساب بباسورد تاني. استخدم «نسيت الباسورد».',disabled:'الحساب ده متوقف من Firebase.'};
  function fbSetupStage(){lgStage='new';lgName='owner';$('lgUser').value='owner';$('lgNewBox').hidden=false;$('lgPwLbl').textContent='باسورد owner الجديد';$('lgGo').textContent='إعداد السيستم والدخول';const m=$('lockMsg');m.className='msg';m.textContent='أول مرة: اختار باسورد owner (8 حروف على الأقل). هيتعمل حساب على '+FB.ownerEmail}
  async function fbBoot(){
    const m=$('lockMsg');
    if(!FB.configured){m.className='msg err';m.textContent='لسه ملف firebase-config.js ما اتملاش ببيانات مشروع Firebase.';return}
    platOwner=true;fbSetup=await FB.needsSetup();
    showLogin('');if(fbSetup)fbSetupStage();
    if(!$('fbForgot')){const a=document.createElement('button');a.type='button';a.id='fbForgot';a.className='mini';a.textContent='نسيت باسورد owner';a.style.alignSelf='center';
      a.onclick=async()=>{const mm=$('lockMsg');try{await FB.ownerReset();mm.className='msg ok';mm.textContent='اتبعت لينك تغيير الباسورد على '+FB.ownerEmail}catch(e){mm.className='msg err';mm.textContent='ما قدرتش أبعت الإيميل، جرب تاني'}};
      $('loginBox').appendChild(a)}
  }
  async function fbLogin(){
    const m=$('lockMsg');m.className='msg err';
    if(Date.now()<lgWait){m.textContent='محاولات كتير غلط. استنى شوية وجرب تاني.';return}
    const name=$('lgUser').value.trim().toLowerCase(),pw=$('lgPw').value;
    if(!name||!pw){m.textContent='اكتب اسم المستخدم والباسورد';return}
    $('lgGo').disabled=true;
    try{
      let r;
      if(lgStage==='new'&&fbSetup){
        if(name!=='owner'){m.textContent='أول إعداد بيكون لـ owner';return}
        if(pw.length<8){m.textContent='الباسورد لازم 8 حروف أو أرقام على الأقل';return}
        if(pw!==$('lgPw2').value){m.textContent='التأكيد مش زي الباسورد';return}
        r=await FB.setupOwner(pw);
      }else r=await FB.signIn(name,pw);
      if(!r.ok){m.textContent=FBMSG[r.code]||'حصلت مشكلة، جرب تاني';if(r.code==='bad_login'){lgFail++;if(lgFail>=5){lgWait=Date.now()+60000;lgFail=0}}$('lgPw').value='';$('lgPw').focus();return}
      lgFail=0;m.className='msg';m.textContent='جاري تحميل البيانات…';
      const u=await window.claude.use('user');userApi=u;
      const [own,edit,id]=await Promise.all([u.isOwner(),u.canEdit(),u.id()]);
      myId=id;isAdminLvl=own||edit;canWrite=true;platOwner=own;
      await Promise.race([settingsP,new Promise(x=>setTimeout(x,15000))]);
      let rec=findUser(name);
      if(r.role==='OWNER')rec={u:'OWNER',role:'OWNER',active:true,resetAt:0};
      else rec=Object.assign({u:name,active:true},rec||{},{role:r.role});
      if(!rec.active){await FB.signOut();location.reload();return}
      appUser=rec;$('lgPw').value='';$('lgPw2').value='';
      logAudit('edit','settings','login',null,{login:rec.u},fbSetup?'إعداد أول مرة':'دخول');
      if(rec.u==='OWNER'){try{await prepBackupKey(pw)}catch(e){}}
      lgStage='pw';enter(rec.role);
      const pb=$('pwBtn');if(pb)pb.hidden=false;
    }catch(e){m.className='msg err';m.textContent='حصلت مشكلة، جرب تاني'}
    finally{$('lgGo').disabled=false}
  }
  const blobSrc=id=>window.FB?FB.blob(id):'/_blob/'+id;
  // change own password
  (function(){
    const box=document.createElement('div');box.className='modal';box.id='pwBox';box.hidden=true;box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.dir='rtl';box.lang='ar';
    box.innerHTML='<form class="card" style="background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:18px;width:100%;max-width:380px;display:flex;flex-direction:column;gap:10px" novalidate><h2 style="margin:0;font-size:18px">تغيير الباسورد</h2><label class="sub" for="pwOld" style="margin:0">الباسورد الحالي</label><input id="pwOld" type="password" dir="ltr" autocomplete="current-password"><label class="sub" for="pwNew" style="margin:0">الباسورد الجديد (8 على الأقل)</label><input id="pwNew" type="password" dir="ltr" autocomplete="new-password"><label class="sub" for="pwNew2" style="margin:0">تأكيد الباسورد الجديد</label><input id="pwNew2" type="password" dir="ltr" autocomplete="new-password"><div style="display:flex;gap:8px"><button class="save" type="submit">حفظ</button><button class="mini" type="button" id="pwCancel">إلغاء</button></div><span class="msg" id="pwMsg" role="status"></span></form>';
    document.body.appendChild(box);
    const close=()=>{box.hidden=true;['pwOld','pwNew','pwNew2'].forEach(i=>$(i).value='');$('pwMsg').textContent=''};
    $('pwCancel').onclick=close;box.addEventListener('click',e=>{if(e.target===box)close()});
    box.querySelector('form').onsubmit=async e=>{e.preventDefault();const mm=$('pwMsg');mm.className='msg err';const o=$('pwOld').value,n=$('pwNew').value;
      if(n.length<8){mm.textContent='الباسورد الجديد لازم 8 حروف على الأقل';return}if(n!==$('pwNew2').value){mm.textContent='التأكيد مش زي الباسورد';return}
      try{await FB.changePassword(o,n);if(appUser&&appUser.u==='OWNER'){try{await prepBackupKey(n)}catch(_){}}logAudit('edit','settings','password:'+(appUser&&appUser.u),null,{passwordChanged:true},'تغيير الباسورد');mm.className='msg ok';mm.textContent='اتغير الباسورد';setTimeout(close,1200)}
      catch(er){mm.textContent=er.code==='bad_old'?'الباسورد الحالي غلط':'ما اتغيرش، جرب تاني'}};
    const pb=$('pwBtn');if(pb)pb.onclick=()=>{box.hidden=false;$('pwOld').focus()};
  })();
"""
R("""  let lgName='';""", """  let lgName='';""" + FB_LOGIN)

# sign out / idle lock -> Firebase sign-out + reload
R("""  function lockScreen(){if(!currentUser)return;""",
  """  function lockScreen(){if(!currentUser)return;if(window.FB){currentUser=null;$('app').hidden=true;setTimeout(()=>FB.signOut().then(()=>location.reload()),600);return}""")
R("""<button type="button" class="mini" id="lockBtn">Sign out</button>""",
  """<button type="button" class="mini" id="pwBtn" hidden>تغيير الباسورد</button><button type="button" class="mini" id="lockBtn">Sign out</button>""")

# ---- 2. users: Firebase accounts -------------------------------------------------------
R("""<div class="field"><label for="nuRole">الدور</label>""",
  """<div class="field"><label for="nuPw">باسورد أول مرة</label><input id="nuPw" type="text" dir="ltr" autocapitalize="none" spellcheck="false" autocomplete="off" placeholder="8 حروف على الأقل"></div>
        <div class="field"><label for="nuRole">الدور</label>""")
R("""    const rec={u,role:$('nuRole').value,active:true,createdAt:Date.now(),resetAt:Date.now()};""",
  """    let fbUid=null;if(window.FB){const p0=$('nuPw').value;if(p0.length<8){m.textContent='باسورد أول مرة لازم 8 حروف على الأقل';return}$('nuAdd').disabled=true;try{fbUid=await FB.createStaff(u,p0)}catch(er){$('nuAdd').disabled=false;m.textContent=er.code==='exists'?'الاسم ده عليه حساب في Firebase قبل كده، اختار اسم تاني':er.code==='weak'?'الباسورد ضعيف':'ما قدرتش أعمل الحساب ('+(er.code||'')+')';return}}
    const rec={u,role:$('nuRole').value,active:true,createdAt:Date.now(),resetAt:Date.now()};if(fbUid)rec.uid=fbUid;""")
R("""m.textContent='اتضاف '+u+'. أول ما يدخل هيختار الباسورد بتاعه.';""",
  """m.textContent=window.FB?'اتضاف '+u+'. يدخل باسم '+u+' والباسورد اللي كتبته، ويقدر يغيّره من «تغيير الباسورد».':'اتضاف '+u+'. أول ما يدخل هيختار الباسورد بتاعه.';if(window.FB)$('nuPw').value='';""")
R("""    if(cols.settings)await cols.settings.doc('users').set(doc);
    else{const ex=state.settings.find(d=>d.id==='users');if(ex)Object.assign(ex,doc);else state.settings.push(Object.assign({id:'users'},doc));saveLocal()}""",
  """    if(cols.settings)await cols.settings.doc('users').set(doc);
    else{const ex=state.settings.find(d=>d.id==='users');if(ex)Object.assign(ex,doc);else state.settings.push(Object.assign({id:'users'},doc));saveLocal()}
    if(window.FB){try{await FB.syncMembers(list)}catch(e){toast('اتحفظ بس ما اتحدثتش صلاحيات الدخول، جرب تاني',true)}}""")
R("""const r=mk('Reset الباسورد','edit');r.onclick=async()=>{""",
  """const r=mk('Reset الباسورد','edit');r.onclick=async()=>{if(window.FB){try{await FB.ownerReset();msg('اتبعت لينك تغيير الباسورد على '+FB.ownerEmail)}catch(e){toast('ما قدرتش أبعت الإيميل',true)}return}""")
R("""rp.onclick=async()=>{""",
  """rp.onclick=async()=>{if(window.FB){$('usrMsg').className='msg';$('usrMsg').textContent='في نسخة Firebase: المستخدم يغيّر الباسورد بنفسه من «تغيير الباسورد». لو نسيه: اقفله هنا وضيفه باسم جديد، أو امسحه من Firebase Console ← Authentication وضيفه تاني بنفس الاسم.';return}""")
R("""td(activated?'متفعل '+tsTxt(a.at):'لسه ما دخلش (هيختار باسورد أول مرة)')""",
  """td(window.FB?(x.uid?'حساب Firebase جاهز':'مش مربوط بحساب — ضيفه تاني'):(activated?'متفعل '+tsTxt(a.at):'لسه ما دخلش (هيختار باسورد أول مرة)'))""")
R("""كل مستخدم بيدخل باسم مستخدم وباسورد. أول مرة يدخل بيختار الباسورد بنفسه. المستخدم كمان لازم يكون عامله Share على السيستم من حساب claude.ai بتاعه (Contributor)، أو يدخل من جهاز عليه حساب متشارك.""",
  """كل مستخدم بيدخل باسم مستخدم وباسورد. وانت بتضيفه بتكتب له باسورد أول مرة، وهو يغيّره بعد كده من «تغيير الباسورد». «قفل» بيمنعه يدخل خالص.""")

# ---- 3. receipt images & Drive ------------------------------------------------------------
R("""say('الربط مع Google Drive مش متاح في العرض ده. افتح الصفحة من حسابك على Claude.',true)""",
  """say(window.FB?'الرفع على Google Drive مش متاح في نسخة Firebase. استخدم «تحميل نسخة مشفرة» كل أسبوع واحفظها على Drive بنفسك.':'الربط مع Google Drive مش متاح في العرض ده. افتح الصفحة من حسابك على Claude.',true)""")
R("""<span class="msg" id="lockMsg" role="status" style="text-align:center">جاري التحقق من حسابك…</span>""",
  """<span class="msg" id="lockMsg" role="status" style="text-align:center">جاري التحميل…</span>""")

# ---- 4. full document -------------------------------------------------------------------
title = re.search(r"<title>(.*?)</title>", s).group(1)
head = f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#6B3F24">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="{title}">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icons/icon-192.png">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<style>:root{{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}}img{{max-width:100%}}[hidden]:not([hidden=until-found i]){{display:none!important}}</style>
<script src="https://www.gstatic.com/firebasejs/{SDK}/firebase-app-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/{SDK}/firebase-auth-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/{SDK}/firebase-firestore-compat.js"></script>
<script src="https://www.gstatic.com/firebasejs/{SDK}/firebase-storage-compat.js"></script>
<script src="/firebase-config.js"></script>
<script src="/firebase-shim.js"></script>
</head>
<body>
"""
out = head + s + "\n</body>\n</html>\n"
open(dst, "w", encoding="utf-8").write(out)
print("built", dst, len(out), "bytes")
