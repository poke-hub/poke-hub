var currentId = 0;
        var amount_authors = 0;

        function show_upload_dataset() {
            document.getElementById("upload_dataset").style.display = "block";
        }

        function generateIncrementalId() {
            return currentId++;
        }

        function addField(newAuthor, name, text, className = 'col-lg-6 col-12 mb-3') {
            let fieldWrapper = document.createElement('div');
            fieldWrapper.className = className;

            let label = document.createElement('label');
            label.className = 'form-label';
            label.for = name;
            label.textContent = text;

            let field = document.createElement('input');
            field.name = name;
            field.className = 'form-control';

            fieldWrapper.appendChild(label);
            fieldWrapper.appendChild(field);
            newAuthor.appendChild(fieldWrapper);
        }

        function addRemoveButton(newAuthor) {
            let buttonWrapper = document.createElement('div');
            buttonWrapper.className = 'col-12 mb-2';

            let button = document.createElement('button');
            button.textContent = 'Remove author';
            button.className = 'btn btn-danger btn-sm';
            button.type = 'button';
            button.addEventListener('click', function (event) {
                event.preventDefault();
                newAuthor.remove();
            });

            buttonWrapper.appendChild(button);
            newAuthor.appendChild(buttonWrapper);
        }

        function createAuthorBlock(idx, suffix) {
            let newAuthor = document.createElement('div');
            newAuthor.className = 'author row';
            newAuthor.style.cssText = "border:2px dotted #ccc;border-radius:10px;padding:10px;margin:10px 0; background-color: white";

            addField(newAuthor, `${suffix}authors-${idx}-name`, 'Name *');
            addField(newAuthor, `${suffix}authors-${idx}-affiliation`, 'Affiliation');
            addField(newAuthor, `${suffix}authors-${idx}-orcid`, 'ORCID');
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

            return (titleLength >= 3 && descriptionLength >= 3);
        }


        document.getElementById('add_author').addEventListener('click', function () {
            let authors = document.getElementById('authors');
            let newAuthor = createAuthorBlock(amount_authors++, "");
            authors.appendChild(newAuthor);
        });


        document.addEventListener('click', function (event) {
            if (event.target && event.target.classList.contains('add_author_to_uvl')) {

                let authorsButtonId = event.target.id;
                let authorsId = authorsButtonId.replace("_button", "");
                let authors = document.getElementById(authorsId);
                let id = authorsId.replace("_form_authors", "")
                let newAuthor = createAuthorBlock(amount_authors, `feature_models-${id}-`);
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
            upload_error.style.display = 'none';
        }

        function write_upload_error(error_message) {
            let upload_error = document.getElementById("upload_error");
            let alert = document.createElement('p');
            alert.style.margin = '0';
            alert.style.padding = '0';
            alert.textContent = 'Upload error: ' + error_message;
            upload_error.appendChild(alert);
            upload_error.style.display = 'block';
        }

        window.onload = function () {

            test_zenodo_connection();

            document.getElementById('upload_button').addEventListener('click', function () {

                clean_upload_errors();
                show_loading();

                // check title and description
                let check = check_title_and_description();

                if (check) {
                    // process data form
                    const formData = {};

                    ["basic_info_form", "uploaded_models_form"].forEach((formId) => {
                        const form = document.getElementById(formId);
                        const inputs = form.querySelectorAll('input, select, textarea');
                        inputs.forEach(input => {
                            if (input.name) {
                                formData[input.name] = formData[input.name] || [];
                                formData[input.name].push(input.value);
                            }
                        });
                    });

                    let formDataJson = JSON.stringify(formData);
                    console.log(formDataJson);

                    const csrfToken = document.getElementById('csrf_token').value;
                    const formUploadData = new FormData();
                    formUploadData.append('csrf_token', csrfToken);

                    for (let key in formData) {
                        if (formData.hasOwnProperty(key)) {
                            formUploadData.set(key, formData[key]);
                        }
                    }

                    let checked_orcid = true;
                    if (Array.isArray(formData.author_orcid)) {
                        for (let orcid of formData.author_orcid) {
                            orcid = orcid.trim();
                            if (orcid !== '' && !isValidOrcid(orcid)) {
                                hide_loading();
                                write_upload_error("ORCID value does not conform to valid format: " + orcid);
                                checked_orcid = false;
                                break;
                            }
                        }
                    }


                    let checked_name = true;
                    if (Array.isArray(formData.author_name)) {
                        for (let name of formData.author_name) {
                            name = name.trim();
                            if (name === '') {
                                hide_loading();
                                write_upload_error("The author's name cannot be empty");
                                checked_name = false;
                                break;
                            }
                        }
                    }


                    if (checked_orcid && checked_name) {
                        const btn = document.getElementById('upload_button');
                        const datasetId = btn?.dataset?.id;
                        const saveAsDraft = btn?.value || "false";

                        // Si tiene id → estás en modo edición, usa /dataset/<id>/edit
                        const url = datasetId ? `/dataset/${datasetId}/edit` : '/dataset/upload';

                        // Añadimos save_as_draft al formData para que el backend lo recoja
                        formUploadData.append('save_as_draft', saveAsDraft);

                        fetch(url, {
                            method: 'POST',
                            body: formUploadData,
                            headers: {
                                'X-Requested-With': 'XMLHttpRequest'
                            }
                        })
                            .then(response => {
                                if (response.ok) {
                                    console.log('Dataset sent successfully');
                                    response.json().then(data => {
                                        console.log(data.message);
                                        window.location.href = "/dataset/list";
                                    });
                                } else {
                                    response.json().then(data => {
                                        console.error('Error: ' + data.message);
                                        hide_loading();

                                        write_upload_error(data.message);

                                    });
                                }
                            })
                            .catch(error => {
                                console.error('Error in POST request:', error);
                            });
                    }


                } else {
                    hide_loading();
                }


            });


        };


        // === Reemplazo del bloque DOMContentLoaded para guardar/actualizar drafts SIN <form> ===
        document.addEventListener("DOMContentLoaded", () => {
        const saveDraftButton   = document.getElementById("save_draft_button");
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
                if (res.redirected) { window.location.href = res.url; return null; }
                return res.json().then((data) => ({ ok: res.ok, data }));
            })
            .then((out) => {
                if (!out) return;
                if (out.ok && out.data?.redirect) window.location.href = out.data.redirect;
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
            const datasetId = btn.dataset.datasetId || btn.getAttribute("data-dataset-id");
            const fmId = btn.dataset.fmId || btn.getAttribute("data-fm-id");

            if (!datasetId || !fmId) {
                alert("Missing dataset/fm id");
                return;
            }

            if (!confirm("¿Seguro que quieres borrar este UVL del dataset?")) return;

            try {
                const res = await fetch(`/dataset/${datasetId}/featuremodel/${fmId}/delete`, {
                    method: "POST",
                    headers: { "X-Requested-With": "XMLHttpRequest" }
                });
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