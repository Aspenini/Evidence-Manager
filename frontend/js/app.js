const { invoke } = window.__TAURI__.tauri;

const elements = {
  search: document.getElementById("search"),
  personList: document.getElementById("person-list"),
  emptyState: document.getElementById("empty-state"),
  details: document.getElementById("person-details"),
  personName: document.getElementById("person-name"),
  personMeta: document.getElementById("person-meta"),
  infoList: document.getElementById("info-list"),
  quoteList: document.getElementById("quote-list"),
  evidenceTable: document.querySelector("#evidence-table tbody"),
  status: document.getElementById("status"),
  addPersonInput: document.getElementById("new-person-name"),
  addPersonButton: document.getElementById("add-person-button"),
  addInfoForm: document.getElementById("add-info-form"),
  infoType: document.getElementById("info-type"),
  infoValue: document.getElementById("info-value"),
  addQuoteForm: document.getElementById("add-quote-form"),
  quoteText: document.getElementById("quote-text"),
  quoteDate: document.getElementById("quote-date"),
  quoteTime: document.getElementById("quote-time"),
  quotePlace: document.getElementById("quote-place"),
  deletePerson: document.getElementById("delete-person"),
  refreshEvidence: document.getElementById("refresh-evidence"),
  addEvidence: document.getElementById("add-evidence"),
};

let persons = [];
let filteredIds = [];
let selectedPersonId = null;

function describeError(error) {
  if (!error) return "Unknown error";
  if (typeof error === "string") return error;
  if (error.message) return error.message;
  try {
    return JSON.stringify(error);
  } catch (_) {
    return String(error);
  }
}

function setStatus(message, type = "info") {
  if (!message) {
    elements.status.textContent = "";
    elements.status.className = "status-bar";
    return;
  }

  elements.status.textContent = message;
  elements.status.className = `status-bar ${type}`;
}

function formatDate(dateString) {
  try {
    return new Date(dateString).toLocaleString();
  } catch (err) {
    return dateString;
  }
}

function formatBytes(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(unit === 0 ? 0 : 1)} ${units[unit]}`;
}

function renderPersonList() {
  const query = elements.search.value.trim().toLowerCase();
  filteredIds = persons
    .filter((person) => person.name.toLowerCase().includes(query))
    .map((person) => person.id);

  elements.personList.innerHTML = "";

  if (filteredIds.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No people found";
    li.classList.add("empty");
    elements.personList.appendChild(li);
    return;
  }

  filteredIds.forEach((id) => {
    const person = persons.find((p) => p.id === id);
    if (!person) return;
    const li = document.createElement("li");
    li.textContent = person.name;
    if (id === selectedPersonId) {
      li.classList.add("active");
    }
    li.addEventListener("click", () => selectPerson(id));
    elements.personList.appendChild(li);
  });
}

function renderInfo(person) {
  elements.infoList.innerHTML = "";
  person.information.forEach((info) => {
    const li = document.createElement("li");
    li.className = "info-item";
    const content = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = info.info_type;
    const value = document.createElement("p");
    value.textContent = info.value;
    value.className = "meta";

    content.appendChild(title);
    content.appendChild(value);

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", async () => {
      await removeInformation(person.id, info.id);
    });

    li.appendChild(content);
    li.appendChild(removeBtn);
    elements.infoList.appendChild(li);
  });
}

function renderQuotes(person) {
  elements.quoteList.innerHTML = "";
  person.quotes.forEach((quote) => {
    const li = document.createElement("li");
    li.className = "quote-item";

    const content = document.createElement("div");
    const text = document.createElement("p");
    text.textContent = `"${quote.quote}"`;
    const meta = document.createElement("span");
    const parts = [quote.date];
    if (quote.time) parts.push(quote.time);
    if (quote.place) parts.push(quote.place);
    meta.textContent = parts.join(" • ");
    meta.className = "meta";

    content.appendChild(text);
    content.appendChild(meta);

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", async () => {
      await removeQuote(person.id, quote.id);
    });

    li.appendChild(content);
    li.appendChild(removeBtn);
    elements.quoteList.appendChild(li);
  });
}

function renderEvidence(rows) {
  elements.evidenceTable.innerHTML = "";
  rows.forEach((item) => {
    const tr = document.createElement("tr");
    const fileCell = document.createElement("td");
    fileCell.textContent = item.original_name;
    const typeCell = document.createElement("td");
    typeCell.textContent = item.file_type;
    const sizeCell = document.createElement("td");
    sizeCell.textContent = formatBytes(item.size);
    const createdCell = document.createElement("td");
    createdCell.textContent = formatDate(item.created_at);
    tr.append(fileCell, typeCell, sizeCell, createdCell);
    elements.evidenceTable.appendChild(tr);
  });
}

function renderDetails(person) {
  if (!person) {
    elements.details.classList.add("hidden");
    elements.emptyState.classList.remove("hidden");
    renderEvidence([]);
    return;
  }

  elements.emptyState.classList.add("hidden");
  elements.details.classList.remove("hidden");
  elements.personName.textContent = person.name;
  elements.personMeta.textContent = `Created ${formatDate(person.created_at)} • Updated ${formatDate(person.updated_at)}`;

  renderInfo(person);
  renderQuotes(person);
  renderEvidence([]);
}

async function refreshEvidence() {
  if (!selectedPersonId) return;
  try {
    const rows = await invoke("scan_evidence", { person_id: selectedPersonId });
    renderEvidence(rows.map((row) => ({
      ...row,
      file_type: typeof row.file_type === "string" ? row.file_type : row.file_type?.replace(/_/g, " "),
    })));
    setStatus("Evidence list refreshed");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to refresh evidence: ${describeError(error)}`, "error");
  }
}

