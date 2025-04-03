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
        $("#alert-btn").text("Okay").click(() => $("#loginModal").modal("show"));
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
        $("#alert-btn").text("Okay").click(() => $("#loginModal").modal("show"));
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

async function userLogin(event) {
    const jsonData = formDataToJson(event);
    fetchData("/login", jsonData, "/", "loginModal");
}

async function requestBook(event, bookId) {
    event.preventDefault();
    const path = `/request?id=${bookId}`;
    const modal = `confirmBookBorrow-${bookId}`;
    fetchData(path, null, "/loans", modal);
}

async function addBook(event) {
    const jsonData = formDataToJson(event);
    fetchData("/add_book", jsonData, "/library", "addBookModal");
}

function formDataToJson(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const jsonData = JSON.stringify(
        Object.fromEntries(
            formData.entries()
        )
    );
    return jsonData;
}

function closeModalAndShowCustomAlert(type, message, redirect, modalToClose) {
    if (modalToClose) {
        $(`#${modalToClose}`).modal("hide").one("hidden.bs.modal", () => {
            showCustomAlert(type, message, redirect);
        });
    }
}

async function fetchData(path, jsonData = null, redirect = null, modalToClose = null, itemToDisable = null) {
    var options = {
        method: "POST",
    };
    if (jsonData !== null) {
        options.headers = {
            "Content-Type": "application/json"
        };
        options.body = jsonData;
    }
    let itemText;
    if (itemToDisable) {
        itemText = $(itemToDisable).text();
        $(itemToDisable).addClass("disabled").html("<i class='fa fa-spinner fa-spin'></i> Sending...");
    }
    await fetch(path, options).then(res => {
        if (!res.ok) {
            return res.json().then(errorRes => {
                throw new Error(errorRes.error);
            });
        }
        return res.json();
    }).then(data => {
        if (data.success) {
            console.log(`Data: ${data}`);
            if (modalToClose) {
                closeModalAndShowCustomAlert("success", data.success, redirect, modalToClose);
            } else {
                showCustomAlert("success", data.success, redirect);
            }
        }
    }).catch(err => {
        if (modalToClose) {
            closeModalAndShowCustomAlert("error", err.message, redirect, modalToClose);
        } else {
            showCustomAlert("error", err.message);
        }
    }).finally(() => {
        if (itemToDisable) {
            $(itemToDisable).removeClass("disabled").html(itemText);
        }
    });
}

function showCustomAlert(type, message, redirect = null) {
    $("#alertBoxModal").modal("show");
    const alertText = $("#lms-alert-text");
    alertText.removeClass("text-danger text-success");
    if (type == "success") {
        alertText.addClass("text-success");
        alertText.text(`Success: ${message}`);
        $("#alertBoxModal").modal("hide").one("hidden.bs.modal", () => {
            // window.location.href = redirect ? redirect : "/";
            if (redirect) {
                window.location.href = redirect;
            }
        });
    } else {
        alertText.addClass("text-danger");
        alertText.text(`Error: ${message}`);
        $("#alert-btn").text("Okay");
    }
    // if (type === "success") {
    //     $("#alert-btn").text("Okay").off("click").click(() => {
    //         $("#alertBoxModal").modal("hide");
    //         if (redirect) window.location.href = redirect;
    //     });
    // } else {
    //     $("#alert-btn").text("Okay");
    // }
}

async function sendMessage(event) {
    const jsonData = formDataToJson(event);
    fetchData("/send_message", jsonData, "/thank_you", null, event.submitter);
}
