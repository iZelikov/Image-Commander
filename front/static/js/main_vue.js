const version = '0.1.1';
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
const maxRequestSizeMB = 50;

const {createApp} = Vue
createApp({
    data() {
        return {
            animationSpeed: getCookie('animationSpeed') || 1,
            footerText: '© iZelikov',
            username: 'root@ic:~#',
            headerText: headerStrings[0],
            selectedFiles: [],
            uploadedImages: [],
            showShell: getCookie('showShell') === 'true' || false,
            viewMode: getCookie('viewMode') === 'true' || false,
            showModal: false,
            terminalText: '',
            commandInput: '',
            modalContent: {"title": "title", "text": "text"},
            commandHistory: [],
            historyIndex: -1,
            activePanel: null,
            selectedFileIndex: -1,
            uploadedFileIndex: -1,
            currentPage: 1,
            pageSize: 20,
            totalImages: 0,
            isLoadingImages: false,
            isUploadProcess: false,
            isDragOver: false,
            isPreloading: true,
            isLoading: true,
            loaderMessages: [],
            loaderProgress: 0,
            currentLoaderStep: 0,
            totalLoaderSteps: 7,
            resizeTimeout: null,
        }
    },
    methods: {
        toTerminal(text) {
            this.terminalText += text + `\n`;
            scrollTerminal();
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
        setMaxImagesPerPage() {
            const panel = document.getElementById('storage-panel');
            if (!panel || panel.clientHeight === 0) {
                this.pageSize = 20;
                return;
            }
            const table_row = document.querySelector('#storage-panel tr')

            // первые две строки таблицы включают толщину границы заголовка 1px
            const height = panel.clientHeight - 5; // минус толщина границы и пара пикселей в запас
            const row_height = (!table_row)? 34: table_row.clientHeight - 1; // row - первая строка выше на 1 пиксель
            // получаем число изображений на страницу для пагинации
            const calculatedSize = Math.floor((height) / row_height) - 2; // пропускаем две строки заголовков

            // Ограничиваем минимальный размер 5 и максимальный 50
            this.pageSize = Math.max(5, Math.min(calculatedSize, 50));

            // Дополнительная защита от некорректных значений
            if (this.pageSize <= 0 || isNaN(this.pageSize)) {
                this.pageSize = 20;
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
                this.$nextTick(() => {
                    this.setMaxImagesPerPage();
                    loadUploadedImages(this).then(() => {
                        this.toTerminal(`Shell is ready`);
                    });
                });
            }, 500)
        },
        executeCommand() {
            const command = this.commandInput.toLowerCase().trim();
            this.commandInput = '';
            this.toTerminal(`>>> ${command}`);
            if (command) {
                this.commandHistory.push(command);
                this.historyIndex = this.commandHistory.length;
                processCommand(command, this);
            }
        },
        ls() {
            this.toTerminal('Uploaded images:')
            this.uploadedFilesInfo.forEach((file, index) => {
                this.toTerminal(`${intend}${index}: ${file.original_name}`);
            })
        },
        nextPage(n) {
            const page = this.currentPage + n;
            if (page >= 1 && page <= this.maxPages) {
                this.currentPage = page;
                if (!this.showShell) {
                    this.toTerminal('Updating images list...');
                }
                loadUploadedImages(this).then(() => {
                    if (!this.showShell) {
                        this.ls();
                    }
                });
            }
        },
        handleSelectedFiles(event) {
            const files = event.target.files;
            const fileArray = Array.from(files);
            this.addSelectedFiles(fileArray);
        },
        addSelectedFiles(fileArray) {
            if (fileArray.length === 0) return;
            this.selectedFiles = fileArray;
            this.toTerminal('You have selected files:');
            this.selectedFilesInfo.forEach(file => {
                this.toTerminal(`${intend}${file.validation.ok ? '✓' : 'x'} ${file.fullName} (${file.sizeMB} MB) ${file.validation.message}`);
            });
            this.toTerminal(`Total selected ${this.selectedFilesSize}MB of valid images`);
            if (this.selectedFilesSize > maxRequestSizeMB) {
                this.toTerminal(`Upload blocked! Max - ${maxRequestSizeMB}MB`);
                this.toTerminal('Select files again');
            } else {
                this.toTerminal('Type "upload" to upload valid images or "select" to select another files');
            }
        },
        clearSelectedFiles() {
            this.selectedFileIndex = -1;
            this.selectedFiles = [];
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
                    console.warn('selectedFile(): Unknown Panel');
            }
        },
        deleteSelectedFile() {
            if (this.disableDelete) {
                return;
            }
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
                this.deleteByIndex(index);
            }
        },
        deleteByIndex(index) {
            const filename = this.uploadedImages[index]['filename'];
            const originalName = this.uploadedImages[index]["original_filename"]
            fetch(
                API_LINKS.delete + filename,
                {method: 'DELETE'}).then(
                () => loadUploadedImages(this).then(
                    () => {
                        this.toTerminal(`Image "${originalName}" deleted`);
                        this.toTerminal('Updating images list...');
                        this.ls();
                    }
                ));
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
                    case 'ArrowRight':
                        if (this.activePanel === 'right') {
                            e.preventDefault();
                            this.nextPage(+1);
                        }
                        break;
                    case 'ArrowLeft':
                        if (this.activePanel === 'right') {
                            e.preventDefault();
                            this.nextPage(-1);
                        }
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
                        this.showModal = false;
                        break;
                }
            }
        },
        handleWindowResize() {
            if (this.resizeTimeout) {
                clearTimeout(this.resizeTimeout);
            }
            this.resizeTimeout = setTimeout(() => {
                if (this.showShell) {
                    this.recalculatePagination();
                    // Загружаем изображения только если страница изменилась
                    loadUploadedImages(this).then(() => {
                        // После загрузки проверяем, что индекс валидный
                        if (this.uploadedFileIndex >= this.uploadedFilesInfo.length) {
                            this.uploadedFileIndex = this.uploadedFilesInfo.length > 0 ? this.uploadedFilesInfo.length - 1 : -1;
                        }
                    });
                }
            }, 500);
        },
        recalculatePagination() {
            // Сохраняем текущий глобальный индекс выделенного файла
            let globalIndex = -1;
            if (this.uploadedFileIndex >= 0) {
                globalIndex = ((this.currentPage - 1) * this.pageSize) + this.uploadedFileIndex;
            }

            // Пересчитываем размер страницы
            this.setMaxImagesPerPage();

            // Если был выделенный файл, вычисляем новую страницу и локальный индекс
            if (globalIndex >= 0 && globalIndex < this.totalImages) {
                // Вычисляем новую страницу
                const newPage = Math.floor(globalIndex / this.pageSize) + 1;

                // Если страница изменилась, обновляем текущую страницу
                if (newPage !== this.currentPage) {
                    this.currentPage = newPage;
                }

                // Вычисляем новый локальный индекс
                this.uploadedFileIndex = globalIndex % this.pageSize;
            } else if (globalIndex >= this.totalImages) {
                // Если глобальный индекс больше общего количества файлов, сбрасываем выделение
                this.uploadedFileIndex = -1;
            }

            // Логирование для отладки

        },
        handleDragOver(e) {
            e.preventDefault();
            this.isDragOver = true;
            e.dataTransfer.dropEffect = 'copy';
        },
        handleDragLeave(e) {
            e.preventDefault();
            this.isDragOver = false;
        },
        handleDrop(e) {
            e.preventDefault();
            this.isDragOver = false;
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.addSelectedFiles(Array.from(files));
            }
        },
        getSelectedFileUrl() {
            if (this.selectedFileIndex >= 0 && this.selectedFiles[this.selectedFileIndex]) {
                return URL.createObjectURL(this.selectedFiles[this.selectedFileIndex]);
            }
            return '';
        },
        async initLoaderAnimation() {
            // Массив шагов загрузки с сообщениями
            const steps = [
                {message: `Starting Image Commander v${version}...`, type: 'system', delay: 100 / this.animationSpeed},
                {message: 'Initializing terminal interface...', type: 'system', delay: 150 / this.animationSpeed},
                {message: '✓ Terminal interface ready', type: 'success', delay: 100 / this.animationSpeed},
                {message: 'Loading file system driver...', type: 'system', delay: 150 / this.animationSpeed},
                {message: '✓ File system ready', type: 'success', delay: 100 / this.animationSpeed},
                {message: 'Connecting to image storage...', type: 'system', delay: 200 / this.animationSpeed},
                {message: '✓ Connection established', type: 'success', delay: 100 / this.animationSpeed},
                {message: 'Loading system configuration...', type: 'system', delay: 150 / this.animationSpeed},
                {message: '✓ Configuration loaded', type: 'success', delay: 100 / this.animationSpeed},
                {message: 'Initializing command processor...', type: 'system', delay: 150 / this.animationSpeed},
                {message: '✓ Command processor ready', type: 'success', delay: 100 / this.animationSpeed},
                {message: 'Booting complete!', type: 'info', delay: 200 / this.animationSpeed},
            ];

            // Добавляем сообщения по одному
            for (let i = 0; i < steps.length; i++) {
                const step = steps[i];

                // Добавляем сообщение
                this.loaderMessages.push({
                    text: step.message,
                    type: step.type
                });

                // Обновляем прогресс
                this.loaderProgress = Math.round((i + 1) / steps.length * 100);
                this.currentLoaderStep = i + 1;

                // Ждем перед следующим сообщением
                await this.sleep(step.delay);
            }

            // Короткая пауза в конце
            await this.sleep(300 / this.animationSpeed);

            // Завершаем загрузку
            this.isLoading = false;
            // в следующий раз загрузимся в 5 раз быстрее
            setCookie('animationSpeed', 5)

            // Устанавливаем фокус на поле ввода
            this.$nextTick(() => {
                this.focusInput();
            });
        },
        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        },
    },
    computed: {
        maxPages() {
            return Math.ceil(this.totalImages / this.pageSize);
        },
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
                const fullDate = new Date(file.lastModified);
                const createdAt = formatDate(fullDate);
                return {
                    name: name,
                    shortName: shortName,
                    fullName: file.name,
                    ext: extension,
                    sizeMB: (file.size / (1024 * 1024)).toFixed(3),
                    createdAt: createdAt,
                    validation: validateFile(file),
                    fileObject: file
                }
            })
        },
        selectedFilesSize() {
            let totalSize = 0;
            this.selectedFilesInfo.forEach(file => {
                if (file.validation.ok) totalSize += parseFloat(file.sizeMB);
            });
            return totalSize.toFixed(3);
        },
        uploadedFilesInfo() {
            if (!Array.isArray(this.uploadedImages)) {
                return [];
            }
            return this.uploadedImages.map(file => {
                const MAX_NAME_LENGTH = 12;
                const splitName = file['original_filename'].split('.');
                const extension = splitName.pop().toLowerCase();
                const name = splitName.join('');
                const shortName = name.length > MAX_NAME_LENGTH ? `${name.slice(0, MAX_NAME_LENGTH - 2)}~1` : name;
                const link = file['link'];
                const preview = file['preview'];
                const fullDate = new Date(file['upload_time']);
                const uploadedAt = formatDate(fullDate);
                return {
                    name: name,
                    shortName: shortName,
                    fullName: file['filename'],
                    original_name: file['original_filename'],
                    ext: extension,
                    link: link,
                    preview: preview,
                    sizeMB: (file.size / (1024 * 1024)).toFixed(3),
                    uploadedAt: uploadedAt,
                }
            })
        },
        currentView() {
            let result = {'link': '#', 'name': '', 'preview': '#'};
            if (this.activePanel === 'right') {
                if (this.uploadedFileIndex >= 0 &&
                    this.uploadedFileIndex < this.uploadedFilesInfo.length &&
                    this.uploadedFilesInfo[this.uploadedFileIndex]) {
                    const view = this.uploadedFilesInfo[this.uploadedFileIndex];
                    result = {'link': view.link, 'name': view.original_name, 'preview': view.preview};
                }
            } else if (this.activePanel === 'left') {
                if (this.selectedFileIndex >= 0) {
                    const link = this.getSelectedFileUrl();
                    const name = this.selectedFilesInfo[this.selectedFileIndex].fullName;
                    result = {'link': link, 'name': name, 'preview': link};
                }
            }
            return result;
        },
        disableUpload() {
            return this.isUploadProcess ||
                this.selectedFiles.length === 0 ||
                this.selectedFilesSize > maxRequestSizeMB;
        },
        disableDelete() {
            const leftDel = this.activePanel === 'left' && this.selectedFileIndex >= 0;
            const rightDel = this.activePanel === 'right' && this.uploadedFileIndex >= 0;
            return !leftDel && !rightDel || this.isUploadProcess;
        },
    },
    watch: {
        showShell(newVal) {
            setCookie('showShell', newVal);
        },
        viewMode(newVal) {
            setCookie('viewMode', newVal);
        },
        uploadedFilesInfo(newVal) {
            if (newVal.length === 0 && this.currentPage > 1) {
                this.uploadedFileIndex = this.pageSize - 1;
                this.nextPage(-1);
            }
        },
    },
    mounted() {
        this.isPreloading = false;
        this.initLoaderAnimation().then(() => {
            return Promise.all([
                loadRandomMemes().then((memeText) => {
                    this.toTerminal(memeText);
                }),
                loadUploadedImages(this)
            ]);
        }).then(() => {
            this.toTerminal(welcomeText);
            if (this.showShell) {
                this.$nextTick(() => {
                    setTimeout(() => {
                        this.setMaxImagesPerPage();
                        loadUploadedImages(this).then();
                    }, 100);
                });
            }
        }).catch(error => {
            console.error("Ошибка загрузки:", error);
            this.loaderMessages.push({
                text: `ERROR: ${error.message}`,
                type: 'error'
            });
            this.toTerminal("Error loading application");
            setTimeout(() => {
                this.isLoading = false;
            }, 2000);
        });
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        window.addEventListener('resize', this.handleWindowResize.bind(this));
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.handleWindowResize);
        document.removeEventListener('keydown', this.handleKeyDown);
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

