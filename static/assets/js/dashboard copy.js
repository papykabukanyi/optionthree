$(document).ready(function () {
    const table = $('#submissionsTable').DataTable({
        responsive: false,
        columnDefs: [],
        order: [[0, 'asc']]
    });

    // Handle delete button click
    $('#submissionsTable tbody').on('click', 'button.btn-delete', function () {
        const submissionId = $(this).data('id');
        if (confirm('Are you sure you want to delete this submission?')) {
            $.ajax({
                url: `/api/submissions/${submissionId}`,
                method: 'DELETE',
                success: function () {
                    table.row($(`#submission-${submissionId}`)).remove().draw();
                    alert('Submission deleted successfully.');
                },
                error: function () {
                    alert('Failed to delete submission.');
                }
            });
        }
    });

    // Handle view details button click
    $('#submissionsTable tbody').on('click', 'button.btn-view-details', function () {
        const submissionId = $(this).data('id');
        const details = $(this).data('details');
        const row = table.row($(this).parents('tr'));

        // Updated detailsHtml with support for email replies and attachments
        const detailsHtml = `
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <p><strong>Application ID:</strong> ${details.app_id || 'N/A'}</p>
                    <p><strong>Company Name:</strong> ${details.company_name || 'N/A'}</p>
                    <p><strong>Time in Business:</strong> ${details.time_in_business || 'N/A'}</p>
                    <p><strong>Address:</strong> ${details.address_line_1 || ''}, ${details.city || ''}, ${details.state || ''} ${details.zip_code || ''}</p>
                    <p><strong>Company Email:</strong> ${details.company_email || 'N/A'}</p>
                    <p><strong>Company Phone:</strong> ${details.company_phone || 'N/A'}</p>
                    <p><strong>EIN / TAX ID Number:</strong> ${details.ein || 'N/A'}</p>
                    <p><strong>Type of Business:</strong> ${details.business_type || 'N/A'}</p>
                    <p><strong>Borrower Name:</strong> ${details.borrower_first_name || ''} ${details.borrower_last_name || ''}</p>
                    <p><strong>Date of Birth:</strong> ${details.borrower_dob || 'N/A'}</p>
                    <p><strong>Percent Ownership:</strong> ${details.borrower_ownership || 'N/A'}</p>
                    <p><strong>SSN:</strong> ${details.borrower_ssn || 'N/A'}</p>
                    <p><strong>Phone:</strong> ${details.borrower_phone || 'N/A'}</p>
                    <p><strong>Email:</strong> ${details.borrower_email || 'N/A'}</p>
                    <p><strong>Preferred Method of Contact:</strong> ${details.borrower_preferred_contact || 'N/A'}</p>
                    <p><strong>Borrower Address:</strong> ${details.borrower_address_line_1 || ''}, ${details.borrower_city || ''}, ${details.borrower_state || ''} ${details.borrower_zip_code || ''}</p>
                    <p><strong>Co-Applicant Name:</strong> ${details.coapplicant_first_name || ''} ${details.coapplicant_last_name || ''}</p>
                    <p><strong>Co-Applicant Date of Birth:</strong> ${details.coapplicant_dob || 'N/A'}</p>
                    <p><strong>Co-Applicant Percent Ownership:</strong> ${details.coapplicant_ownership || 'N/A'}</p>
                    <p><strong>Co-Applicant SSN:</strong> ${details.coapplicant_ssn || 'N/A'}</p>
                    <p><strong>Co-Applicant Phone:</strong> ${details.coapplicant_phone || 'N/A'}</p>
                    <p><strong>Co-Applicant Email:</strong> ${details.coapplicant_email || 'N/A'}</p>
                    <p><strong>Co-Applicant Address:</strong> ${details.coapplicant_address_line_1 || ''}, ${details.coapplicant_city || ''}, ${details.coapplicant_state || ''} ${details.coapplicant_zip_code || ''}</p>
                    <p><strong>Loan Amount:</strong> ${details.loan_amount || 'N/A'}</p>
                    <p><strong>Max Down Payment:</strong> ${details.max_down_payment || 'N/A'}</p>
                    <p><strong>Equipment & Seller Info:</strong> ${details.equipment_seller_info || 'N/A'}</p>
                    <p><strong>Submission Time:</strong> ${details.submission_time || 'N/A'}</p>
                    <p><strong>Browser:</strong> ${details.browser || 'N/A'}</p>
                    <p><strong>IP Address:</strong> ${details.ip_address || 'N/A'}</p>
                    <p><strong>Unique ID:</strong> ${details.unique_id || 'N/A'}</p>
                    <p><strong>Location:</strong> ${details.location || 'N/A'}</p>
                    <p><strong>Uploaded Files:</strong></p>
                    ${(details.uploaded_files || []).map(file => `<p><a href="/uploads/${file}" target="_blank">${file}</a></p>`).join('')}
                    <p><strong>Application PDF:</strong> <a href="/uploads/${details.pdf_filename || ''}" target="_blank">${details.pdf_filename || 'N/A'}</a></p>
                </div>
                <div style="width: 45%; padding-left: 20px;">
                    <h5>Notes✨ & Status Updates🔌</h5>
                    <div id="notes-section-${submissionId}" class="notes-section"></div>
                    <div class="notes-container">
                        <textarea id="note-input-${submissionId}" rows="3" placeholder="Add a new note...👀"></textarea>
                        <button class="btn btn-primary btn-send-note mt-2" onclick="saveNote(${submissionId})">Save Note🔥</button>
                    </div>
                    <h6 class="mt-3">Status Update🤗</h6>
                    <div style="display: flex; align-items: center;">
                        <select id="status-select-${submissionId}" class="form-control status-select">
                            <option value="">Select Status</option>
                            <option value="In Review">In Review🙃</option>
                            <option value="Rejected">Rejected😥</option>
                            <option value="Approved">Approved🎉</option>
                        </select>
                        <button class="btn btn-success btn-send-status" onclick="sendStatusUpdate(${submissionId})">Send⚡</button>
                        <span id="status-loader-${submissionId}" style="display: none; margin-left: 10px;">Loading...</span>
                        <span id="status-check-${submissionId}" style="display: none; color: green; margin-left: 10px;">&#10003;</span>
                    </div>
                </div>
            </div>`;

        if (row.child.isShown()) {
            row.child.hide();
            $(this).text('View Details');
        } else {
            row.child(detailsHtml).show();
            $(this).text('Hide Details');
            loadNotesAndReplies(submissionId); // Load notes and replies for this submission
        }
    });
});

