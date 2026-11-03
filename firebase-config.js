// ==========================================================
//  Bunwich — إعدادات Firebase  (ده الملف الوحيد اللي بتعدّله)
// ==========================================================
// 1) من Firebase Console ← Project settings ← Your apps ← Web app
//    انسخ القيم وحطها مكان الكلام اللي بين علامات التنصيص.
// 2) OWNER_EMAIL: الإيميل اللي هيدخل بيه owner (يستخدم في «نسيت الباسورد»).
//    لازم يكون هو نفس الإيميل المكتوب في firestore.rules.
// 3) USE_STORAGE: خليها false لو مشروعك على الباقة المجانية (Spark).
//    خليها true بس لو فعّلت Cloud Storage (محتاج باقة Blaze) علشان صور الإيصالات.
window.BUNWICH_FIREBASE = {
  config: {
    apiKey: "AIzaSyAJTd1uZYQeUA4BZbLJj6MspZIuVjeelvE",
    authDomain: "bunwich-d6f7c.firebaseapp.com",
    projectId: "bunwich-d6f7c",
    storageBucket: "bunwich-d6f7c.firebasestorage.app",
    messagingSenderId: "719266835732",
    appId: "1:719266835732:web:fb340b37b826dda2606601"
  },
  OWNER_EMAIL: "ramz.ghaly@gmail.com",
  STAFF_DOMAIN: "bunwich.app",   // المستخدمين بيتعملوا كـ  ahmed@bunwich.app  (مش إيميل حقيقي)
  USE_STORAGE: false
};
