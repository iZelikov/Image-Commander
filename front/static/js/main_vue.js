const version = '0.0.1';
const API_LINKS = {
    "get": "/api/get_images/",
    "upload": "/api/upload/",
    "delete": "/api/delete/",
    "images_path": "/images/"
}
const headerStrings = [
    'Image Commander: oldschool hosting',
    'Image Commander: uploading shell'];
const welcomeText = 'Welcome to Image Commander\nType "help" for help';
const intend = '  ';

const {createApp} = Vue
createApp({
    data() {
        return {
            footerText: '© iZelikov',
            username: 'root@ic:~#',
            headerText: headerStrings[0],
            selectedFiles: [],
            uploadedImages: [],
            showShell: false,
            viewMode: false,
            showModal: false,
            terminalText: '',
            commandInput: '',
            modalContent: {"title": "title", "text": "text"},
            commandHistory: [],
            historyIndex: -1,
            activePanel: null,
            selectedFileIndex: -1,
            uploadedFileIndex: -1,
            isLoadingImages: false,
        }
    },
    methods: {
        toTerminal(text) {
            this.terminalText += text + `\n`;
            scrollTerminal(this);
            this.focusInput();
        },
        focusInput() {
            // Устанавливаем фокус на поле ввода
            this.$refs.commandInput?.focus();
        },
        getHistory(n) {
            let i = this.historyIndex + n;
            if (i >= 0 && i < this.commandHistory.length) {
                this.commandInput = this.commandHistory[i] || '';
                this.historyIndex = i;
            }
        },
        btnHelp() {
            this.modalContent = getHelpContent();
            this.showModal = !this.showModal;
        },
        btnSelect() {
            document.getElementById('fileInput').click();
        },
        btnView() {
            this.viewMode = !this.viewMode;
        },
        btnUpload() {
            uploadFiles(this);
        },
        btnExit() {
            if (this.showShell) {
                this.toTerminal(`Welcome back to terminal mode`)
            }
            this.showShell = false;
            this.headerText = headerStrings[0];
            this.focusInput();
        },
        startShell() {
            this.toTerminal(`Start uploading shell...`);
            setTimeout(() => {
                this.showShell = true;
                this.headerText = headerStrings[1];
                this.toTerminal(`Shell is ready`);
            }, 500)
        },
        executeCommand() {
            const command = this.commandInput.toLowerCase().trim();
            this.commandInput = '';
            this.toTerminal(`> ${command}`);
            if (command) {
                this.commandHistory.push(command);
                this.historyIndex = this.commandHistory.length;
                processCommand(command, this);
            }
        },
        handleFiles(event) {
            const files = event.target.files;
            this.selectedFiles = Array.from(files);
            this.toTerminal('You have selected files:')
            this.selectedFilesInfo.forEach((file, index) => {
                this.toTerminal(`${intend}${file.validation.ok ? '✓' : 'x'} ${file.fullName} (${file.sizeMB} MB) ${file.validation.message}`)
            });
            this.toTerminal('Type "upload" to upload valid images or "select" to select another files')
        },
        selectFile(index, panel) {
            switch (panel) {
                case 'left':
                    this.selectedFileIndex = index;
                    this.activePanel = 'left'
                    break;
                case 'right':
                    this.uploadedFileIndex = index;
                    this.activePanel = 'right';
                    break;
                default:
                    this.activePanel = null;
            }
        },
        deleteSelectedFile() {
            if (this.activePanel === 'left') {
                this.selectedFiles.splice(this.selectedFileIndex, 1);
                if (this.selectedFiles.length === 0) {
                    this.selectedFileIndex = -1;
                } else if (this.selectedFileIndex >= this.selectedFiles.length) {
                    this.selectedFileIndex = this.selectedFiles.length - 1;
                }
            }
            if (this.activePanel === 'right') {
                const index = this.uploadedFileIndex;
                const filename_to_delete = this.uploadedImages[index]['filename'];
                fetch(
                    API_LINKS.delete + filename_to_delete,
                    {method: 'DELETE'}).then(
                    () => loadUploadedImages(this).then(
                        () => console.log(filename_to_delete + ' was removed.')));
            }
        },
        changeFile(shift) {
            switch (this.activePanel) {
                case "left":
                    let i = this.selectedFileIndex + shift;
                    if (i >= 0 && i < this.selectedFilesInfo.length) this.selectedFileIndex = i;
                    break;
                case "right":
                    let j = this.uploadedFileIndex + shift;
                    if (j >= 0 && j < this.uploadedImages.length) this.uploadedFileIndex = j;
                    break;
            }
            this.$nextTick(() => {
                this.scrollToSelected();
            });
        },
        scrollToSelected() {
            if (!this.activePanel) return;
            const selectedElement = document.querySelector(`[data-selected="true"]`);
            if (selectedElement) {
                selectedElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'nearest',
                    inline: 'nearest'
                });
            }
        },
        handleKeyDown(e) {
            if (this.activePanel) {
                switch (e.key) {
                    case 'ArrowUp':
                        e.preventDefault();
                        this.changeFile(-1);
                        break;
                    case 'ArrowDown':
                        e.preventDefault();
                        this.changeFile(+1);
                        break;
                    case 'Tab':
                        e.preventDefault();
                        const tabs = {"left": "right", "right": "left"}
                        this.activePanel = tabs[this.activePanel];
                        break;
                    case 'Delete':
                        e.preventDefault();
                        this.deleteSelectedFile();
                        break;
                    case 'F8':
                        e.preventDefault();
                        this.deleteSelectedFile();
                        break;
                }
            }
            if (this.showShell) {
                switch (e.key) {
                    case 'F1':
                        e.preventDefault();
                        this.btnHelp();
                        break;
                    case 'F2':
                        e.preventDefault();
                        this.btnSelect();
                        break;
                    case 'F3':
                        e.preventDefault();
                        this.btnView();
                        break;
                    case 'F4':
                        this.btnUpload();
                        break;
                    case 'F10':
                        e.preventDefault();
                        this.btnExit();
                        break;
                    case 'Escape':
                        this.activePanel = null;
                        this.selectedFileIndex = -1;
                        this.uploadedFileIndex = -1;
                        break;
                }
            }
        }
    },
    computed: {
        selectedFilesInfo() {
            if (!Array.isArray(this.selectedFiles)) {
                return [];
            }
            return this.selectedFiles.map(file => {
                const MAX_NAME_LENGTH = 12;
                const splitName = file.name.split('.');
                const extension = splitName.pop().toLowerCase();
                const name = splitName.join('');
                const shortName = name.length > MAX_NAME_LENGTH ? `${name.slice(0, MAX_NAME_LENGTH - 2)}~1` : name;
                return {
                    name: name,
                    shortName: shortName,
                    fullName: file.name,
                    ext: extension,
                    sizeMB: (file.size / (1024 * 1024)).toFixed(3),
                    validation: validateFile(file),
                    fileObject: file
                }
            })
        },
        uploadedFilesInfo() {
            if (!Array.isArray(this.uploadedImages)) {
                return [];
            }
            return this.uploadedImages.map(file => {
                const MAX_NAME_LENGTH = 12;
                const splitName = file.original_filename.split('.');
                const extension = splitName.pop().toLowerCase();
                const name = splitName.join('');
                const shortName = name.length > MAX_NAME_LENGTH ? `${name.slice(0, MAX_NAME_LENGTH - 2)}~1` : name;
                const link = API_LINKS.images_path + file.filename;
                return {
                    name: name,
                    shortName: shortName,
                    fullName: file.filename,
                    original_name: file.original_filename,
                    ext: extension,
                    link: link,
                    sizeMB: (file.size / (1024 * 1024)).toFixed(3),

                }
            })
        },
        viewLink() {
            if (this.uploadedFileIndex >= 0) {
                return this.uploadedFilesInfo[this.uploadedFileIndex].link;
            } else return '#';
        },
    },
    mounted() {
        loadRandomMemes().then((memeText) => {
            this.toTerminal(memeText);
        }).then(() => {
            this.toTerminal(welcomeText)
            this.focusInput();
        });
        loadUploadedImages(this).then(() => {
            console.log("Image list loaded")
        });
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }
}).mount('#app')

