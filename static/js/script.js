console.log("It's alive!")
function viewLoans() {
    fetch("/loans").then(res => {
        if (!res.ok) {
            return res.json().then(err => {
                throw new Error(err.error);
            });
        }
        window.location.href = "/loans";
    }).catch(error => {
        $("#alertBoxModal").modal("show");
        const alertText = $("#lms-alert-text")
        alertText.addClass("text-danger");
        alertText.text(`Sorry, ${error.message}`);
        $("#alert-btn").text("Log In").click(() => $("#loginModal").modal("show"));
    });
}

function viewReturns() {
    fetch("/returns").then(res => {
        if (!res.ok) {
            return res.json().then(err => {
                throw new Error(err.error);
            });
        }
        window.location.href = "/returns";
    }).catch(error => {
        $("#alertBoxModal").modal("show");
        const alertText = $("#lms-alert-text")
        alertText.addClass("text-danger");
        alertText.text(`Sorry, ${error.message}`);
        $("#alert-btn").text("Log In").click(() => $("#loginModal").modal("show"));
    });
}

function showPw(e) {
    var current = e.currentTarget;
    var icon = current.querySelector("#icon");
    var pw = current.previousElementSibling;
    if (pw.type === "password") {
        pw.type = "text";
        icon.classList.replace("fa-eye-slash", "fa-eye");
    } else {
        pw.type = "password";
        icon.classList.replace("fa-eye", "fa-eye-slash");
    }
}

function userLogin(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const jsonData = JSON.stringify(
        Object.fromEntries(
            formData.entries()
        )
    );
    fetchData("/login", jsonData);
}

function requestBook(event) {
    event.preventDefault();
    const currentTarget = event.target;
    const formData = new FormData(currentTarget);
    const jsonData = JSON.stringify(
        Object.fromEntries(
            formData.entries()
        )
    );
    debugger;
    fetchData("/request", jsonData);
}

function fetchData(path, jsonData) {
    fetch(path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: jsonData
    }).then(res => {
        if (!res.ok) {
            return res.json().then(errorRes => {
                throw new Error(errorRes.error);
            });
        }
        return res.json();
    }).then(data => {
        if (data.success) {
            $("#loginModal").modal("hide");
            $("#alertBoxModal").modal("show");
            const alertText = $("#lms-alert-text")
            alertText.addClass("text-success");
            alertText.text(`Success: ${data.success}`);
            $("#alert-btn").text("Okay").click(() => window.location.href = "/");
        }
    }).catch(err => {
        $("#loginModal").modal("hide");
        $("#alertBoxModal").modal("show");
        const alertText = $("#lms-alert-text")
        alertText.addClass("text-danger");
        alertText.text(`Error: ${err.message}`);
        $("#alert-btn").text("Okay");
    });
}