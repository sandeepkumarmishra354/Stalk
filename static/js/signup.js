var isValidUsername = true;
function validate_form_data() {
    let form = document.forms['signupformid'];
    let pswrd_err = document.getElementById('pswrd_err_element');
    
    if(!form['gender_male'].checked && !form['gender_female'].checked) {
        pswrd_err.innerHTML = "Error: choose your gender";
        return false;
    }

    if(form['pswrd1'].value.length < 6 || form['pswrd2'].value.length < 6) {
        pswrd_err.innerHTML = "password must be 6 digit long";
        return false;
    }
    if(form['pswrd1'].value != form['pswrd2'].value) {
        pswrd_err.innerHTML = "please enter same password in both fields";
        return false;
    }
    if(form['pswrd1'].value.includes(' ') || form['pswrd2'].value.includes(' ')) {
        pswrd_err.innerHTML = "Error: password contains blank space";
        return false;
    }
    if(form['username'].value.includes(' ')) {
        pswrd_err.innerHTML = "Error: username contains blank space";
        return false;
    }
    if(!isValidUsername) {
        pswrd_err.innerHTML = "Error: username is already in use";
        return false;
    }
    
    if(form['gender_male'].checked)
        form['gender'].value = "male";
    if(form['gender_female'].checked)
        form['gender'].value = "female";

    username_err.style.display = "none";
    console.log(form['gender'].value)
    pswrd_err.innerHTML = "";
    return true;
}

function checkUsernameAvail(username) {
    let username_err = document.getElementById('usernameerror')
    if(username != "") {
        let xhttp = new XMLHttpRequest();
        xhttp.onreadystatechange = ()=> {
            if(xhttp.readyState == 4 && xhttp.status == 200) {
                let res_text = xhttp.responseText;
                username_err.style.display = "block";
                if(res_text == "AVAIL") {
                    username_err.innerHTML = "Available";
                    username_err.style.color = "green";
                    isValidUsername = true;
                }
                if(res_text == "NOT AVAIL") {
                    username_err.innerHTML = "Already exists";
                    username_err.style.color = "red";
                    isValidUsername = false;
                }
            }
        }
        xhttp.open("POST","/check_username",true);
        xhttp.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        xhttp.send("username="+username);
    }
    else {
        username_err.innerHTML = "";
        username_err.style.display = "none";
    }
}