// Save note function with @email feature
function saveNote(submissionId) {
    const note = $(`#note-input-${submissionId}`).val();
    if (!note) return alert("Please enter a note.");

    // Check for @email prefix to send an email
    const sendEmail = note.startsWith("@email");

    $.ajax({
        url: `/api/submissions/${submissionId}/note`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ note, sendEmail }),  // Include the flag
        success: function () {
            $(`#note-input-${submissionId}`).val(''); // Clear input
            loadNotesAndReplies(submissionId); // Reload notes and replies section
        },
        error: function () {
            alert('Failed to save note.');
        }
    });
}

// Load notes and replies function with attachments handling
function loadNotesAndReplies(submissionId) {
    $.ajax({
        url: `/api/submissions/${submissionId}/notes`,
        method: 'GET',
        success: function (notes) {
            const notesSection = $(`#notes-section-${submissionId}`);
            notesSection.empty();

            // Sort notes by timestamp from oldest to newest
            notes.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

            notes.forEach(note => {
                const timeAgo = formatTimeAgo(note.timestamp);
                let noteHtml = `<div><strong>${timeAgo}:</strong> ${note.note}</div>`;
                
                // Check if the note has attachments
                if (note.attachments && note.attachments.length > 0) {
                    noteHtml += `<div>Attachments:</div>`;
                    note.attachments.forEach(file => {
                        noteHtml += `<div><a href="/uploads/${file}" target="_blank">${file}</a></div>`;
                    });
                }

                notesSection.append(noteHtml);
            });

            scrollToBottom(notesSection); // Auto-scroll to the latest note
        },
        error: function () {
            alert('Failed to load notes.');
        }
    });
}

// Scroll to the bottom of the notes section
function scrollToBottom(element) {
    element.scrollTop(element.prop("scrollHeight"));
}

// Send status update function with loader and note entry
function sendStatusUpdate(submissionId) {
    const status = $(`#status-select-${submissionId}`).val();
    if (!status) return alert("Please select a status.");

    $(`#status-loader-${submissionId}`).show();
    $(`#status-check-${submissionId}`).hide();

    $.ajax({
        url: `/api/submissions/${submissionId}/status`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ status }),
        success: function () {
            $(`#status-loader-${submissionId}`).hide();
            $(`#status-check-${submissionId}`).show();
            setTimeout(() => $(`#status-check-${submissionId}`).hide(), 2000);
            saveNoteWithStatus(submissionId, `Status updated to ${status}`);
        },
        error: function () {
            $(`#status-loader-${submissionId}`).hide();
            alert('Failed to send status update.');
        }
    });
}

// Save a note specifically for a status update
function saveNoteWithStatus(submissionId, note) {
    $.ajax({
        url: `/api/submissions/${submissionId}/note`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ note }),
        success: function () {
            loadNotesAndReplies(submissionId); // Reload notes section
        },
        error: function () {
            alert('Failed to save status update note.');
        }
    });
}

// "Time ago" formatter function using Moment.js to calculate based on server time
function formatTimeAgo(timestamp) {
    const time = moment.utc(timestamp);  // Convert timestamp to UTC moment
    return time.local().fromNow();       // Convert to local time and format as "time ago"
}

// Dark mode setup
$(document).ready(function () {
    $('#settingsIcon').click(function () {
        $('#themeToggle').toggle();
    });

    $('body').addClass('dark-mode');

    $('#darkModeBtn').click(function () {
        $('body').addClass('dark-mode');
        $('#themeToggle').hide();
    });

    $('#lightModeBtn').click(function () {
        $('body').removeClass('dark-mode');
        $('#themeToggle').hide();
    });
});
