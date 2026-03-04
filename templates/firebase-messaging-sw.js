importScripts('https://www.gstatic.com/firebasejs/10.12.3/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.3/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyCd9VsPWHai-_xZrpuMUs98VYFGyogBfNA",
  authDomain: "luckyshop-69.firebaseapp.com",
  projectId: "luckyshop-69",
  storageBucket: "luckyshop-69.firebasestorage.app",
  messagingSenderId: "855170830346",
  appId: "1:855170830346:web:690f001606d65dd9974ff3",
  measurementId: "G-D3GJKFLTVT"
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);

  const notificationTitle = payload.notification?.title || "LuckyShop";
  const notificationOptions = {
    body: payload.notification?.body || "",
    icon: 'https://api.dicebear.com/9.x/initials/svg?seed=shop',
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});