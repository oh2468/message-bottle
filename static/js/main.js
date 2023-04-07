
function constructFetchJsonPost(data) {
  return {
    method: "post",
    body: JSON.stringify(data),
    headers: {
      'Content-Type': 'application/json'
    },
  }
}


function handleDecryptResponse(target, resp) {
  redColor = "#FF6666"
  greenColor = "#66FF66"
  var bgColor = resp.status == "success" ? greenColor : redColor;
  var cellText = resp.message;

  target.parentNode.style.background = bgColor;
  target.parentNode.innerText = cellText;
}


function decryptBtnClick(event) {
  row = event.target.parentNode.parentNode;
  row_id = row.getAttribute("value");
  password = prompt("Enter the password: ");

  if (!password) return

  data = {
    "row_id": row_id,
    "password": password,
  }


  fetch("/decrypt", constructFetchJsonPost(data))
  .then(resp => resp.json())
  .then(json => handleDecryptResponse(event.target, json));
}


function expandCellText(event) {
  console.log("EXPAND CELL");
}


function tableBodyClick(event) {
  // console.log("EVENT: ");
  // console.log(event);
  // console.log("TARGET: ");
  // console.log(event.target);

  if (event.target.tagName == "BUTTON") {
    decryptBtnClick(event);
  } else if (event.target.cellIndex == 2 && !event.target.children.length) {
    expandCellText(event);
  }
}


function sortSubmit(event) {
  var sort = event.target.value;
  sessionStorage.setItem("sorting", sort);
  event.target.parentNode.submit();
}


function filterSubmit(event) {
  var formData = new FormData(event.target);
  
  for (var kv of formData.entries()) {
    sessionStorage.setItem(kv[0], kv[1]);
  }
  
  sessionStorage.removeItem("form-id");
  sessionStorage.removeItem("sorting")
}


function resetSubmit(event) {
  event.preventDefault();
  window.location = "/"
}


function populateFormWithSessionStorage(event) {
  var form_data = event.formData;
  console.log(form_data);

  for(var i = 0; i < sessionStorage.length; i++) {
    var key = sessionStorage.key(i);
    form_data.append(key, sessionStorage.getItem(key));
  }
}


function clearSessionStorage(event) {
  sessionStorage.clear();
}


function changePageArrow(event, dir) {
  event.preventDefault();
  curr_page = window.location.pathname.split("/")[1];
  curr_page = curr_page ? curr_page : 1
  last_page = document.getElementsByClassName("actual-page-number").length

  if (curr_page == 1 && dir < 0) {
    return;
  } else if (curr_page >= last_page && dir > 0) {
    return;
  } else {
    var new_page = parseInt(curr_page) + dir;
    submitPageChanger(new_page);
  }
}


function changePageNumber(event) {
  event.preventDefault();

  if (event.target.className != "actual-page-number") return;

  page = event.target.innerText;
  submitPageChanger(page);
}


function submitPageChanger(page){
  pageChanger = document.getElementById("page-changer");
  pageChanger.action = page;
  pageChanger.submit();
}


document.getElementById("bottle-content").addEventListener("click", tableBodyClick);
document.getElementById("left-url").addEventListener("click", (event) => changePageArrow(event, -1));
document.getElementById("right-url").addEventListener("click", (event) => changePageArrow(event, 1));
document.getElementById("pages").addEventListener("click", changePageNumber)

document.getElementById("sorting").addEventListener("change", sortSubmit);

document.getElementById("filter-form").addEventListener("submit", filterSubmit);
document.getElementById("reset-form").addEventListener("submit", resetSubmit);

document.getElementById("sort-form").addEventListener("formdata", populateFormWithSessionStorage);
document.getElementById("page-changer").addEventListener("formdata", populateFormWithSessionStorage)

window.addEventListener("load", () => { if (self.location.pathname == "/") { clearSessionStorage(); }});