function processCommand(commandString, app) {
    const parts = commandString.toLowerCase().trim().split(/\s+/g);
    const command = parts[0] || '';
    const args = parts.slice(1);
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
        case 'del':
            if (args[0].match(/^\d+$/)) {
                let index = parseInt(args[0])
                if (index >= 0 && index < app.uploadedImages.length) {
                    app.deleteByIndex(index);
                } else {
                    app.toTerminal('Index out of range! Please enter an existing image index.\nUse \'ls\' command.');
                }
            } else {
                app.toTerminal(`Invalid argument '${args[0]}'! Expected valid index number after del keyword`)
            }
            break;
        case 'ls':
            app.ls();
            break;
        case 'next':
            if (app.currentPage === app.maxPages) {
                app.toTerminal("No more images on server");
                app.toTerminal('Use "prev" command to step backwards');
            } else {
                app.nextPage(1);
            }
            break;
        case 'prev':
            if (app.currentPage === 1) {
                app.toTerminal("No more images on server");
                app.toTerminal('Use "next" command to step forward');
            } else {
                app.nextPage(-1);
            }
            break;
        case 'rm':
            if (parts.join(' ') === 'rm -rf /') {
                app.toTerminal(`Congratulations!\nYou have successfully deleted the entire system.`);
            } else {
                app.toTerminal('Wrong syntax of rm command!')
                app.toTerminal('Type "rm -rf /" to remove all your files');
            }
            break;
        default:
            app.toTerminal(`Unknown command: ${command}`);
    }
}