async function loadRandomMemes() {
    const maxMemes = 23;
    let random_name = Math.floor(Math.random() * maxMemes) + 1;
    return await loadTextFile(`./static/ascii/${random_name}`);
}

async function loadTextFile(fileName) {
    const response = await fetch(fileName);
    if (response.ok) {
        return await response.text()
    }
    throw new Error(`Failed to load file ${fileName}`);
}

function processCommand(command, app) {
    switch (command) {
        case '':
            break;
        case 'clear':
            app.terminalText = '';
            app.historyIndex = -1;
            app.commandHistory = [];
            break;
        case 'help':
            loadTextFile(`./static/txt/help.txt?v=${version}`).then((text) => {
                app.toTerminal(text);
            });
            break;
        case 'exit':
            app.btnExit();
            break;
        case 'shell':
            app.startShell();
            break;
        case 'select':
            app.btnSelect()
            break;
        case 'upload':
            uploadFiles(app);
            break;
        case 'ls':
            app.toTerminal('Uploaded images:')
            app.uploadedFilesInfo.forEach(file => {
                app.toTerminal(intend + file.original_name);
            })
            break;
        case 'rm -rf /':
            app.toTerminal(`Congratulations!\nYou have successfully deleted the entire system.`);
            break;
        default:
            app.toTerminal(`Unknown command: ${command}`);
    }
}

