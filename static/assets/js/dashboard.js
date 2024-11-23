$(document).ready(function () {
    console.log("Initializing dashboard...");
    
    // Initialize layout
    $('#main-layout').w2layout({
        name: 'layout',
        panels: [
            { type: 'left', size: 150, resizable: false, minSize: 120 },
            { type: 'main', minSize: 550 }
        ]
    });
    
    console.log("Initializing sidebar...");
    
    // Initialize sidebar with "Submissions", "Vendors", and "Analytics"
    $().w2sidebar({
        name: 'sidebar',
        nodes: [{
            id: 'menu',
            text: 'Menu',
            group: true,
            expanded: true,
            nodes: [
                { id: 'submissions', text: 'Submissions', icon: 'fa fa-university' },
                { id: 'vendors', text: 'Vendors', icon: 'fa fa-briefcase' },
                { id: 'analytics', text: 'Analytics', icon: 'fa fa-chart-bar' }
            ]
        }],
        onClick: function (event) {
            console.log("Sidebar item clicked:", event.target);
            
            if (event.target === 'submissions') {
                w2ui.layout.html('main', '<div id="submissionsTableWrapper" style="width: 100%; height: 100%;"></div>');
                loadSubmissionsGrid();
            } else if (event.target === 'vendors') {
                w2ui.layout.html('main', '<div id="vendorsTableWrapper" style="width: 100%; height: 100%;"></div>');
                loadVendorsGrid();
            } else if (event.target === 'analytics') {
                w2ui.layout.html('main', '<div id="analyticsContent" style="padding: 20px;"><h2>Analytics Dashboard</h2><p>Here is where analytics data will be displayed.</p></div>');
            }
        }
    });
    
    console.log("Rendering sidebar in layout...");
    w2ui.layout.html('left', w2ui['sidebar']);

    // Load W2UI grid for submissions
    function loadSubmissionsGrid() {
        console.log("Loading submissions grid...");
        
        if (w2ui['submissionsGrid']) w2ui['submissionsGrid'].destroy();
        $('#submissionsTableWrapper').w2grid({
            name: 'submissionsGrid',
            show: { toolbar: true, footer: true },
            columns: [
                { field: 'app_id', text: 'ID', size: '150px' },
                { field: 'company_name', text: 'Business Name', size: '550px' },
                { field: 'borrower_name', text: 'Borrower Name', size: '350px' },
                { field: 'submission_time', text: 'Submission Time', size: '200px' },
                {
                    field: 'actions',
                    text: 'Actions',
                    size: '110px',
                    render: function (record) {
                        return `<button class="w2ui-btn w2ui-btn-blue btn-view-details" data-recid="${record.recid}">View Details</button>`;
                    }
                }
            ],
            records: [],
            onRender: function () {
                $('#submissionsTableWrapper').off('click', '.btn-view-details').on('click', '.btn-view-details', function () {
                    const recid = $(this).data('recid');
                    const record = w2ui['submissionsGrid'].get(recid);
                    if (record) {
                        viewSubmissionDetails(record);
                    } else {
                        console.error("Record not found for recid:", recid);
                    }
                });
            }
        });
        loadSubmissionsData();
    }

    // Load W2UI grid for vendors
    function loadVendorsGrid() {
        console.log("Loading vendors grid...");
        
        if (w2ui['vendorsGrid']) w2ui['vendorsGrid'].destroy();
        $('#vendorsTableWrapper').w2grid({
            name: 'vendorsGrid',
            show: { toolbar: true, footer: true },
            columns: [
                { field: 'vendor_id', text: 'Vendor ID', size: '150px' },
                { field: 'business_name', text: 'Business Name', size: '550px' },
                { field: 'contact_name', text: 'Contact Name', size: '350px' },
                { field: 'contact_email', text: 'Contact Email', size: '200px' },
                {
                    field: 'actions',
                    text: 'Actions',
                    size: '110px',
                    render: function (record) {
                        return `<button class="w2ui-btn w2ui-btn-blue btn-view-vendor" data-recid="${record.recid}">View Vendor</button>`;
                    }
                }
            ],
            records: [],
            onRender: function () {
                $('#vendorsTableWrapper').off('click', '.btn-view-vendor').on('click', '.btn-view-vendor', function () {
                    const recid = $(this).data('recid');
                    const record = w2ui['vendorsGrid'].get(recid);
                    if (record) {
                        viewVendorDetails(record);
                    } else {
                        console.error("Record not found for recid:", recid);
                    }
                });
            }
        });
        loadVendorsData();
    }

    // Load submissions data from the server
    function loadSubmissionsData() {
        console.log("Fetching submissions data from /api/submissions...");
        
        $.ajax({
            url: '/api/submissions',
            method: 'GET',
            success: function (data) {
                console.log("Received submissions data:", data);
                
                const records = data.map((submission, index) => ({
                    recid: index + 1,
                    submission_id: submission.id,
                    app_id: submission.app_id,
                    company_name: submission.data.company_name || 'N/A',
                    borrower_name: `${submission.data.borrower_first_name || ''} ${submission.data.borrower_last_name || ''}`,
                    submission_time: submission.submission_time || 'N/A',
                }));
                w2ui['submissionsGrid'].records = records;
                w2ui['submissionsGrid'].refresh();
            },
            error: function (xhr, status, error) {
                console.error('Failed to load submissions. Status:', status, 'Error:', error);
                alert('Failed to load submissions.');
            }
        });
    }

    // Load vendors data from the server
    function loadVendorsData() {
        console.log("Fetching vendors data from /api/vendors...");
        
        $.ajax({
            url: '/api/vendors',
            method: 'GET',
            success: function (data) {
                console.log("Received vendors data:", data);
                
                const records = data.map((vendor, index) => ({
                    recid: index + 1,
                    vendor_id: vendor.vendor_id,
                    business_name: vendor.business_name || 'N/A',
                    contact_name: `${vendor.first_name || ''} ${vendor.last_name || ''}`,
                    contact_email: vendor.email || 'N/A',
                }));
                w2ui['vendorsGrid'].records = records;
                w2ui['vendorsGrid'].refresh();
            },
            error: function (xhr, status, error) {
                console.error('Failed to load vendors. Status:', status, 'Error:', error);
                alert('Failed to load vendors.');
            }
        });
    }

    // View submission details in a popup
    function viewSubmissionDetails(record) {
        const detailsHtml = `
            <div style="padding: 10px; display: flex; justify-content: space-between;">
                <div style="width: 50%;">
                    <p><strong>Application ID:</strong> ${record.app_id || 'N/A'}</p>
                    <p><strong>Company Name:</strong> ${record.company_name || 'N/A'}</p>
                    <p><strong>Time in Business:</strong> ${record.time_in_business || 'N/A'}</p>
                    <p><strong>Address:</strong> ${record.address_line_1 || ''}, ${record.city || ''}, ${record.state || ''} ${record.zip_code || ''}</p>
                    <p><strong>Company Email:</strong> ${record.company_email || 'N/A'}</p>
                    <p><strong>Company Phone:</strong> ${record.company_phone || 'N/A'}</p>
                </div>
                <div style="width: 45%; padding-left: 20px;">
                    <h5>Notes✨ & Status Updates🔌</h5>
                    <div id="notes-section-${record.submission_id}" class="notes-section"></div>
                    <div class="notes-container">
                        <textarea id="note-input-${record.submission_id}" rows="3" placeholder="Add a new note...👀"></textarea>
                        <button class="w2ui-btn w2ui-btn-blue btn-send-note mt-2" data-submission-id="${record.submission_id}">Save Note🔥</button>
                    </div>
                    <h6 class="mt-3">Status Update🤗</h6>
                    <div style="display: flex; align-items: center;">
                        <select id="status-select-${record.submission_id}" class="form-control status-select">
                            <option value="">Select Status</option>
                            <option value="In Review">In Review🙃</option>
                            <option value="Rejected">Rejected😥</option>
                            <option value="Approved">Approved🎉</option>
                        </select>
                        <button class="w2ui-btn w2ui-btn-green btn-send-status" onclick="sendStatusUpdate(${record.submission_id})">Send⚡</button>
                        <span id="status-loader-${record.submission_id}" style="display: none; margin-left: 10px;">Loading...</span>
                        <span id="status-check-${record.submission_id}" style="display: none; color: green; margin-left: 10px;">&#10003;</span>
                    </div>
                </div>
            </div>`;
        w2popup.open({
            title: record.app_id,
            body: detailsHtml,
            width: 1000,
            height: 600,
            modal: false,
            showClose: true,
            showMax: true,
        });
        loadNotes(record.submission_id);
    }

    // View vendor details in a popup
    function viewVendorDetails(record) {
        const detailsHtml = `
            <div style="padding: 10px; display: flex; justify-content: space-between;">
                <div style="width: 50%;">
                    <p><strong>Business Name:</strong> ${record.business_name || 'N/A'}</p>
                    <p><strong>Contact Name:</strong> ${record.contact_name || 'N/A'}</p>
                    <p><strong>Contact Email:</strong> ${record.contact_email || 'N/A'}</p>
                </div>
                <div style="width: 45%; padding-left: 20px;">
                    <h5>Notes✨ & Status Updates🔌</h5>
                    <div id="notes-section-${record.vendor_id}" class="notes-section"></div>
                    <div class="notes-container">
                        <textarea id="note-input-${record.vendor_id}" rows="3" placeholder="Add a new note...👀"></textarea>
                        <button class="w2ui-btn w2ui-btn-blue btn-send-note mt-2" data-vendor-id="${record.vendor_id}">Save Note🔥</button>
                    </div>
                    <h6 class="mt-3">Status Update🤗</h6>
                    <div style="display: flex; align-items: center;">
                        <select id="status-select-${record.vendor_id}" class="w2ui-select">
                            <option value="">Select Status</option>
                            <option value="In Review">In Review🙃</option>
                            <option value="Rejected">Rejected😥</option>
                            <option value="Approved">Approved🎉</option>
                        </select>
                        <button class="w2ui-btn w2ui-btn-green btn-send-status" onclick="sendStatusUpdate(${record.vendor_id})">Send⚡</button>
                        <span id="status-loader-${record.vendor_id}" style="display: none; margin-left: 10px;">Loading...</span>
                        <span id="status-check-${record.vendor_id}" style="display: none; color: green; margin-left: 10px;">&#10003;</span>
                    </div>
                </div>
            </div>`;
        w2popup.open({
            title: record.business_name,
            body: detailsHtml,
            width: 1000,
            height: 600,
            modal: false,
            showClose: true,
            showMax: true,
        });
        loadNotes(record.vendor_id);
    }

    // Additional unchanged methods: sendStatusUpdate, saveNoteForRecord, loadNotes, formatTimeAgo, etc.
    // Send status update
    function sendStatusUpdate(id) {
        const status = $(`#status-select-${id}`).val();
        if (!status) return alert("Please select a status.");
        $(`#status-loader-${id}`).show();
        $.ajax({
            url: `/api/submissions/${id}/status`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ status }),
            success: function () {
                $(`#status-loader-${id}`).hide();
                $(`#status-check-${id}`).show().delay(2000).fadeOut();
            },
            error: function () {
                $(`#status-loader-${id}`).hide();
                alert("Failed to update status.");
            }
        });
    }

    // Event delegation for saving notes
    $(document).on('click', '.btn-send-note', function () {
        const id = $(this).data('submission-id') || $(this).data('vendor-id');
        saveNoteForRecord(id);
    });

    // Save note for a submission or vendor
    function saveNoteForRecord(id) {
        const note = $(`#note-input-${id}`).val();
        if (!note) return alert("Please enter a note.");
        $.ajax({
            url: `/api/submissions/${id}/note`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ note }),
            success: function () {
                $(`#note-input-${id}`).val('');
                loadNotes(id);
            },
            error: function () {
                alert("Failed to save note.");
            }
        });
    }

    // Load notes for a submission or vendor
    function loadNotes(id) {
        $.ajax({
            url: `/api/submissions/${id}/notes`,
            method: 'GET',
            success: function (notes) {
                const notesSection = $(`#notes-section-${id}`);
                notesSection.empty();
                notes.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                notes.forEach(note => {
                    const timeAgo = formatTimeAgo(note.timestamp);
                    notesSection.append(`<div><strong>${timeAgo}:</strong> ${note.note}</div>`);
                });
                scrollToBottom(notesSection);
            },
            error: function () {
                alert("Failed to load notes.");
            }
        });
    }

    // "Time ago" formatter function
    function formatTimeAgo(timestamp) {
        const time = moment.utc(timestamp);
        return time.local().fromNow();
    }
});
// Scroll to the bottom of the notes section
function scrollToBottom(element) {
    element.scrollTop(element.prop("scrollHeight"));
}
