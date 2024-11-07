let fileUploadCount = 1;

function addFileUpload() {
    fileUploadCount++;
    const fileUploadContainer = document.getElementById('file-upload-container');

    const newFileUploadDiv = document.createElement('div');
    newFileUploadDiv.className = 'file-upload';

    const newLabel = document.createElement('label');
    newLabel.setAttribute('for', `files${fileUploadCount}`);
    newLabel.textContent = 'Select Files';
    newFileUploadDiv.appendChild(newLabel);

    const newInput = document.createElement('input');
    newInput.type = 'file';
    newInput.id = `files${fileUploadCount}`;
    newInput.name = 'files';
    newInput.multiple = true;
    newFileUploadDiv.appendChild(newInput);

    const newFileList = document.createElement('ul');
    newFileList.className = 'file-list';
    newFileList.id = `file-list${fileUploadCount}`;
    newFileUploadDiv.appendChild(newFileList);

    fileUploadContainer.appendChild(newFileUploadDiv);

    newInput.addEventListener('change', function () {
        const fileList = document.getElementById(`file-list${fileUploadCount}`);
        fileList.innerHTML = '';
        for (const file of newInput.files) {
            const listItem = document.createElement('li');
            listItem.textContent = file.name;
            fileList.appendChild(listItem);
        }
    });
}

document.getElementById('files1').addEventListener('change', function () {
    const fileList = document.getElementById('file-list1');
    fileList.innerHTML = '';
    for (const file of this.files) {
        const listItem = document.createElement('li');
        listItem.textContent = file.name;
        fileList.appendChild(listItem);
    }
});

let signaturePad = new SignaturePad(document.getElementById('signature-pad'), {
    minWidth: 1,
    maxWidth: 3,
    penColor: "black",
    velocityFilterWeight: 0.7
});
let signatureInput = document.getElementById('signature-input');
let clearButton = document.getElementById('clear-signature');

clearButton.addEventListener('click', function () {
    signaturePad.clear();
    signatureInput.value = '';
});

// Prevent double submission
let isSubmitting = false;

// Handle form submission
document.querySelector('form').addEventListener('submit', function (e) {
    if (isSubmitting) {
        e.preventDefault();
        return false;
    }

    if (!signaturePad.isEmpty()) {
        signatureInput.value = signaturePad.toDataURL();
    } else {
        alert('Please provide a signature.');
        e.preventDefault();
        return false;
    }

    isSubmitting = true;  // Set submitting flag to prevent multiple submissions
});

// Function to format SSN and EIN fields in real-time
function formatInput(field, pattern) {
    field.addEventListener('input', function () {
        let value = field.value.replace(/\D/g, ''); // Remove non-numeric characters
        let formattedValue = '';

        for (let i = 0, j = 0; i < pattern.length && j < value.length; i++) {
            if (pattern[i] === '-') {
                formattedValue += '-';
            } else {
                formattedValue += value[j++];
            }
        }

        field.value = formattedValue;
    });
}

// Function to format percentage fields in real-time
function formatPercentage(field) {
    field.addEventListener('input', function () {
        let value = field.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
        if (value) {
            field.value = `${value}%`;
        }
    });
}

// Function to format currency fields in real-time
function formatCurrency(field) {
    field.addEventListener('input', function () {
        let value = field.value.replace(/[^0-9]/g, ''); // Remove non-numeric characters
        if (value) {
            field.value = '$' + parseInt(value).toLocaleString();
        }
    });
}

// Applying formatting to SSN and EIN fields for borrower and co-applicant
const borrowerSSN = document.getElementById('borrower-ssn');
const borrowerEIN = document.getElementById('borrower-ein');
const coApplicantSSN = document.getElementById('coapplicant-ssn');
const coApplicantEIN = document.getElementById('coapplicant-ein');

// Ensure elements exist before applying formatting to avoid errors
if (borrowerSSN) formatInput(borrowerSSN, '###-##-####'); // SSN pattern
if (borrowerEIN) formatInput(borrowerEIN, '##-#######');   // EIN pattern
if (coApplicantSSN) formatInput(coApplicantSSN, '###-##-####'); // SSN pattern
if (coApplicantEIN) formatInput(coApplicantEIN, '##-#######');   // EIN pattern

// Applying formatting for percentage ownership and currency fields
const borrowerOwnership = document.getElementById('borrower-ownership');
const coApplicantOwnership = document.getElementById('coapplicant-ownership');
const borrowerEquipmentAmount = document.getElementById('borrower-equipment-amount');
const borrowerDownPayment = document.getElementById('borrower-down-payment');
const coApplicantEquipmentAmount = document.getElementById('coapplicant-equipment-amount');
const coApplicantDownPayment = document.getElementById('coapplicant-down-payment');

// Apply percentage formatting
if (borrowerOwnership) formatPercentage(borrowerOwnership);
if (coApplicantOwnership) formatPercentage(coApplicantOwnership);

// Apply currency formatting
if (borrowerEquipmentAmount) formatCurrency(borrowerEquipmentAmount);
if (borrowerDownPayment) formatCurrency(borrowerDownPayment);
if (coApplicantEquipmentAmount) formatCurrency(coApplicantEquipmentAmount);
if (coApplicantDownPayment) formatCurrency(coApplicantDownPayment);
