// ---------- Reusable Alert Function ----------
function showAlert(message, type = "success") {
    const alertBox = document.getElementById("alertBox");
    alertBox.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    setTimeout(() => {
        const alertEl = document.querySelector(".alert");
        if (alertEl) {
            alertEl.classList.remove("show");
        }
    }, 4000);
}

// ---------- On Load ----------
$(document).ready(function() {
    loadMappings();
    loadLogs();
});

// ---------- Email Mappings ----------
function addMapping() {
    let email = $("#mapEmail").val();
    let username = $("#mapUsername").val();
    $.ajax({
        url: "/add_mapping",
        method: "POST",
        contentType: "application/json",
        data: JSON.stringify({ email: email, username: username }),
        success: function(data) {
            showAlert("✅ Mapping added successfully!", "success");
            loadMappings();
        },
        error: function() {
            showAlert("❌ Failed to add mapping.", "danger");
        }
    });
}

function loadMappings() {
    $.get("/get_mappings", function(data) {
        if (Array.isArray(data) && data.length > 0) {
            let table = `<table class="table table-bordered table-striped">
                            <thead><tr><th>Email</th><th>Username</th></tr></thead><tbody>`;
            data.forEach(row => {
                table += `<tr><td>${row.email}</td><td>${row.username}</td></tr>`;
            });
            table += `</tbody></table>`;
            $("#mapTableContainer").html(table);
        } else {
            $("#mapTableContainer").html("<p class='text-muted'>No mappings found.</p>");
        }
    });
}

// ---------- Search ----------
function searchEmail() {
    let email = $("#email").val();
    $.get(`/search_email?email=${email}`, function(data){
        $("#emailResult").text(JSON.stringify(data, null, 2));
        showAlert("ℹ️ Search completed", "info");
    }).fail(() => showAlert("❌ Failed to search email.", "danger"));
}

// ---------- Repositories ----------
function listRepos() {
    let username = $("#username").val();
    $.get(`/repos?username=${username}`, function(data){
        $("#reposResult").text(JSON.stringify(data, null, 2));
        showAlert("📂 Repositories loaded", "success");
    }).fail(() => showAlert("❌ Failed to load repositories.", "danger"));
}

// ---------- Collaborators ----------
function loadCollaborators() {
    let owner = $("#owner").val();
    let repo = $("#repo").val();
    if (!owner || !repo) {
        showAlert("⚠️ Enter owner and repo first.", "warning");
        return;
    }

    $.get(`/collaborators?owner=${owner}&repo=${repo}`, function(data) {
        if (Array.isArray(data) && data.length > 0) {
            let table = `<table class="table table-bordered table-striped">
                            <thead>
                              <tr>
                                <th>Avatar</th>
                                <th>Username</th>
                                <th>Role</th>
                                <th>Permissions</th>
                              </tr>
                            </thead>
                            <tbody>`;
            data.forEach(user => {
                table += `<tr>
                            <td><img src="${user.avatar_url}" width="40" class="rounded-circle"></td>
                            <td>${user.login}</td>
                            <td>${user.role_name || 'N/A'}</td>
                            <td>
                                Admin: ${user.permissions?.admin ? "✅" : "❌"} |
                                Push: ${user.permissions?.push ? "✅" : "❌"} |
                                Pull: ${user.permissions?.pull ? "✅" : "❌"}
                            </td>
                          </tr>`;
            });
            table += `</tbody></table>`;
            $("#collabTableContainer").html(table);
        } else {
            $("#collabTableContainer").html("<p class='text-muted'>No collaborators found.</p>");
        }
    }).fail(() => showAlert("❌ Failed to fetch collaborators.", "danger"));
}

function addCollaborator() {
    let owner = $("#owner").val();
    let repo = $("#repo").val();
    let username = $("#collabUsername").val();
    let permission = $("#permission").val();
    $.get(`/add_collaborator?owner=${owner}&repo=${repo}&username=${username}&permission=${permission}`, function(data){
        showAlert(data.message || "✅ Collaborator added", "success");
        loadCollaborators();
        loadLogs();
    }).fail(() => showAlert("❌ Failed to add collaborator.", "danger"));
}

function removeCollaborator() {
    let owner = $("#owner").val();
    let repo = $("#repo").val();
    let username = $("#collabUsername").val();
    $.get(`/remove_collaborator?owner=${owner}&repo=${repo}&username=${username}`, function(data){
        showAlert(data.message || "✅ Collaborator removed", "warning");
        loadCollaborators();
        loadLogs();
    }).fail(() => showAlert("❌ Failed to remove collaborator.", "danger"));
}

// ---------- Bulk ----------
function previewBulk() {
    let file = $("#bulkFile")[0].files[0];
    let formData = new FormData();
    formData.append("file", file);
    $.ajax({
        url: "/bulk_preview",
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            $("#bulkResult").text(JSON.stringify(data, null, 2));
            showAlert("📦 Bulk preview ready", "info");
        },
        error: function() {
            showAlert("❌ Bulk preview failed.", "danger");
        }
    });
}

function applyBulk() {
    let owner = $("#bulkOwner").val();
    let repo = $("#bulkRepo").val();
    let file = $("#bulkFile")[0].files[0];
    let formData = new FormData();
    formData.append("file", file);
    $.ajax({
        url: `/bulk_apply?owner=${owner}&repo=${repo}`,
        method: "POST",
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            $("#bulkResult").text(JSON.stringify(data, null, 2));
            showAlert("✅ Bulk changes applied", "success");
            loadLogs();
        },
        error: function() {
            showAlert("❌ Bulk apply failed.", "danger");
        }
    });
}

// ---------- Reports ----------
function generateReport(type) {
    let owner = $("#reportOwner").val();
    let repo = $("#reportRepo").val();
    let url = type === "excel" ? "/report_excel" : "/report_pdf";
    $.get(`${url}?owner=${owner}&repo=${repo}`, function(data){
        $("#reportResult").text(JSON.stringify(data, null, 2));
        showAlert(`📊 ${type.toUpperCase()} report generated`, "success");
    }).fail(() => showAlert("❌ Report generation failed.", "danger"));
}

// ---------- Logs ----------
function loadLogs() {
    $.get("/get_logs", function(data) {
        if (Array.isArray(data) && data.length > 0) {
            let table = `<table class="table table-bordered table-striped">
                            <thead><tr><th>ID</th><th>Action</th><th>Repo</th><th>User</th><th>Permission</th><th>Status</th><th>Timestamp</th></tr></thead><tbody>`;
            data.forEach(row => {
                table += `<tr>
                            <td>${row.id || ''}</td>
                            <td>${row.action || ''}</td>
                            <td>${row.repo || ''}</td>
                            <td>${row.username || ''}</td>
                            <td>${row.permission || ''}</td>
                            <td>${row.status || ''}</td>
                            <td>${row.timestamp || ''}</td>
                          </tr>`;
            });
            table += `</tbody></table>`;
            $("#logsTableContainer").html(table);
        } else {
            $("#logsTableContainer").html("<p class='text-muted'>No logs found.</p>");
        }
    }).fail(() => showAlert("❌ Failed to load logs.", "danger"));
}
