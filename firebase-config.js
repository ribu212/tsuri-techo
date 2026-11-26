// ログイン機能（Firebase）の設定
// Firebase コンソールの「プロジェクトの設定 → マイアプリ」に出てくる firebaseConfig の中身です。
// null にすると、ログイン機能なし（記録はそのスマホの中だけに保存）で動きます。
// ※ この値は公開されても問題ない「接続先の情報」です。データは Firebase 側のルール（firestore.rules）で本人しか読めないよう守っています。
export default {
  apiKey: "AIzaSyAlhlyr7PsYxqWixaGwYcVVUzqquT5wZmY",
  authDomain: "tsuri-techo-4bf69.firebaseapp.com",
  projectId: "tsuri-techo-4bf69",
  storageBucket: "tsuri-techo-4bf69.firebasestorage.app",
  messagingSenderId: "359039040055",
  appId: "1:359039040055:web:4b67565492aca531479db2",
};
