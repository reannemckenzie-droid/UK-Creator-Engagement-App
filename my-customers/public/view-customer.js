import { db, storage } from "./firebase-config.js";
import { 
    doc, 
    getDoc, 
    updateDoc, 
    deleteDoc 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";
import { 
    ref, 
    uploadBytes, 
    getDownloadURL 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-storage.js";

const form = document.getElementById("customer-form");
const loadingEl = document.getElementById("loading");
const feedbackEl = document.getElementById("feedback");
const photoPreview = document.getElementById("photo-preview");
const photoInput = document.getElementById("photo-input");

// Get customer ID from URL
const urlParams = new URLSearchParams(window.location.search);
const customerId = urlParams.get("id");

if (!customerId) {
    window.location.href = "index.html";
}

// Show feedback message
function showFeedback(message) {
    feedbackEl.textContent = message;
    feedbackEl.classList.remove("hidden");
    setTimeout(() => {
        feedbackEl.classList.add("hidden");
    }, 3000);
}

// Load customer data
async function loadCustomer() {
    try {
        const docRef = doc(db, "customers", customerId);
        const docSnap = await getDoc(docRef);

        if (docSnap.exists()) {
            const customer = docSnap.data();
            
            // Populate form
            form.name.value = customer.name || "";
            form.status.value = customer.status || "Planning";
            form.balance.value = customer.balance || 0;
            form.notes.value = customer.notes || "";
            
            if (customer.photoURL) {
                photoPreview.src = customer.photoURL;
            }

            // Show form, hide loading
            loadingEl.classList.add("hidden");
            form.classList.remove("hidden");
        } else {
            showFeedback("Customer not found.");
            setTimeout(() => window.location.href = "index.html", 2000);
        }
    } catch (error) {
        console.error("Error loading customer:", error);
        showFeedback("Error loading customer data.");
    }
}

// Handle Form Submission
form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const saveBtn = document.getElementById("save-btn");
    saveBtn.disabled = true;
    saveBtn.textContent = "Saving...";

    try {
        let photoURL = photoPreview.src;

        // Upload new photo if selected
        if (photoInput.files[0]) {
            const file = photoInput.files[0];
            const storageRef = ref(storage, `customer-photos/${customerId}/${file.name}`);
            const snapshot = await uploadBytes(storageRef, file);
            photoURL = await getDownloadURL(snapshot.ref);
        }

        // Update Firestore
        const customerRef = doc(db, "customers", customerId);
        await updateDoc(customerRef, {
            name: form.name.value,
            status: form.status.value,
            balance: parseFloat(form.balance.value),
            notes: form.notes.value,
            photoURL: photoURL
        });

        showFeedback("Customer saved successfully!");
    } catch (error) {
        console.error("Error updating customer:", error);
        showFeedback("Error saving customer.");
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Customer";
    }
});

// Handle Photo Preview
photoInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            photoPreview.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }
});

// Handle Deletion
document.getElementById("delete-btn").addEventListener("click", async () => {
    if (confirm("Are you sure you want to delete this customer?")) {
        try {
            await deleteDoc(doc(db, "customers", customerId));
            showFeedback("Customer deleted.");
            setTimeout(() => window.location.href = "index.html", 1500);
        } catch (error) {
            console.error("Error deleting customer:", error);
            showFeedback("Error deleting customer.");
        }
    }
});

// Initialize
loadCustomer();
