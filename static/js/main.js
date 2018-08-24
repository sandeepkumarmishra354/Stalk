function checkdata() {
    let err_element = document.getElementById('err_element');
    let form = document.forms['loginformid'];
    let pswrd = form['password'].value;
    let usrnm = form['username'].value;

    if(pswrd.length < 6) {
        err_element.innerHTML = "password must be 6 digit long";
        return false;
    }
    if(pswrd.includes(' ')) {
        err_element.innerHTML = "Error: password with blank space";
        return false;
    }
    if(usrnm.includes(' ')) {
        err_element.innerHTML = "Error: username with blank space";
        return false;
    }

    return true;
}