function scrollTerminal(app) {
    const terminalContent = document.querySelector('.terminal-content');
    if (terminalContent) {
        setTimeout(() => {
            terminalContent.scrollTop = terminalContent.scrollHeight;
        }, 100)
    }
}

function validateFile(file) {
    const MAX_SIZE_MB = 5;
    const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;
    const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp'];

    if (!ALLOWED_TYPES.includes(file.type)) {
        const fileExtension = file.name.split(".").pop()?.toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(fileExtension)) {
            return {
                ok: false,
                message: `restricted type: ${fileExtension}`
            };
        }
    }

    if (file.size > MAX_SIZE_BYTES) {
        return {
            ok: false,
            message: `max ${MAX_SIZE_MB} MB`
        };
    }

    return {ok: true, message: ''};
}


function uploadFiles(app) {

    if (app.selectedFilesInfo.length === 0) {
        app.toTerminal('No files to upload. Use "select" command first.');
        return;
    }

    app.toTerminal('Starting upload...');

    const formData = new FormData();
    let flag = false;
    app.selectedFilesInfo.forEach((file, index) => {
        if (file.validation.ok) {
            formData.append('file' + index, file.fileObject);
            flag = true;
        }
    });

    if (!flag) {
        app.toTerminal('No files uploaded');
        app.selectedFiles = [];
        return;
    }


    fetch(API_LINKS.upload, {
        method: 'POST',
        body: formData
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            throw new Error('Upload failed');
        })
        .then(data => {
            app.toTerminal('Upload successful!');
            app.selectedFiles = [];
            loadUploadedImages(app).then(() => {
                console.log("Image list Updated")
            });
        })
        .catch(error => {
            app.toTerminal(`Upload error: ${error.message}`);
        });
}

async function loadUploadedImages(app) {
    app.isLoadingImages = true;

    try {
        console.log('Loading images list from server...');

        const response = await fetch(API_LINKS.get);

        if (!response.ok) {
            console.error(`Failed to load images: ${response.status}`);
        }

        const data = await response.json();

        if (app.uploadedFileIndex >= data.length) {
            app.uploadedFileIndex = data.length === 0 ? -1 : data.length - 1;
        }

        if (Array.isArray(data)) {
            app.uploadedImages = data;
        } else {
            console.error('Invalid response format from server');
        }

        console.log(`Loaded ${app.uploadedImages.length} image(s) from server`);

    } catch (error) {
        console.error(`Error loading images: ${error.message}`);
    } finally {
        app.isLoadingImages = false;
    }
}

function getHelpContent() {

    return {
        "title": "Image Commander Help",
        "text":
            "Usage tips:\n" +
            " - Press Select button and choose one or more pictures.\n" +
            " - Press Upload Button to upload them.\n" +
            " - Use mouse or arrow keys to navigate between images.\n" +
            " - Use F8 (or Del) key or Delete button to delete selected.\n" +
            " - Press View button to enter / exit preview mode.\n" +
            " - Press Esc anytime you want.\n" +
            " - Use Terminal CLI during shell mode if you want.\n" +
            " - Press Exit button to leave shell mode"
    };
}