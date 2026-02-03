const version = '0.0.1'
const headerStrings = [
    'Image Commander: oldschool hosting',
    'Image Commander: uploading shell']
const welcomeText = '\nWelcome to Image Commander\nType "help" for help\n'

const {createApp} = Vue
createApp({
    data() {
        return {
            footerText: '© iZelikov',
            username: 'root@ic:~#',
            headerText: headerStrings[0],
            toUploadList: [],
            uploadedImages: [],
            showShell: false,
            terminalText: '',
            commandInput: '',
            commandHistory: [],
            historyIndex: -1
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
            this.commandHistory.push(command);
            this.historyIndex = this.commandHistory.length;
            processCommand(command, this).then((text) => {
            });
        }
    },
    mounted() {
        loadRandomMemes().then((memeText) => {
            this.toTerminal(memeText);
        }).then(() => {
            this.toTerminal(welcomeText)
            this.focusInput();
        })
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
}

async function processCommand(command, app) {
    switch (command) {
        case '':
            break;
        case 'clear':
            app.terminalText = '';
            break;
        case 'help':
            await loadTextFile(`./static/txt/help.txt?v=${version}`).then((text) => {
                app.toTerminal(text);
            });
            break;
        case 'exit':
            app.btnExit();
            break;
        case 'shell':
            app.startShell();
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

function focusInput() {

}