function scrollTerminal() {
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

    if (app.selectedFilesSize > maxRequestSizeMB) {
        app.toTerminal(`Upload blocked! Maximum - ${maxRequestSizeMB}MB`);
        app.toTerminal('Select files again');
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
        app.clearSelectedFiles();
        return;
    }

    app.isUploadProcess = true;
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
        .then(() => {
            app.isUploadProcess = false;
            app.toTerminal('Upload successful!');
            app.clearSelectedFiles();
            loadUploadedImages(app).then();
        })
        .catch(error => {
            app.toTerminal(`Upload error: ${error.message}`);
        }).finally(() => {
        app.isUploadProcess = false;
    });
}

async function loadUploadedImages(app) {
    app.isLoadingImages = true;

    // Защита от некорректных значений page и size
    const page = Math.max(1, app.currentPage); // Не меньше 1
    const size = Math.max(1, app.pageSize); // Не меньше 1

    try {
        const link = `${API_LINKS.get}?page=${page}&size=${size}`
        const response = await fetch(link);

        if (!response.ok) {
            console.error(`Failed to load images: ${response.status}`);
        }

        const responseJson = await response.json();
        const data = responseJson['files'];
        const total = responseJson['total'];

        if (app.uploadedFileIndex >= data.length) {
            app.uploadedFileIndex = data.length === 0 ? -1 : data.length - 1;
        }

        if (Array.isArray(data)) {
            app.uploadedImages = data;
            app.totalImages = total;
        } else {
            console.error('Invalid response format from server');
        }

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
            " - Press Select button and choose one or more pictures\n" +
            " - Press Upload Button to upload them\n" +
            " - Use mouse or arrow keys to navigate between images\n" +
            " - Use F8 (or Del) key or Delete button to delete selected\n" +
            " - Press View button to enter / exit preview mode\n" +
            " - Press Esc anytime you want\n" +
            " - Use Terminal CLI during shell mode if you want\n" +
            " - Press Exit button to leave GUI-shell mode"
    };
}

function setCookie(name, value, days = 7) {
    let expires = "";
    if (days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function formatDate(date) {
    const sep = '/';

    let dd = date.getDate();
    if (dd < 10) dd = '0' + dd;

    let mm = date.getMonth() + 1;
    if (mm < 10) mm = '0' + mm;

    let yyyy = date.getFullYear();

    return dd + sep + mm + sep + yyyy;
}