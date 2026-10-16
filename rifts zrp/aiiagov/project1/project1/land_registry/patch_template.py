import re

filepath = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\governance\project_detail.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure badges are updated in the header
content = content.replace(
    "{% elif phase.status == 'Review' %}",
    "{% elif phase.status == 'Awaiting Team Member Approval' %}\n                             <span class=\"badge bg-warning-subtle text-warning rounded-pill px-3 py-2\"> <i class=\"fas fa-user\"></i> Awaiting Team Member</span>\n                             {% elif phase.status == 'Awaiting Project Leader Approval' %}"
)

# New 5-level HTML Block
new_gates_html = """
                    <!-- 5-LEVEL GOVERNANCE GATE CONTROLS -->
                    
                    {% if phase.status == 'Active' and gov_role == 'Team Member' %}
                    <!-- LEVEL 1: TEAM MEMBER -->
                    <div class="rounded-4 p-3 shadow-sm border mt-3" style="background: var(--card-bg); color: var(--text-color); border: 1px solid rgba(13, 110, 253, 0.2) !important;">
                        <h6 class="fw-bold mb-3 d-flex align-items-center justify-content-between">
                            <span><i class="fas fa-layer-group text-primary me-2"></i> Initial Phase Submission (Team Member)</span>
                            <span class="badge bg-primary bg-opacity-10 text-primary extra-small">Execution Phase</span>
                        </h6>
                        <form action="{% url 'advance-phase' phase.pk %}" method="POST">
                            {% csrf_token %}
                            <div class="mb-3">
                                <label class="small text-muted fw-bold mb-1">TEAM MEMBER COMMENTS (Optional)</label>
                                <textarea name="comments" class="form-control form-control-sm rounded-3" rows="2" placeholder="Peer review comments..."></textarea>
                            </div>
                            <div class="d-flex justify-content-end gap-2">
                                <button type="submit" class="btn btn-primary btn-sm rounded-pill px-4 fw-bold shadow-sm">
                                    <i class="fas fa-paper-plane me-2"></i> Submit to Project Leader
                                </button>
                            </div>
                        </form>
                    </div>

                    {% elif phase.status == 'Awaiting Project Leader Approval' and gov_role == 'Project Leader' %}
                    <!-- LEVEL 2: PROJECT LEADER -->
                    <div class="rounded-4 p-3 shadow-sm border mt-3" style="background: var(--card-bg); color: var(--text-color); border: 1px solid rgba(255, 193, 7, 0.5) !important;">
                        <h6 class="fw-bold mb-3 d-flex align-items-center justify-content-between">
                            <span><i class="fas fa-user-tie text-warning me-2"></i> Consolidation & Submission to PMT</span>
                            <span class="badge bg-warning bg-opacity-10 text-warning extra-small">PL Gate Review</span>
                        </h6>
                        <form action="{% url 'pm-consolidate-phase' phase.pk %}" method="POST">
                            {% csrf_token %}
                            <div class="mb-3">
                                <label class="small text-muted fw-bold mb-1">CONSOLIDATION NOTES (Summary for PMT/HOD/MD)</label>
                                <textarea name="comments" class="form-control form-control-sm rounded-3" rows="3" required placeholder="Consolidate tasks and provide an executive summary..."></textarea>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <button type="button" class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-semibold" onclick="openReturnModal({{ phase.pk }}, 'Project Leader')">
                                        <i class="fas fa-undo me-1"></i> Return for Correction
                                    </button>
                                </div>
                                <div>
                                    <button type="submit" class="btn btn-warning text-dark btn-sm rounded-pill px-4 fw-bold shadow-sm">
                                        <i class="fas fa-paper-plane me-2"></i> Forward to PMT
                                    </button>
                                </div>
                            </div>
                        </form>
                    </div>

                    {% elif phase.status == 'Awaiting PMT Approval' and gov_role == 'Project Management Team' %}
                    <!-- LEVEL 3: PMT -->
                    <div class="card border-0 shadow-sm rounded-4 overflow-hidden mt-3" style="border: 1px solid rgba(13, 202, 240, 0.5);">
                        <div class="card-header bg-info bg-opacity-10 border-0 py-3">
                            <h6 class="fw-bold mb-0 text-info"><i class="fas fa-user-shield me-2"></i> Project Management Team Verification (PMT)</h6>
                        </div>
                        <div class="card-body p-4">
                            {% if request.user.id not in phase.approver_ids %}
                             <form action="{% url 'pmt-verify-phase' phase.pk %}" method="POST" class="signature-form">
                                {% csrf_token %}
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">YOUR VERIFICATION COMMENTS (MANDATORY)</label>
                                    <textarea name="comments" class="form-control form-control-sm rounded-3" rows="2" required placeholder="Add your PMT verification notes..."></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">ELECTRONIC SIGNATURE (REQUIRED)</label>
                                    <div class="signature-wrapper glass-panel p-1 rounded-3 mb-2" style="background: rgba(255,255,255,0.05);">
                                        <canvas class="signature-pad" width="400" height="150" style="width: 100%; height: 150px; cursor: crosshair;"></canvas>
                                    </div>
                                    <input type="hidden" name="signature_data" class="signature-input">
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                     <button type="button" class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-semibold" onclick="openReturnModal({{ phase.pk }}, 'PMT')">Return to PL</button>
                                     <button type="submit" class="btn btn-info text-white btn-sm rounded-pill px-4 fw-bold submit-approval">Forward to HODs</button>
                                </div>
                            </form>
                            {% else %}
                            <div class="alert alert-info rounded-4 border-0 small py-3 px-4 mb-0">
                                <i class="fas fa-info-circle me-2"></i> You have already submitted your verification for this phase.
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    {% elif phase.status == 'Awaiting HODs Approval' and gov_role == 'HODs' %}
                    <!-- LEVEL 4: HODs -->
                    <div class="card border-0 shadow-sm rounded-4 overflow-hidden mt-3" style="border: 1px solid rgba(102, 16, 242, 0.5);">
                        <div class="card-header border-0 py-3" style="background: rgba(102, 16, 242, 0.1);">
                            <h6 class="fw-bold mb-0 text-indigo" style="color: #6610f2;"><i class="fas fa-building me-2"></i> Head of Departments Endorsement</h6>
                        </div>
                        <div class="card-body p-4">
                            {% if request.user.id not in phase.approver_ids %}
                             <form action="{% url 'hods-verify-phase' phase.pk %}" method="POST" class="signature-form">
                                {% csrf_token %}
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">YOUR STRATEGIC COMMENTS (MANDATORY)</label>
                                    <textarea name="comments" class="form-control form-control-sm rounded-3" rows="2" required placeholder="HODs notes and endorsement..."></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">ELECTRONIC SIGNATURE (REQUIRED)</label>
                                    <div class="signature-wrapper glass-panel p-1 rounded-3 mb-2" style="background: rgba(255,255,255,0.05);">
                                        <canvas class="signature-pad" width="400" height="150" style="width: 100%; height: 150px; cursor: crosshair;"></canvas>
                                    </div>
                                    <input type="hidden" name="signature_data" class="signature-input">
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                     <button type="button" class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-semibold" onclick="openReturnModal({{ phase.pk }}, 'HODs')">Return to PMT</button>
                                     <button type="submit" class="btn btn-indigo text-white btn-sm rounded-pill px-4 fw-bold submit-approval" style="background: #6610f2;">Forward to Board</button>
                                </div>
                            </form>
                            {% else %}
                            <div class="alert alert-indigo rounded-4 border-0 small py-3 px-4 mb-0" style="background: rgba(102, 16, 242, 0.08); color: #6610f2;">
                                <i class="fas fa-info-circle me-2"></i> You have already endorsed this phase.
                            </div>
                            {% endif %}
                        </div>
                    </div>

                    {% elif phase.status == 'Awaiting Board Approval' and gov_role == 'Board of Executives' %}
                    <!-- LEVEL 5: BOARD -->
                    <div class="card border-0 shadow-sm rounded-4 overflow-hidden mt-3" style="border: 2px solid #ff4757;">
                        <div class="card-header border-0 py-3" style="background: rgba(255, 71, 87, 0.1);">
                            <h6 class="fw-bold mb-0 text-danger"><i class="fas fa-crown me-2"></i> Final Board of Executives Approval</h6>
                        </div>
                        <div class="card-body p-4">
                            {% if request.user.id not in phase.approver_ids %}
                             <form action="{% url 'approve-phase' phase.pk 'Approved' %}" method="POST" class="signature-form">
                                {% csrf_token %}
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">FINAL VERDICT NOTES (MANDATORY)</label>
                                    <textarea name="comments" class="form-control form-control-sm rounded-3" rows="2" required placeholder="Board resolution notes..."></textarea>
                                </div>
                                <div class="mb-3">
                                    <label class="small text-muted fw-bold mb-1">ELECTRONIC SIGNATURE (REQUIRED)</label>
                                    <div class="signature-wrapper glass-panel p-1 rounded-3 mb-2" style="background: rgba(255,255,255,0.05);">
                                        <canvas class="signature-pad" width="400" height="150" style="width: 100%; height: 150px; cursor: crosshair;"></canvas>
                                    </div>
                                    <input type="hidden" name="signature_data" class="signature-input">
                                </div>
                                <div class="d-flex justify-content-end gap-2">
                                     <button type="button" class="btn btn-outline-danger btn-sm rounded-pill px-3 fw-semibold" onclick="openReturnModal({{ phase.pk }}, 'Board')">Reject / Return to HODs</button>
                                     <button type="submit" class="btn btn-danger text-white btn-sm rounded-pill px-4 fw-bold submit-approval">GRANT FINAL APPROVAL</button>
                                </div>
                            </form>
                            {% else %}
                            <div class="alert alert-danger rounded-4 border-0 small py-3 px-4 mb-0" style="background: rgba(255, 71, 87, 0.08);">
                                <i class="fas fa-info-circle me-2"></i> You have already approved this phase.
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endif %}
"""

# Regex replacement of the old gate control logic block
# Starting from "<!-- PL Actions: Gate Control & Consolidation -->" down to the matching "{% endif %}" before phase.consolidation_notes
pattern = r"<!-- PL Actions: Gate Control & Consolidation -->.*?{% endif %}\s*(?={% if phase\.consolidation_notes %})"

modified_content = re.sub(pattern, new_gates_html, content, flags=re.DOTALL)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(modified_content)

print("Template patched successfully!")
