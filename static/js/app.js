// File drop zone: show filename, drag states. No emojis, no frameworks.
(function () {
  var drop = document.getElementById("drop");
  var input = document.getElementById("resume_file");
  var fname = document.getElementById("fname");

  if (drop && input) {
    function show() {
      if (input.files && input.files.length) {
        fname.textContent = "Selected: " + input.files[0].name;
        drop.classList.add("has-file");
      } else {
        drop.classList.remove("has-file");
      }
    }
    input.addEventListener("change", show);
    ["dragenter", "dragover"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("drag"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("drag"); });
    });
    drop.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; show(); }
    });
  }

  var form = document.getElementById("forge-form");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = document.getElementById("submit-btn");
      if (btn) { btn.disabled = true; btn.textContent = "Forging your resume..."; }
    });
  }
})();
