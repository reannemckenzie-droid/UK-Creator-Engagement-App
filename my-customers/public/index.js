import { db } from "./firebase-config.js";
import { 
    collection, 
    onSnapshot, 
    doc, 
    updateDoc, 
    addDoc, 
    query, 
    where 
} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-firestore.js";

const columns = ["Planning", "In-progress", "Review"];
const feedbackEl = document.getElementById("feedback");

// Show feedback message
function showFeedback(message) {
    feedbackEl.textContent = message;
    feedbackEl.classList.remove("hidden");
    setTimeout(() => {
        feedbackEl.classList.add("hidden");
    }, 3000);
}

// Fetch and render customers
function loadCustomers() {
    const customersRef = collection(db, "customers");
    // Exclude "Complete" status
    const q = query(customersRef, where("status", "in", columns));

    onSnapshot(q, (snapshot) => {
        // Clear existing cards
        columns.forEach(col => {
            document.getElementById(col).innerHTML = "";
        });

        snapshot.forEach((doc) => {
            const customer = doc.data();
            const card = createCustomerCard(doc.id, customer);
            const colId = columns.includes(customer.status) ? customer.status : "Planning";
            document.getElementById(colId).appendChild(card);
        });
    });
}

// Create card element
function createCustomerCard(id, customer) {
    const card = document.createElement("div");
    card.className = "bg-white p-4 rounded shadow border border-gray-200 cursor-move hover:shadow-md transition";
    card.draggable = true;
    card.id = id;

    // Use a placeholder if no photo URL
    const photoURL = customer.photoURL || "https://via.placeholder.com/150";

    card.innerHTML = `
        <img src="${photoURL}" class="w-full h-32 object-cover rounded mb-3" alt="${customer.name}">
        <a href="view-customer.html?id=${id}" class="text-lg font-bold text-blue-600 hover:underline block">${customer.name || 'Unnamed Customer'}</a>
        <p class="text-gray-600">Balance: $${(customer.balance || 0).toFixed(2)}</p>
    `;

    // Drag events
    card.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", id);
        card.classList.add("opacity-50");
    });

    card.addEventListener("dragend", () => {
        card.classList.remove("opacity-50");
    });

    return card;
}

// Setup drop zones
function setupDragAndDrop() {
    columns.forEach(colId => {
        const column = document.getElementById(colId);

        column.addEventListener("dragover", (e) => {
            e.preventDefault();
            column.classList.add("drag-over");
        });

        column.addEventListener("dragleave", () => {
            column.classList.remove("drag-over");
        });

        column.addEventListener("drop", async (e) => {
            e.preventDefault();
            column.classList.remove("drag-over");
            
            const customerId = e.dataTransfer.getData("text/plain");
            const newStatus = colId;

            try {
                const customerRef = doc(db, "customers", customerId);
                await updateDoc(customerRef, { status: newStatus });
                showFeedback(`Customer moved to ${newStatus}`);
            } catch (error) {
                console.error("Error updating status:", error);
                showFeedback("Error updating status.");
            }
        });
    });
}

// Handle Add Customer
document.getElementById("add-customer-btn").addEventListener("click", async () => {
    try {
        const docRef = await addDoc(collection(db, "customers"), {
            name: "New Customer",
            status: "Planning",
            balance: 0,
            photoURL: "",
            notes: ""
        });
        window.location.href = `view-customer.html?id=${docRef.id}`;
    } catch (error) {
        console.error("Error adding customer:", error);
        showFeedback("Error adding customer.");
    }
});

// Initialize
loadCustomers();
setupDragAndDrop();
