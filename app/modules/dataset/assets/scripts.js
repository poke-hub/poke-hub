var currentId = 0;
var amount_authors = 0;

function show_upload_dataset() {
  document.getElementById("upload_dataset").style.display = "block";
}

function generateIncrementalId() {
  return currentId++;
}

function addField(newAuthor, name, text, className = "col-lg-6 col-12 mb-3") {
  let fieldWrapper = document.createElement("div");
  fieldWrapper.className = className;

  let label = document.createElement("label");
  label.className = "form-label";
  label.for = name;
  label.textContent = text;

  let field = document.createElement("input");
  field.name = name;
  field.className = "form-control";

  fieldWrapper.appendChild(label);
  fieldWrapper.appendChild(field);
  newAuthor.appendChild(fieldWrapper);
}

function addRemoveButton(newAuthor) {
  let buttonWrapper = document.createElement("div");
  buttonWrapper.className = "col-12 mb-2";

  let button = document.createElement("button");
  button.textContent = "Remove author";
  button.className = "btn btn-danger btn-sm";
  button.type = "button";
  button.addEventListener("click", function (event) {
    event.preventDefault();
    newAuthor.remove();
  });

  buttonWrapper.appendChild(button);
  newAuthor.appendChild(buttonWrapper);
}

function createAuthorBlock(idx, suffix) {
  let newAuthor = document.createElement("div");
  newAuthor.className = "author row";
  newAuthor.style.cssText =
    "border:2px dotted #ccc;border-radius:10px;padding:10px;margin:10px 0; background-color: white";

  addField(newAuthor, `${suffix}authors-${idx}-name`, "Name *");
  addField(newAuthor, `${suffix}authors-${idx}-affiliation`, "Affiliation");
  addField(newAuthor, `${suffix}authors-${idx}-orcid`, "ORCID");
  addRemoveButton(newAuthor);

  return newAuthor;
}

function check_title_and_description() {
  let titleInput = document.querySelector('input[name="title"]');
  let descriptionTextarea = document.querySelector('textarea[name="desc"]');

  titleInput.classList.remove("error");
  descriptionTextarea.classList.remove("error");
  clean_upload_errors();

  let titleLength = titleInput.value.trim().length;
  let descriptionLength = descriptionTextarea.value.trim().length;

  if (titleLength < 3) {
    write_upload_error("title must be of minimum length 3");
    titleInput.classList.add("error");
  }

  if (descriptionLength < 3) {
    write_upload_error("description must be of minimum length 3");
    descriptionTextarea.classList.add("error");
  }

  return titleLength >= 3 && descriptionLength >= 3;
}

document.getElementById("add_author").addEventListener("click", function () {
  let authors = document.getElementById("authors");
  let newAuthor = createAuthorBlock(amount_authors++, "");
  authors.appendChild(newAuthor);
});

document.addEventListener("click", function (event) {
  if (event.target && event.target.classList.contains("add_author_to_poke")) {
    let authorsButtonId = event.target.id;
    let authorsId = authorsButtonId.replace("_button", "");
    let authors = document.getElementById(authorsId);
    let id = authorsId.replace("_form_authors", "");
    let newAuthor = createAuthorBlock(amount_authors, `poke_models-${id}-`);
    authors.appendChild(newAuthor);
  }
});

function show_loading() {
  document.getElementById("upload_button").style.display = "none";
  document.getElementById("loading").style.display = "block";
}

function hide_loading() {
  document.getElementById("upload_button").style.display = "block";
  document.getElementById("loading").style.display = "none";
}

function clean_upload_errors() {
  let upload_error = document.getElementById("upload_error");
  upload_error.innerHTML = "";
  upload_error.style.display = "none";
}

function write_upload_error(error_message) {
  let upload_error = document.getElementById("upload_error");
  let alert = document.createElement("p");
  alert.style.margin = "0";
  alert.style.padding = "0";
  // Use innerText so newlines in error_message are preserved in rendering
  alert.innerText = "Upload error: " + error_message;
  upload_error.appendChild(alert);
  upload_error.style.display = "block";
}

// Helper to stringify nested error structures (WTForms returns nested dicts/arrays)
function formatError(err) {
  if (err === null || err === undefined) return "";
  if (typeof err === "string") return err;
  if (typeof err === "number" || typeof err === "boolean") return String(err);
  if (Array.isArray(err)) return err.map((v) => formatError(v)).join("; ");
  if (typeof err === "object") {
    try {
      return Object.entries(err)
        .map(([k, v]) => {
          const formatted = formatError(v);
          return formatted ? `${k}: ${formatted}` : `${k}`;
        })
        .join("\n");
    } catch (e) {
      return JSON.stringify(err);
    }
  }
  return String(err);
}

