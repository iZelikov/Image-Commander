const version = '0.0.1';
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
            terminalText: '',
            commandInput: '',
            commandHistory: [],
            historyIndex: -1,
            activePanel: null,
            selectedFileIndex: -1,
            uploadedFileIndex: -1,
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
        btnSelect() {
            document.getElementById('fileInput').click();
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
                e.preventDefault();
                switch (e.key) {
                    case 'ArrowUp':
                        this.changeFile(-1);
                        break;
                    case 'ArrowDown':
                        this.changeFile(+1);
                        break;
                    case 'Tab':
                        const tabs = {"left": "right", "right": "left"}
                        this.activePanel = tabs[this.activePanel];
                        break;
                    case 'Delete':
                        this.deleteSelectedFile();
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
    },
    mounted() {
        loadRandomMemes().then((memeText) => {
            this.toTerminal(memeText);
        }).then(() => {
            this.toTerminal(welcomeText)
            this.focusInput();
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
            app.toTerminal(`Uploaded images:\n${intend}` + app.uploadedImages.join(`\n${intend}`));
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
    // заглушка
    app.selectedFilesInfo.forEach(file => {
        if (file.validation.ok) {
            app.uploadedImages.push(file);
        }
    })
    app.selectedFiles = [];
    // заглушка


    if (app.selectedFilesInfo.length === 0) {
        app.toTerminal('No files to upload. Use "select" command first.');
        return;
    }

    app.toTerminal('Starting upload...');

    const formData = new FormData();

    app.selectedFiles.forEach((file, index) => {
        formData.append('file' + index, file);
    });

    fetch('/api/upload/', {
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
        })
        .catch(error => {
            app.toTerminal(`Upload error: ${error.message}`);
        });
}