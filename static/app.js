function filterTable(inputId, tableId) {
    const query = document.getElementById(inputId).value.toLowerCase();
    document.querySelectorAll(`#${tableId} tbody tr`).forEach((row) => {
        row.style.display = row.innerText.toLowerCase().includes(query) ? '' : 'none';
    });
}
