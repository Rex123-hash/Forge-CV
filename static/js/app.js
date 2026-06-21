// ForgeCV input page: mode toggle, upload auto-fill, sample JD chips.
// No emojis, no frameworks.
(function () {
  function $(id) { return document.getElementById(id); }
  function setVal(id, v) { var el = $(id); if (el && v) el.value = v; }

  var fileInput = $("resume_file");
  var drop = $("drop");
  var fname = $("fname");
  var note = $("autofill-note");
  var uploadPane = $("upload-pane");

  // ---- mode toggle (Upload vs Fill manually) ----
  var modeBtns = document.querySelectorAll(".mode-btn");
  modeBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      modeBtns.forEach(function (x) { x.classList.remove("on"); });
      b.classList.add("on");
      if (b.dataset.mode === "upload") {
        if (uploadPane) uploadPane.style.display = "";
      } else {
        if (uploadPane) uploadPane.style.display = "none";
        if (fileInput) fileInput.value = "";
        if (fname) fname.textContent = "";
        if (drop) drop.classList.remove("has-file");
        if (note) note.classList.remove("show");
      }
    });
  });

  // ---- upload -> auto-fill the fields via /parse ----
  function autofill(file) {
    if (!file) return;
    fname.textContent = "Reading " + file.name + " ...";
    drop.classList.add("has-file");
    var fd = new FormData();
    fd.append("resume_file", file);
    fetch("/parse", { method: "POST", body: fd })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) {
          setVal("f-name", d.name); setVal("f-email", d.email);
          setVal("f-phone", d.phone); setVal("f-skills", d.skills);
          setVal("f-experience", d.experience);
          fname.textContent = "Loaded: " + file.name;
          if (note) note.classList.add("show");
        } else {
          fname.textContent = "Couldn't read that file - you can still fill the fields below.";
        }
      })
      .catch(function () {
        fname.textContent = "Couldn't read that file - you can still fill the fields below.";
      });
  }

  if (drop && fileInput) {
    fileInput.addEventListener("change", function () {
      if (fileInput.files.length) autofill(fileInput.files[0]);
    });
    ["dragenter", "dragover"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.add("drag"); });
    });
    ["dragleave", "drop"].forEach(function (ev) {
      drop.addEventListener(ev, function (e) { e.preventDefault(); drop.classList.remove("drag"); });
    });
    drop.addEventListener("drop", function (e) {
      if (e.dataTransfer && e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        autofill(e.dataTransfer.files[0]);
      }
    });
  }

  // ---- sample job-description chips ----
  var SAMPLES = {
    aiml: "We are hiring a Machine Learning Engineer with strong Python, scikit-learn, XGBoost and deep learning skills. You will build, evaluate and deploy ML models, do feature engineering and model evaluation, and ship to production with MLOps tools (MLflow, Docker) on the cloud.",
    webdev: "Seeking a Full-Stack Web Developer skilled in JavaScript, React, Node.js, HTML, CSS and REST APIs. You will build responsive web apps, integrate backends and databases (SQL or MongoDB), and deploy with Docker to the cloud.",
    datasci: "Looking for a Data Scientist proficient in Python, Pandas, NumPy, SQL and statistics. Responsibilities include exploratory data analysis, building predictive models, A/B testing, data visualization, and communicating insights to stakeholders.",
    swe: "Hiring a Software Engineer with strong data structures, algorithms and OOP in Python, Java or C++. You will design, build and test scalable backend services, write clean maintainable code, and collaborate via Git in an agile team.",
    cloud: "We need a Cloud / DevOps Engineer experienced with AWS or GCP, Docker, Kubernetes, CI/CD pipelines and infrastructure as code. You will automate deployments, manage cloud infrastructure, and own monitoring and reliability."
  };
  var chips = $("jd-chips");
  if (chips) {
    chips.addEventListener("click", function (e) {
      var b = e.target.closest(".jchip");
      if (!b) return;
      var jd = $("f-jd");
      if (jd && SAMPLES[b.dataset.jd]) { jd.value = SAMPLES[b.dataset.jd]; jd.focus(); }
    });
  }

  // ---- loading overlay on submit (with cycling messages) ----
  var form = $("forge-form");
  if (form) {
    form.addEventListener("submit", function () {
      var btn = $("submit-btn");
      if (btn) { btn.disabled = true; btn.textContent = "Forging..."; }
      var overlay = $("overlay"), msg = $("overlay-msg");
      if (overlay) {
        overlay.classList.add("show");
        var steps = ["Reading your details...", "Rewriting your experience...",
                     "Tailoring to the job...", "Scoring against ATS rules...",
                     "Laying out your one-page resume..."];
        var i = 0;
        setInterval(function () {
          i = (i + 1) % steps.length;
          if (msg) msg.textContent = steps[i];
        }, 1800);
      }
    });
  }

  // ---- frosted nav on scroll ----
  var nav = document.querySelector(".nav");
  if (nav) {
    var onScroll = function () { nav.classList.toggle("scrolled", window.scrollY > 8); };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  // ---- count up the score gauge numbers ----
  var nums = document.querySelectorAll(".gauge-num");
  nums.forEach(function (el) {
    var target = parseInt(el.textContent, 10);
    if (isNaN(target)) return;
    var start = null, dur = 1000;
    function tick(t) {
      if (start === null) start = t;
      var p = Math.min((t - start) / dur, 1);
      el.textContent = Math.round(target * p);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
})();
