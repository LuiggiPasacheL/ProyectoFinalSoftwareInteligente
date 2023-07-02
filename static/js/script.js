const defaultUser = "hola";
const defaultPassword = "hola";

function addListener() {
    let button = document.getElementById("form-button");
    button.addEventListener("click", function () {
        let username = document.getElementById("form-username").value;
        let password = document.getElementById("form-password").value;

        if (username === "") {
            alert("Por favor ingrese su usuario");
        }

        if (password === "") {
            alert("Por favor ingrese su contraseña");
        }

        if (username === defaultUser && password === defaultPassword) {
            alert("Usuario y contraseña correctos");
            window.location.href = "home";
        } else {
            alert("Usuario y/o contraseña incorrectos");
        }
    });
}

function fillUser() {
    let title = document.getElementById("welcome-title");

    title.innerHTML += `${defaultUser}!`;

    console.log(defaultUser)
}

try {
    addListener();
} catch (error) {}

try {
    fillUser()
} catch (error) {}