async function loadPersons() {
  try {
    persons = await invoke("list_persons");
    renderPersonList();
    if (selectedPersonId) {
      const person = persons.find((p) => p.id === selectedPersonId);
      if (person) {
        renderDetails(person);
        await refreshEvidence();
        return;
      }
    }
    selectedPersonId = null;
    renderDetails(null);
  } catch (error) {
    console.error(error);
    setStatus(`Failed to load persons: ${describeError(error)}`, "error");
  }
}

async function selectPerson(id) {
  selectedPersonId = id;
  renderPersonList();
  const person = persons.find((p) => p.id === id);
  renderDetails(person);
  await refreshEvidence();
}

async function addPerson() {
  const name = elements.addPersonInput.value.trim();
  if (!name) return;
  try {
    const person = await invoke("add_person", { name });
    persons.push(person);
    elements.addPersonInput.value = "";
    setStatus(`Added ${person.name}`);
    renderPersonList();
    await selectPerson(person.id);
  } catch (error) {
    console.error(error);
    setStatus(`Failed to add person: ${describeError(error)}`, "error");
  }
}

async function deletePerson() {
  if (!selectedPersonId) return;
  const person = persons.find((p) => p.id === selectedPersonId);
  if (!person) return;
  if (!confirm(`Delete ${person.name}? This will remove their evidence.`)) return;

  try {
    await invoke("delete_person", { person_id: selectedPersonId });
    persons = persons.filter((p) => p.id !== selectedPersonId);
    selectedPersonId = null;
    renderPersonList();
    renderDetails(null);
    setStatus("Person deleted");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to delete person: ${describeError(error)}`, "error");
  }
}

async function addInformation(personId, infoType, value) {
  try {
    const updated = await invoke("add_information", {
      person_id: personId,
      info_type: infoType,
      value,
    });
    persons = persons.map((p) => (p.id === updated.id ? updated : p));
    renderDetails(updated);
    setStatus("Information added");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to add information: ${describeError(error)}`, "error");
  }
}

async function removeInformation(personId, infoId) {
  try {
    const updated = await invoke("remove_information", {
      person_id: personId,
      info_id: infoId,
    });
    persons = persons.map((p) => (p.id === updated.id ? updated : p));
    renderDetails(updated);
    setStatus("Information removed");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to remove information: ${describeError(error)}`, "error");
  }
}

async function addQuote(personId, quote, date, time, place) {
  try {
    const updated = await invoke("add_quote", {
      person_id: personId,
      quote,
      date,
      time: time || null,
      place: place || null,
    });
    persons = persons.map((p) => (p.id === updated.id ? updated : p));
    renderDetails(updated);
    setStatus("Quote added");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to add quote: ${describeError(error)}`, "error");
  }
}

async function removeQuote(personId, quoteId) {
  try {
    const updated = await invoke("remove_quote", {
      person_id: personId,
      quote_id: quoteId,
    });
    persons = persons.map((p) => (p.id === updated.id ? updated : p));
    renderDetails(updated);
    setStatus("Quote removed");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to remove quote: ${describeError(error)}`, "error");
  }
}

async function addEvidence() {
  if (!selectedPersonId) return;
  const sourcePath = prompt("Enter the full path to the evidence file");
  if (!sourcePath) return;
  const evidenceType = prompt(
    "Enter the evidence type (image, audio, video, document, quote)",
    "document"
  );
  if (!evidenceType) return;

  try {
    await invoke("add_evidence", {
      request: {
        person_id: selectedPersonId,
        source_path: sourcePath,
        evidence_type: evidenceType,
      },
    });
    await refreshEvidence();
    setStatus("Evidence copied");
  } catch (error) {
    console.error(error);
    setStatus(`Failed to add evidence: ${describeError(error)}`, "error");
  }
}

function registerEvents() {
  elements.search.addEventListener("input", () => renderPersonList());
  elements.addPersonButton.addEventListener("click", addPerson);
  elements.addPersonInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addPerson();
    }
  });

  elements.addInfoForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedPersonId) return;
    const infoType = elements.infoType.value.trim();
    const value = elements.infoValue.value.trim();
    if (!infoType || !value) return;
    await addInformation(selectedPersonId, infoType, value);
    elements.infoType.value = "";
    elements.infoValue.value = "";
  });

  elements.addQuoteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!selectedPersonId) return;
    const quote = elements.quoteText.value.trim();
    const date = elements.quoteDate.value;
    const time = elements.quoteTime.value;
    const place = elements.quotePlace.value.trim();
    if (!quote || !date) return;
    await addQuote(selectedPersonId, quote, date, time, place);
    elements.quoteText.value = "";
    elements.quoteDate.value = "";
    elements.quoteTime.value = "";
    elements.quotePlace.value = "";
  });

  elements.deletePerson.addEventListener("click", deletePerson);
  elements.refreshEvidence.addEventListener("click", refreshEvidence);
  elements.addEvidence.addEventListener("click", addEvidence);
}

registerEvents();
loadPersons();
