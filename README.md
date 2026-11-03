# Bunwich على Firebase

نفس سيستم Bunwich اللي على Claude، بس شغال على **Firebase** (تسجيل الدخول + قاعدة البيانات + الاستضافة)، والكود على **GitHub**، وكل ما تعمل push على `main` بيتنشر لوحده. وتقدر تثبّته **كـ App** على الموبايل أو الكمبيوتر.

---

## الملفات

| الملف | لازمته |
|---|---|
| `public/index.html` | السيستم نفسه (اتعمل من `src/bunwich-artifact.html` بـ `tools/build.py`) |
| `public/firebase-config.js` | **الملف الوحيد اللي بتملاه**: بيانات مشروع Firebase وإيميل owner |
| `public/firebase-shim.js` | بيوصّل السيستم بـ Firebase (الدخول، البيانات، التحميل، زرار تثبيت التطبيق) |
| `public/manifest.webmanifest` و `public/sw.js` و `public/icons/` | علشان يتثبت كـ App ويفتح بسرعة |
| `firestore.rules` | قواعد الأمان: مين يقرا ويكتب إيه |
| `firebase.json` و `.firebaserc` | إعدادات النشر |
| `.github/workflows/deploy.yml` | النشر التلقائي من GitHub |

---

## خطوات التشغيل (أول مرة بس)

### 1) جهّز مشروع Firebase
في [Firebase Console](https://console.firebase.google.com) على مشروعك:
1. **Authentication** ← Get started ← Sign-in method ← فعّل **Email/Password**.
2. **Firestore Database** ← Create database ← اختار **Production mode** ← المكان: `eur3` أو أقرب منطقة ليك.
3. ⚙️ **Project settings** ← Your apps ← لو مفيش Web app دوس `</>` واعمل واحد (من غير Hosting setup).
   - انسخ القيم (`apiKey`, `authDomain`, `projectId`, …).

### 2) الإعدادات (اتملت خلاص)
مشروع `bunwich-d6f7c`، وإيميل owner `ramz.ghaly@gmail.com`، متكتبين في `public/firebase-config.js` و`firestore.rules` و`.firebaserc`. لو عايز تغيّر إيميل owner، غيّره في أول ملفين.

### 3) ارفع على GitHub
ارفع كل الملفات دي على الـ repo بتاعك (على فرع `main`)، بما فيهم الفولدر المخفي `.github`.

### 4) اربط GitHub بـ Firebase (علشان النشر التلقائي)
1. Firebase Console ← ⚙️ Project settings ← **Service accounts** ← **Generate new private key** ← هينزل ملف JSON.
2. GitHub ← الـ repo ← **Settings** ← **Secrets and variables** ← **Actions** ← **New repository secret**:
   - Name: `FIREBASE_SERVICE_ACCOUNT`
   - Secret: الصق محتوى ملف الـ JSON كله.
3. امسح ملف الـ JSON من جهازك بعد كده (ده مفتاح سري).
4. GitHub ← **Actions** ← **Deploy to Firebase** ← **Run workflow** (أو اعمل أي push).

بعد دقيقتين السيستم هيبقى على: `https://<PROJECT_ID>.web.app`

> لو حابب تنشر من الكمبيوتر بدل GitHub:
> `npm i -g firebase-tools` ← `firebase login` ← `firebase deploy --only hosting,firestore`

### 5) أول دخول
1. افتح اللينك. هيطلبلك تختار **باسورد owner** (8 حروف على الأقل)، وده بيعمل حساب owner على إيميلك.
   - **اعمل الخطوة دي أول ما تنشر**، قبل ما تبعت اللينك لحد.
2. **انقل البيانات من سيستم Claude:**
   - في Bunwich على Claude: الصلاحيات ← النسخ الاحتياطية ← **تحميل نسخة مشفرة (JSON)**.
   - في النسخة الجديدة: الصلاحيات ← **استرجاع من نسخة** ← اختار الملف ← اكتب **باسورد owner بتاع سيستم Claude** ← استرجاع.
3. **ضيف المستخدمين:** الصلاحيات ← اسم المستخدم + **باسورد أول مرة** + الدور ← إضافة.
   - المستخدم بيدخل بالاسم والباسورد ده، ويغيّره من زرار **«تغيير الباسورد»** فوق.

### 6) التثبيت كـ App
- **أندرويد / كروم / إيدج:** هيظهر زرار **«📲 تثبيت التطبيق»**، أو من قايمة المتصفح ← Install app.
- **آيفون (Safari):** زرار المشاركة ⬆️ ← **Add to Home Screen**.

---

## الفرق عن نسخة Claude

| الحاجة | نسخة Firebase |
|---|---|
| الدخول | اسم مستخدم + باسورد (Firebase Authentication). owner بيدخل بـ `owner` وعنده «نسيت الباسورد» على إيميله. |
| نسي مستخدم الباسورد | اقفله من الصلاحيات وضيفه باسم جديد، أو امسحه من Firebase ← Authentication وضيفه تاني بنفس الاسم. |
| قفل مستخدم | «قفل» بيمنعه يدخل فوراً، وقواعد Firestore بتمنعه يقرا أو يكتب أي حاجة. |
| النسخة الأسبوعية على Google Drive | **مش متاحة هنا** (كانت شغالة من خلال Claude). استخدم «تحميل نسخة مشفرة» كل أسبوع واحفظها على Drive. |
| صور الإيصالات | محتاجة Cloud Storage، وده محتاج باقة **Blaze**. لو فعّلتها: خلي `USE_STORAGE: true` وانشر `storage.rules`. صور الإيصالات القديمة اللي على Claude مش بتتنقل. |
| الشغل من غير نت | البيانات بتتحفظ على الجهاز وبتتزامن أول ما النت يرجع. |
| سجل التعديلات | كل مستخدم بيكتب في السجل بتاعه بس، ومحدش يقدر يعدّل أو يمسح سطر في السجل. |

## تحديث السيستم بعد كده
لما يتعمل تعديل على Bunwich في Claude:
```
python3 tools/build.py src/bunwich-artifact.html public/index.html
```
وبعدين push، والنشر بيتعمل لوحده. لو عايز التحديث يوصل للموبايلات المثبّت عليها التطبيق فوراً، غيّر `VERSION` في `public/sw.js`.

## التكلفة
الباقة المجانية (Spark) بتكفي كافيه أو مطعم: 50 ألف قراءة و20 ألف كتابة في اليوم، و1 جيجا تخزين. كل فتحة للسيستم بتقرا كل الحركات مرة واحدة (حوالي 1,500 قراءة دلوقتي)، ومع الوقت الرقم ده بيزيد.
