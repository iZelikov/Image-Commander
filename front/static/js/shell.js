const filesToUpload = ['1.jpg', '2.jpg']
const uploadedFiles = getUploadedFiles()

setUploadDropArea();
setFilesToUploadList();
setUploadedFilesList();


function setUploadDropArea(dropArea) {
    dropArea = document.getElementById("upload-panel");
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault()
        dropArea.classList.add('dragover')
    });
    dropArea.addEventListener('dragleave', (e) => {
        e.preventDefault()
        dropArea.classList.remove('dragover')
    });
    dropArea.addEventListener('drop', (e) => {
        e.preventDefault()
        dropArea.classList.remove('dragover')
    });
}

function setFilesToUploadList() {}

function setUploadedFilesList() {}

function getUploadedFiles() {
    return JSON.parse(localStorage.getItem('uploadedFiles')) || ['3.jpg', '4.jpg']
}