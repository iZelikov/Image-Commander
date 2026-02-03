const terminal_welcome = 'root@icAdmin:~#'

window.onload = function () {
    const input = document.getElementById("cl-input");
    const clLabel = document.getElementById("cl-label");
    const terminalText = document.getElementById("terminal-text");
    const terminalContent = document.querySelector('.terminal-content');
    input.focus();
    clLabel.textContent = terminal_welcome;
    document.querySelector('.terminal-content').addEventListener('click', function() {
        input.focus();
    });
    welcome(terminalText);
    setTypeCommand(input, terminalText, terminalContent);
}

function setTypeCommand(input, output, scroll) {
    input.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            const command = input.value.trim();
            const newLine = `${terminal_welcome} ${command}\n`;
            output.textContent += newLine;
            executeCommand(command, output);
            scroll.scrollTop = output.scrollHeight;
            input.value = "";
            input.focus();
        }
    });
}

function executeCommand(command, output) {
    switch (command.toLowerCase()) {
        case "help":
            loadTextFile("static/txt/help.txt?v=1.0.0").then((value)=>{
                output.textContent += value;
                output.textContent += "\n";
            });
            break;
        case "upload":
            output.textContent += 'start uploading shell...\n';
            setTimeout(function() {
                window.location.replace("upload.html");
            }, 500);
            break;
        case "rm -rf /":
            output.textContent += 'Congratulation!\nAll your system files successfully deleted\n';
            break;
        case "ic rm -rf /":
            output.textContent += 'Permission denied!\nUse uploading shell\n';
            break;
        default:
            output.textContent += `command "${command}" not found\n`;
    }
}

function welcome(output) {
    loadRandomMemes(output)
    setTimeout(function() {
        output.textContent += '\n';
        output.textContent += 'Welcome to Image Commander\n';
        output.textContent += 'Type "help" for help\n';
    }, 300);
}

async function loadTextFile(filename) {
  try {
    const response = await fetch(filename);

    if (!response.ok) {
      throw new Error(`Ошибка HTTP: ${response.status}`);
    }

    const content = await response.text();
    return content;
  } catch (error) {
    console.error('Ошибка загрузки файла:', error);
    return '\nfile loading error';
  }
}

function loadRandomMemes(output) {
    let max_files = 23
    random_name = Math.floor(Math.random() * max_files) + 1;
    let meme = loadTextFile("static/ascii/"+random_name)
    meme.then((value)=>{
        output.textContent += value;
    });
}
