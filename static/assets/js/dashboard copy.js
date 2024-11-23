// Import necessary w2ui modules
import { w2layout, w2sidebar, w2popup, w2utils, w2field, query } from 'https://rawgit.com/vitmalina/w2ui/master/dist/w2ui.es6.min.js';

$(document).ready(function () {
    // Initialize layout only if not already registered
    if (!w2ui['layout']) {
        $('#main-layout').w2layout({
            name: 'layout',
            panels: [
                { type: 'top', size: 50, resizable: false, style: 'padding: 5px;' },
                { type: 'left', size: 200, resizable: false, style: 'border-right: 1px solid #ddd;' },
                { type: 'main', style: 'padding: 15px;' }
            ]
        });
    }

    // Once layout is rendered, set the top panel content
    if (w2ui['layout']) {
        w2ui['layout'].content('top', `
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <h3 style="margin: 0; font-size: 1.2em;">ZapBot🔥</h3>
                <div class="settings-container">
                    <i class="fas fa-cog settings-icon" id="settingsIcon"></i>
                    <div id="themeToggle" class="theme-toggle" style="display: none;">
                        <button id="darkModeBtn" class="btn btn-dark">🌙 Dark Mode</button>
                        <button id="lightModeBtn" class="btn btn-light">☀️ Light Mode</button>
                    </div>
                </div>
            </div>
        `);
    }

    // Initialize the sidebar only if not already registered
    if (!w2ui['sidebar']) {
        $().w2sidebar({
            name: 'sidebar',
            nodes: [{
                id: 'menu',
                text: 'Menu',
                group: true,
                expanded: true,
                nodes: [
                    { id: 'submissions', text: 'Submissions', icon: 'fa fa-university' },
                    { id: 'vendors', text: 'Vendors', icon: 'fa fa-briefcase' }
                ]
            }],
            onClick: function (event) {
                if (event.target === 'submissions') {
                    w2ui.layout.html('main', '<div id="submissionsTableWrapper" style="width: 100%; height: 100%;"></div>');
                    loadSubmissionsGrid();
                } else if (event.target === 'vendors') {
                    w2ui.layout.html('main', '<div id="vendorsTableWrapper" style="width: 100%; height: 100%;"></div>');
                    loadVendorsGrid();
                }
            }
        });
    }

    // Render sidebar in the left panel
    if (w2ui['layout']) {
        w2ui['layout'].content('left', w2ui['sidebar']);
    }

    // Theme toggle logic
    $('#settingsIcon').on('click', function () {
        $('#themeToggle').toggle();
    });

    $('#darkModeBtn').on('click', function () {
        $('body').css('background-color', '#2e2e2e');
        $('#main-layout').css('color', '#ffffff');
    });

    $('#lightModeBtn').on('click', function () {
        $('body').css('background-color', '#ffffff');
        $('#main-layout').css('color', '#000000');
    });

    // Load W2UI grid for submissions
    function loadSubmissionsGrid() {
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
                        return `<button class="btn btn-view-details" data-recid="${record.recid}">View Details</button>`;
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
                        return `<button class="btn btn-view-vendor" data-recid="${record.recid}">View Vendor</button>`;
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
        $.ajax({
            url: '/api/submissions',
            method: 'GET',
            success: function (data) {
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
            error: function () {
                alert('Failed to load submissions.');
            }
        });
    }

    // Load vendors data from the server
    function loadVendorsData() {
        $.ajax({
            url: '/api/vendors',
            method: 'GET',
            success: function (data) {
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
            error: function () {
                alert('Failed to load vendors.');
            }
        });
    }

    // View submission details in a popup
    function viewSubmissionDetails(record) {
        const detailsHtml = `
            <div style="padding: 10px;">
                <p><strong>Application ID:</strong> ${record.app_id || 'N/A'}</p>
                <p><strong>Company Name:</strong> ${record.company_name || 'N/A'}</p>
                <p><strong>Time in Business:</strong> ${record.time_in_business || 'N/A'}</p>
                <p><strong>Address:</strong> ${record.address_line_1 || ''}, ${record.city || ''}, ${record.state || ''} ${record.zip_code || ''}</p>
                <p><strong>Company Email:</strong> ${record.company_email || 'N/A'}</p>
                <p><strong>Company Phone:</strong> ${record.company_phone || 'N/A'}</p>
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
            <div style="padding: 10px;">
                <p><strong>Business Name:</strong> ${record.business_name || 'N/A'}</p>
                <p><strong>Contact Name:</strong> ${record.contact_name || 'N/A'}</p>
                <p><strong>Contact Email:</strong> ${record.contact_email || 'N/A'}</p>
            </div>`;
        w2popup.open({
            title: record.business_name,
            body: detailsHtml,
            width: 800,
            height: 400,
            modal: false,
            showClose: true,
            showMax: true,
        });
    }
});
