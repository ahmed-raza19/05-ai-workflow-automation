const systemDot = document.getElementById("system-dot");
const systemStatus = document.getElementById("system-status");
const llmState = document.getElementById("llm-state");
const ticketsTotal = document.getElementById("tickets-total");
const ticketForm = document.getElementById("ticket-form");
const customerNameInput = document.getElementById("customer-name");
const subjectInput = document.getElementById("subject");
const messageInput = document.getElementById("message");
const resetBtn = document.getElementById("reset-btn");
const feedback = document.getElementById("feedback");
const emptyState = document.getElementById("empty-state");
const resultWrap = document.getElementById("result-wrap");
const sourcePill = document.getElementById("decision-source");
const ticketId = document.getElementById("ticket-id");
const category = document.getElementById("category");
const priority = document.getElementById("priority");
const department = document.getElementById("department");
const reviewFlag = document.getElementById("review-flag");
const summary = document.getElementById("summary");
const reply = document.getElementById("reply");
const exampleBtns = document.querySelectorAll(".example-btn");

let processedCount = 0;

function setFeedback(message, isError = false) {
    feedback.textContent = message;
    feedback.style.color = isError ? "#b91c1c" : "var(--muted)";
}

function setChipState(value) {
    sourcePill.textContent = value;
    sourcePill.style.background =
        value === "llm" ? "rgba(16, 185, 129, 0.12)" : "rgba(245, 158, 11, 0.12)";
    sourcePill.style.color = value === "llm" ? "#059669" : "#b45309";
}

function renderDecision(data) {
    ticketId.textContent = data.ticket_id;
    category.textContent = data.category;
    priority.textContent = data.priority;
    department.textContent = data.department;
    reviewFlag.textContent = data.requires_human_review ? "Yes" : "No";
    reviewFlag.style.color = data.requires_human_review ? "#b91c1c" : "#059669";
    summary.textContent = data.summary;
    reply.textContent = data.suggested_reply;
    setChipState(data.decision_source || "rule_based_fallback");

    emptyState.classList.add("hidden");
    resultWrap.classList.remove("hidden");
    processedCount += 1;
    ticketsTotal.textContent = String(processedCount);
}

async function loadSystemStatus() {
    try {
        const response = await fetch("/status");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to load status");
        }

        systemDot.classList.add("online");
        systemStatus.textContent = "Ready";
        llmState.textContent = data.llm_available
            ? "LLM decisioning is enabled."
            : "LLM unavailable; rule fallback is active.";
    } catch (error) {
        systemDot.classList.add("offline");
        systemStatus.textContent = "Offline";
        llmState.textContent = "Could not read system status.";
    }
}

async function submitTicket(event) {
    event.preventDefault();

    const payload = {
        customer_name: customerNameInput.value.trim(),
        subject: subjectInput.value.trim(),
        message: messageInput.value.trim(),
    };

    if (!payload.customer_name || !payload.subject || !payload.message) {
        setFeedback("Fill in all three fields before routing the ticket.", true);
        return;
    }

    setFeedback("Routing ticket...");

    try {
        const response = await fetch("/submit-ticket", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Unable to process ticket.");
        }

        renderDecision(data);
        setFeedback(`Ticket routed to ${data.department}.`);
    } catch (error) {
        setFeedback(error.message, true);
    }
}

function fillExample(button) {
    customerNameInput.value = button.dataset.name || "";
    subjectInput.value = button.dataset.subject || "";
    messageInput.value = button.dataset.message || "";
    customerNameInput.focus();
}

function resetForm() {
    ticketForm.reset();
    setFeedback("");
    emptyState.classList.remove("hidden");
    resultWrap.classList.add("hidden");
    subjectInput.focus();
}

exampleBtns.forEach((button) => {
    button.addEventListener("click", () => fillExample(button));
});

ticketForm.addEventListener("submit", submitTicket);
resetBtn.addEventListener("click", resetForm);

loadSystemStatus();