function showToast(type, message) {
  const alerts = document.getElementById("alerts");
  const box = document.createElement("div");
  box.className = `alert alert-${type}`;
  box.style.marginTop = "8px";
  box.textContent = message;

  if (alerts) {
    alerts.style.display = "block";
    alerts.appendChild(box);
    setTimeout(() => {
      box.remove();
      if (!alerts.children.length) alerts.style.display = "none";
    }, 4000);
  } else {
    box.style.position = "fixed";
    box.style.right = "16px";
    box.style.bottom = "16px";
    box.style.zIndex = 2000;
    document.body.appendChild(box);
    setTimeout(() => box.remove(), 4000);
  }
}

function appendUploadedModel(filename) {
  show_upload_dataset();

  const fileList = document.getElementById("file-list");
  if (!fileList) return;

  const listItem = document.createElement("li");
  const h4Element = document.createElement("h4");
  h4Element.textContent = filename;
  listItem.appendChild(h4Element);

  const formUniqueId = generateIncrementalId();

  const formButton = document.createElement("button");
  formButton.innerHTML = "Show info";
  formButton.classList.add(
    "info-button",
    "btn",
    "btn-outline-secondary",
    "btn-sm"
  );
  formButton.style.borderRadius = "5px";
  formButton.id = formUniqueId + "_button";

  let space = document.createTextNode(" ");
  listItem.appendChild(space);

  const removeButton = document.createElement("button");
  removeButton.innerHTML = "Delete model";
  removeButton.classList.add(
    "remove-button",
    "btn",
    "btn-outline-danger",
    "btn-sm",
    "remove-button"
  );
  removeButton.style.borderRadius = "5px";

  removeButton.addEventListener("click", function () {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/dataset/file/delete", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = function () {
      if (xhr.status === 200) {
        fileList.removeChild(listItem);
        if (!fileList.children.length) {
          document.getElementById("upload_dataset").style.display = "none";
          clean_upload_errors();
        }
        showToast("success", "File deleted.");
      } else {
        showToast("danger", "Error deleting file.");
      }
    };
    xhr.send(JSON.stringify({ file: filename }));
  });

  listItem.appendChild(formButton);
  listItem.appendChild(removeButton);

  const formContainer = document.createElement("div");
  formContainer.id = formUniqueId + "_form";
  formContainer.classList.add("poke_form", "mt-3");
  formContainer.style.display = "none";

  formContainer.innerHTML = `
        <div class="row">
            <input type="hidden" value="${filename}" name="poke_models-${formUniqueId}-poke_filename">
            <div class="col-12">
                <div class="row">
                    <div class="col-12">
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="poke_models-${formUniqueId}-title">
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="mb-3">
                            <label class="form-label">Description</label>
                            <textarea rows="4" class="form-control" name="poke_models-${formUniqueId}-desc"></textarea>
                        </div>
                    </div>
                    <div class="col-lg-6 col-12">
                        <div class="mb-3">
                            <label class="form-label" for="publication_type">Publication type</label>
                            <select class="form-control" name="poke_models-${formUniqueId}-publication_type">
                                <option value="none">None</option>
                                <option value="annotationcollection">Annotation Collection</option>
                                <option value="book">Book</option>
                                <option value="section">Book Section</option>
                                <option value="conferencepaper">Conference Paper</option>
                                <option value="datamanagementplan">Data Management Plan</option>
                                <option value="article">Journal Article</option>
                                <option value="patent">Patent</option>
                                <option value="preprint">Preprint</option>
                                <option value="deliverable">Project Deliverable</option>
                                <option value="milestone">Project Milestone</option>
                                <option value="proposal">Proposal</option>
                                <option value="report">Report</option>
                                <option value="softwaredocumentation">Software Documentation</option>
                                <option value="taxonomictreatment">Taxonomic Treatment</option>
                                <option value="technicalnote">Technical Note</option>
                                <option value="thesis">Thesis</option>
                                <option value="workingpaper">Working Paper</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                    </div>
                    <div class="col-lg-6 col-6">
                        <div class="mb-3">
                            <label class="form-label" for="publication_doi">Publication DOI</label>
                            <input class="form-control" name="poke_models-${formUniqueId}-publication_doi" type="text" value="">
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="mb-3">
                            <label class="form-label">Tags (separated by commas)</label>
                            <input type="text" class="form-control" name="poke_models-${formUniqueId}-tags">
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="mb-3">
                            <label class="form-label">Poke version</label>
                            <input type="text" class="form-control" name="poke_models-${formUniqueId}-poke_version">
                        </div>
                    </div>
                    <div class="col-12">
                        <div class="mb-3">
                            <label class="form-label">Authors</label>
                            <div id="${formContainer.id}_authors"></div>
                            <button type="button" class="add_author_to_poke btn btn-secondary" id="${formContainer.id}_authors_button">Add author</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

  formButton.addEventListener("click", function () {
    if (formContainer.style.display === "none") {
      formContainer.style.display = "block";
      formButton.innerHTML = "Hide info";
    } else {
      formContainer.style.display = "none";
      formButton.innerHTML = "Show info";
    }
  });

  listItem.appendChild(formContainer);
  fileList.appendChild(listItem);
}

// handlers ZIP / GitHub
function onZipSelected(e) {
  e.preventDefault();

  const zipInput = document.getElementById("zipFile");
  const savedBox = document.getElementById("zipSavedBox");
  const ignoredBox = document.getElementById("zipIgnoredBox");
  const savedList = document.getElementById("zipSavedList");
  const ignoredList = document.getElementById("zipIgnoredList");
  const errorBox = document.getElementById("zipErrorBox");

  if (!zipInput) return;

  if (savedBox) {
    savedBox.style.display = "none";
    savedList && (savedList.innerHTML = "");
  }
  if (ignoredBox) {
    ignoredBox.style.display = "none";
    ignoredList && (ignoredList.innerHTML = "");
  }
  if (errorBox) {
    errorBox.style.display = "none";
    errorBox.textContent = "";
  }

  if (!zipInput.files || !zipInput.files.length) {
    showToast("warning", "Selecciona un archivo ZIP.");
    if (errorBox) {
      errorBox.textContent = "Selecciona un archivo ZIP.";
      errorBox.style.display = "block";
    }
    return;
  }

  const fd = new FormData();
  fd.append("file", zipInput.files[0]);

  fetch("/dataset/zip/upload", { method: "POST", body: fd })
    .then((r) =>
      r.json().then((j) => ({ ok: r.ok, status: r.status, body: j }))
    )
    .then(({ ok, status, body }) => {
      if (!ok) throw new Error(body.message || "ZIP error (" + status + ")");

      (body.saved || []).forEach((fn) => {
        if (savedList) {
          const li = document.createElement("li");
          li.textContent = fn;
          savedList.appendChild(li);
        }
        appendUploadedModel(fn);
      });
      (body.ignored || []).forEach((fn) => {
        if (ignoredList) {
          const li = document.createElement("li");
          li.textContent = fn;
          ignoredList.appendChild(li);
        }
      });

      if (savedBox && (body.saved || []).length)
        savedBox.style.display = "block";
      if (ignoredBox && (body.ignored || []).length)
        ignoredBox.style.display = "block";

      showToast(
        "success",
        `ZIP procesado: ${(body.saved || []).length} archivos .poke añadidos`
      );
    })
    .catch((err) => {
      showToast("danger", err.message || "Error procesando ZIP");
      if (errorBox) {
        errorBox.textContent = err.message;
        errorBox.style.display = "block";
      }
    });
}

function onGithubImport(e) {
  e.preventDefault();

  const url = (document.getElementById("ghUrl")?.value || "").trim();
  const branch =
    (document.getElementById("ghBranch")?.value || "").trim() || "main";
  const subdir =
    (document.getElementById("ghSubdir")?.value || "").trim() || null;

  const savedBox = document.getElementById("ghSavedBox");
  const ignoredBox = document.getElementById("ghIgnoredBox");
  const savedList = document.getElementById("ghSavedList");
  const ignoredList = document.getElementById("ghIgnoredList");
  const errorBox = document.getElementById("ghErrorBox");

  if (savedBox) {
    savedBox.style.display = "none";
    savedList && (savedList.innerHTML = "");
  }
  if (ignoredBox) {
    ignoredBox.style.display = "none";
    ignoredList && (ignoredList.innerHTML = "");
  }
  if (errorBox) {
    errorBox.style.display = "none";
    errorBox.textContent = "";
  }

  if (!url) {
    const msg = "Introduce una URL de GitHub válida.";
    showToast("warning", msg);
    if (errorBox) {
      errorBox.textContent = msg;
      errorBox.style.display = "block";
    }
    return;
  }

  fetch("/dataset/github/import", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: url, branch: branch, subdir: subdir }),
  })
    .then((r) =>
      r.json().then((j) => ({ ok: r.ok, status: r.status, body: j }))
    )
    .then(({ ok, status, body }) => {
      if (!ok)
        throw new Error(body.message || "GitHub import error (" + status + ")");

      (body.saved || []).forEach((fn) => {
        if (savedList) {
          const li = document.createElement("li");
          li.textContent = fn;
          savedList.appendChild(li);
        }
        appendUploadedModel(fn);
      });
      (body.ignored || []).forEach((fn) => {
        if (ignoredList) {
          const li = document.createElement("li");
          li.textContent = fn;
          ignoredList.appendChild(li);
        }
      });

      if (savedBox && (body.saved || []).length)
        savedBox.style.display = "block";
      if (ignoredBox && (body.ignored || []).length)
        ignoredBox.style.display = "block";

      showToast(
        "success",
        `GitHub import: ${(body.saved || []).length} archivos .poke añadidos`
      );
    })
    .catch((err) => {
      showToast("danger", err.message || "Error importando desde GitHub");
      if (errorBox) {
        errorBox.textContent = err.message;
        errorBox.style.display = "block";
      }
    });
}

window.onload = function () {
  // Intentar test de Zenodo solo si la función existe
  if (typeof test_zenodo_connection === "function") {
    test_zenodo_connection();
  }

  const zipBtn = document.getElementById("processZipBtn");
  if (zipBtn) {
    zipBtn.addEventListener("click", onZipSelected);
  }

  const ghBtn = document.getElementById("importGithubBtn");
  if (ghBtn) {
    ghBtn.addEventListener("click", onGithubImport);
  }

  document
    .getElementById("upload_button")
    .addEventListener("click", function () {
      clean_upload_errors();
      show_loading();

      // check title and description
      let check = check_title_and_description();

      if (check) {
        // process data form
        const formData = {};

        ["basic_info_form", "uploaded_models_form"].forEach((formId) => {
          const form = document.getElementById(formId);
          const inputs = form.querySelectorAll("input, select, textarea");
          inputs.forEach((input) => {
            if (input.name) {
              formData[input.name] = formData[input.name] || [];
              formData[input.name].push(input.value);
            }
          });
        });

        let formDataJson = JSON.stringify(formData);
        console.log(formDataJson);

        const csrfToken = document.getElementById("csrf_token").value;
        const formUploadData = new FormData();
        formUploadData.append("csrf_token", csrfToken);

        for (let key in formData) {
          if (formData.hasOwnProperty(key)) {
            formUploadData.set(key, formData[key]);
          }
        }

        let checked_orcid = true;
        if (Array.isArray(formData.author_orcid)) {
          for (let orcid of formData.author_orcid) {
            orcid = orcid.trim();
            if (orcid !== "" && !isValidOrcid(orcid)) {
              hide_loading();
              write_upload_error(
                "ORCID value does not conform to valid format: " + orcid
              );
              checked_orcid = false;
              break;
            }
          }
        }
        let checked_name = true;
        if (Array.isArray(formData.author_name)) {
          for (let name of formData.author_name) {
            name = name.trim();
            if (name === "") {
              hide_loading();
              write_upload_error("The author's name cannot be empty");
              checked_name = false;
              break;
            }
          }
        }

        if (checked_orcid && checked_name) {
          const datasetId = this.dataset.id;

          const url = datasetId
            ? `/dataset/${datasetId}/edit`
            : `/dataset/upload`;

          formUploadData.set("save_as_draft", "0");

          fetch(url, {
            method: "POST",
            body: formUploadData,
            headers: {
              "X-Requested-With": "XMLHttpRequest",
            },
          })
            .then(async (response) => {
              if (!response.ok) {
                try {
                  const data = await response.json();
                  console.error("Error: " + (data.message || JSON.stringify(data)));

                  // Si el servidor devuelve un objeto con errores en la raíz
                  // (por ejemplo { poke_models: {...} }) usamos formatError
                  // para convertirlo a texto legible.
                  let errorMsg = "Unexpected error";

                  if (data) {
                    if (data.message) {
                      // message puede ser string u objeto
                      errorMsg = typeof data.message === "object" ? formatError(data.message) : String(data.message);
                    } else {
                      // Si no hay 'message', formateamos todo el objeto devuelto
                      errorMsg = formatError(data);
                    }
                  }

                  write_upload_error(errorMsg || "Unexpected error");
                } catch (e) {
                  console.error("Error no-JSON", e);
                  write_upload_error("Unexpected error uploading dataset");
                }
                hide_loading();
                return;
              }

              console.log("Dataset sent successfully");

              if (response.redirected) {
                window.location.href = response.url;
                return;
              }

              const ct = response.headers.get("Content-Type") || "";

              if (ct.includes("application/json")) {
                try {
                  const data = await response.json();
                  console.log(data.message || data);

                  if (data.redirect) {
                    window.location.href = data.redirect;
                  } else {
                    window.location.href = "/dataset/list";
                  }
                } catch (e) {
                  console.error("JSON parse error", e);
                  window.location.href = "/dataset/list";
                }
              } else {
                window.location.href = "/dataset/list";
              }
            })
            .catch((error) => {
              console.error("Error in POST request:", error);
              hide_loading();
              write_upload_error("Network error: " + error.message);
            });
        }
      } else {
        hide_loading();
      }
    });
};

// === Reemplazo del bloque DOMContentLoaded para guardar/actualizar drafts SIN <form> ===
document.addEventListener("DOMContentLoaded", () => {
  const saveDraftButton = document.getElementById("save_draft_button");
  const updateDraftButton = document.getElementById("update_draft_button");

  // Recoge los campos desde los contenedores (divs) basic_info_form y uploaded_models_form
  const collectFields = () => {
    const data = {};
    ["basic_info_form", "uploaded_models_form"].forEach((id) => {
      const box = document.getElementById(id);
      if (!box) return;
      const inputs = box.querySelectorAll("input, select, textarea");
      inputs.forEach((el) => {
        if (!el.name) return;
        if (!data[el.name]) data[el.name] = [];
        data[el.name].push(el.value);
      });
    });
    return data;
  };

  // Envía el draft a la URL indicada
  const sendDraft = (url) => {
    const fields = collectFields();
    const fd = new FormData();

    // CSRF (WTForms hidden_tag lo sigue pintando aunque no haya <form>)
    const csrf = document.getElementById("csrf_token");
    if (csrf?.value) fd.append("csrf_token", csrf.value);

    // Campos recogidos
    Object.keys(fields).forEach((k) => fd.set(k, fields[k]));

    // Flag de borrador
    fd.set("save_as_draft", "1");

    fetch(url, { method: "POST", body: fd })
      .then((res) => {
        if (res.redirected) {
          window.location.href = res.url;
          return null;
        }
        return res.json().then((data) => ({ ok: res.ok, data }));
      })
      .then((out) => {
        if (!out) return;
        if (out.ok && out.data?.redirect)
          window.location.href = out.data.redirect;
        else if (out.data?.message) alert(out.data.message);
      })
      .catch((err) => console.error("Error saving draft:", err));
  };

  // Crear nuevo draft (pantalla de upload)
  if (saveDraftButton) {
    saveDraftButton.addEventListener("click", (e) => {
      e.preventDefault();
      sendDraft("/dataset/upload");
    });
  }

  // Actualizar draft existente (pantalla de edición)
  if (updateDraftButton) {
    updateDraftButton.addEventListener("click", (e) => {
      e.preventDefault();
      const datasetId = updateDraftButton.dataset.id;
      if (!datasetId) {
        console.error("Falta data-id en #update_draft_button");
        alert("No se puede actualizar: falta el identificador del dataset.");
        return;
      }
      sendDraft(`/dataset/${datasetId}/edit`);
    });
  }

  document.querySelectorAll(".delete-existing-fm").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const datasetId =
        btn.dataset.datasetId || btn.getAttribute("data-dataset-id");
      const fmId = btn.dataset.fmId || btn.getAttribute("data-fm-id");

      if (!datasetId || !fmId) {
        alert("Missing dataset/fm id");
        return;
      }

      if (!confirm("¿Seguro que quieres borrar este UVL del dataset?")) return;

      try {
        const res = await fetch(
          `/dataset/${datasetId}/featuremodel/${fmId}/delete`,
          {
            method: "POST",
            headers: { "X-Requested-With": "XMLHttpRequest" },
          }
        );
        const out = await res.json();
        if (res.ok && out.ok) {
          const row = document.getElementById(`fm-row-${fmId}`);
          if (row) row.remove();
        } else {
          alert(out?.message || "Error deleting feature model");
        }
      } catch (err) {
        console.error(err);
        alert("Error deleting feature model");
      }
    });
  });
});

function isValidOrcid(orcid) {
  let orcidRegex = /^\d{4}-\d{4}-\d{4}-\d{4}$/;
  return orcidRegex.test(orcid);
}
