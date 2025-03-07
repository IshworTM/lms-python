console.log("It's alive!")
function viewLoans() {
    fetch("/loans").then(res => {
        if (!res.ok) {
            return res.json().then(data => {
                $("#loginModal").modal("show");
                alert(data.error);
            });
        }
        return res.text();
    }).then(data => {
        if (data) {
            // window.location.href = "/loans";
            $("body").html(data);
        }
    }).catch(err => {
        alert("Error: " + err.message);
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
