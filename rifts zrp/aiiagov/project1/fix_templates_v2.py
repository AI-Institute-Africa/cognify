import os

def fix_manage_files():
    target = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\manage_files.html'
    content = """{% load static %}
<div class="container-fluid">
    <form action="" id="file_doc-form">
        <input type="hidden" name="id" value="{{file_doc.id}}">
        <div class="row">
            <div class="col-md-6 mb-4">
                <label for="ref_num" class="form-label small fw-bold text-muted text-uppercase mb-2">Reference
                    Number</label>
                <input type="text" id="ref_num" name="ref_num"
                    class="form-control border-0 shadow-sm rounded-pill px-3 font-monospace"
                    value="{{file_doc.ref_num}}" required placeholder="REF-XXXXX">
            </div>
            <div class="col-md-3 mb-4">
                <label for="barcode" class="form-label small fw-bold text-muted text-uppercase mb-2">Barcode</label>
                <input type="text" id="barcode" name="barcode"
                    class="form-control border-0 shadow-sm rounded-pill px-3 font-monospace"
                    value="{{file_doc.barcode|default:''}}" placeholder="Scan Barcode">
            </div>
            <div class="col-md-3 mb-4">
                <label for="nfc_id" class="form-label small fw-bold text-muted text-uppercase mb-2">NFC ID</label>
                <input type="text" id="nfc_id" name="nfc_id"
                    class="form-control border-0 shadow-sm rounded-pill px-3 font-monospace"
                    value="{{file_doc.nfc_id|default:''}}" placeholder="Scan NFC Tag">
            </div>
        </div>
        <div class="mb-4">
            <label for="sub_category" class="form-label small fw-bold text-muted text-uppercase mb-2">Classification /
                Sub-Category</label>
            <select id="sub_category" name="sub_category" class="form-select border-0 shadow-sm rounded-pill" required>
                {% if not file_doc.sub_category %}
                <option value="" disabled selected>Select Category</option>
                {% endif %}
                {% for sub_category in sub_categories %}
                <option value="{{sub_category.id}}" {% if file_doc.sub_category.id == sub_category.id %}selected{% endif %}>{{sub_category.category}} - {{sub_category.name}}</option>
                {% endfor %}
            </select>
        </div>
        <div class="mb-4">
            <label for="title" class="form-label small fw-bold text-muted text-uppercase mb-2">File Title /
                Label</label>
            <input type="text" id="title" name="title" class="form-control border-0 shadow-sm rounded-pill px-3"
                value="{{file_doc.title}}" required placeholder="Enter File Title">
        </div>
        <div class="mb-4">
            <label for="description" class="form-label small fw-bold text-muted text-uppercase mb-2">Technical
                Description</label>
            <textarea rows="3" id="description" name="description"
                class="form-control border-0 shadow-sm rounded-3 px-3 py-2" required
                placeholder="Enter record summary...">{{file_doc.description}}</textarea>
        </div>
        <div class="mb-4">
            <label for="status" class="form-label small fw-bold text-muted text-uppercase mb-2">Record Status</label>
            <select id="status" name="status" class="form-select border-0 shadow-sm rounded-pill px-3" required>
                <option value="1" {% if file_doc.status == '1' %}selected{% endif %}>Active</option>
                <option value="0" {% if file_doc.status == '0' or file_doc.status == '2' %}selected{% endif %}>Inactive
                </option>
            </select>
        </div>
        <div class="mb-4">
            <label for="file_attachment" class="form-label small fw-bold text-muted text-uppercase mb-2">Digital
                Attachment (Optional)</label>
            <input type="file" id="file_attachment" name="file_attachment"
                class="form-control border-0 shadow-sm rounded-pill px-3">
            {% if file_doc.file_attachment %}
            <div class="mt-2 ps-3">
                <a href="{{ file_doc.file_attachment.url }}" target="_blank" class="text-primary small"><i
                        class="fas fa-file-download me-1"></i> View Current: {{ file_doc.file_attachment.name }}</a>
            </div>
            {% endif %}
        </div>
    </form>
</div>
<script>
    $(function () {
        $('#uni_modal').on('shown.bs.modal', function () {
            $('#sub_category').select2({
                width: "100%",
                placeholder: "Please Select Category Here",
                dropdownParent: $('#uni_modal'),
                selectionCssClass: "form-control border-0 shadow-sm rounded-pill"
            })
        })
        $('#file_doc-form').submit(function (e) {
            e.preventDefault();
            var _this = $(this)
            $('.err-msg').remove();
            var el = $('<div>')
            el.addClass("alert alert-danger err-msg rounded-3 small p-2 mb-3")
            el.hide()
            if (_this[0].checkValidity() == false) {
                _this[0].reportValidity();
                return false;
            }
            start_loader();
            $.ajax({
                headers: {
                    "X-CSRFToken": '{{csrf_token}}'
                },
                url: "{% url 'save-file_doc' %}",
                data: new FormData($(this)[0]),
                cache: false,
                contentType: false,
                processData: false,
                method: 'POST',
                type: 'POST',
                dataType: 'json',
                error: err => {
                    console.error(err)
                    alert("An error occured", 'error');
                    end_loader();
                },
                success: function (resp) {
                    if (typeof resp == 'object' && resp.status == 'success') {
                        location.reload()
                    } else if (resp.status == 'failed' && !!resp.msg) {
                        el.text(resp.msg)
                    } else {
                        el.text("An error occured", 'error');
                        end_loader();
                        console.error(resp)
                    }
                    _this.prepend(el)
                    el.show('slow')
                    $("html, body, .modal").scrollTop(0);
                    end_loader()
                }
            })
        })
    })
</script>"""
    with open(target, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"Fixed {target}")

