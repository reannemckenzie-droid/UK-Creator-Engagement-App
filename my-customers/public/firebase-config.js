import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getFirestore } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
import { getStorage } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-storage.js";

// Your web app's Firebase configuration
// Replace the placeholder values with your actual Firebase project configuration
const firebaseConfig = {
  apiKey: "AIzaSyDaHUuzWOI_uMDxPPdAJff1uSZBeFvwLvI",
  authDomain: "my-customers-498915.firebaseapp.com",
  projectId: "my-customers-498915",
  storageBucket: "my-customers-498915.firebasestorage.app",
  messagingSenderId: "984271348831",
  appId: "1:984271348831:web:608dbc7ad7a849d8a567ea"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getFirestore(app);
const storage = getStorage(app);

export { db, storage };