def fix_manage_borrow():
    target = r'c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\manage_borrow.html'
    content = """{% load static %}
<div class="container-fluid">
    <form action="" id="borrow-form">
        <input type="hidden" name="id" value="{{ borrow.id }}">
        <input type="hidden" name="code" value="generate_code">
        <div class="row">
            <div class="col-lg-6 col-md-6 col-sm-12">
                <div class="mb-4">
                    <label for="file_doc" class="form-label small fw-bold text-muted text-uppercase mb-2">Registry
                        File</label>
                    <select id="file_doc" name="file_doc" class="form-select border-0 shadow-sm rounded-pill" required>
                        {% if not borrow %}
                        <option value="" selected disabled>Select File</option>
                        {% endif %}
                        {% for f in file_doc %}
                        <option value="{{ f.id }}" {% if borrow.file_doc.id == f.id %}selected{% endif %}>{{ f }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-12">
                <div class="mb-4">
                    <label for="borrower" class="form-label small fw-bold text-muted text-uppercase mb-2">Borrower /
                        Officer</label>
                    <select id="borrower" name="borrower" class="form-select border-0 shadow-sm rounded-pill" required>
                        {% if not borrow %}
                        <option value="" selected disabled>Select Officer</option>
                        {% endif %}
                        {% for b in borrower %}
                        <option value="{{ b.id }}" data-email="{{ b.email }}" {% if borrow.borrower.id == b.id %}selected{% endif %}>{{ b.code }} - {{ b.first_name }} {{ b.last_name }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-12">
                <div class="mb-4">
                    <label for="borrowing_date" class="form-label small fw-bold text-muted text-uppercase mb-2">Issue
                        Date</label>
                    <input type="date" id="borrowing_date" name="borrowing_date"
                        class="form-control border-0 shadow-sm rounded-pill px-3"
                        value="{% if borrow %}{{ borrow.borrowing_date|date:'Y-m-d' }}{% else %}{% now 'Y-m-d' %}{% endif %}"
                        required>
                </div>
            </div>
            <div class="col-lg-6 col-md-6 col-sm-12">
                <div class="mb-4">
                    <label for="return_date" class="form-label small fw-bold text-muted text-uppercase mb-2">Return Due
                        Date</label>
                    <input type="date" id="return_date" name="return_date"
                        class="form-control border-0 shadow-sm rounded-pill px-3"
                        value="{{ borrow.return_date|date:'Y-m-d' }}" min="{% now 'Y-m-d' %}" required>
                </div>
            </div>
            <div class="col-lg-7 col-md-8 col-sm-12">
                <div class="mb-4">
                    <label for="folio_ref" class="form-label small fw-bold text-muted text-uppercase mb-2">Folio ID /
                        Reference</label>
                    <input type="text" id="folio_ref" name="folio_ref"
                        class="form-control border-0 shadow-sm rounded-pill px-3 font-monospace"
                        placeholder="Enter Reference" value="{{ borrow.folio_ref }}" required>
                </div>
            </div>
            <div class="col-12">
                <div class="mb-4">
                    <label for="scanned_tag" class="form-label small fw-bold text-primary mb-2"><i
                            class="fas fa-barcode me-1"></i> Scan QR/Barcode/NFC</label>
                    <input type="text" id="scanned_tag" name="scanned_tag"
                        class="form-control border-0 shadow-sm rounded-pill px-3 bg-light"
                        placeholder="Awaiting scan..." required autofocus>
                    <div class="extra-small text-muted mt-1">Please scan the physical file tag to verify identity before
                        issuing.</div>
                </div>
            </div>
        </div>
    </form>
</div>
<script>
    $(function () {
        $('#uni_modal').on('shown.bs.modal', function () {
            $('#borrower').select2({ placeholder: 'Please Select Borrower Here', width: '100%', dropdownParent: $('#uni_modal') });
            $('#file_doc').select2({ placeholder: 'Please Select File Here', width: '100%', dropdownParent: $('#uni_modal') });
        });
        $('#borrow-form').submit(function (e) {
            e.preventDefault();
            var _this = $(this);
            $('.err-msg').remove();
            var el = $('<div>').addClass('alert alert-danger err-msg rounded-3 small p-2 mb-3').hide();
            if (_this[0].checkValidity() == false) { _this[0].reportValidity(); return false; }
            start_loader();
            $.ajax({
                headers: { 'X-CSRFToken': '{{ csrf_token }}' },
                url: "{% url 'save-borrow' %}",
                data: new FormData($(this)[0]),
                cache: false, contentType: false, processData: false,
                method: 'POST', type: 'POST', dataType: 'json',
                error: err => { console.error(err); alert('An error occurred'); end_loader(); },
                success: function (resp) {
                    if (typeof resp == 'object' && resp.status == 'success') {
                        location.reload()
                    } else if (resp.status == 'failed' && !!resp.msg) {
                        el.text(resp.msg);
                    } else { el.text('An error occurred'); end_loader(); }
                    _this.prepend(el); el.show('slow');
                    $('html, body, .modal').scrollTop(0);
                    end_loader();
                }
            });
        });
    });
</script>"""
    with open(target, 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print(f"Fixed {target}")

if __name__ == "__main__":
    fix_manage_files()
    fix_manage_borrow()
