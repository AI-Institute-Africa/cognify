filepath = r"c:\Users\USER 2\Downloads\project1\project1\land_registry\registry\templates\governance\project_detail.html"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "<!-- PL Actions: Gate Control & Consolidation -->"
end_marker = "{% if phase.consolidation_notes %}"

s1 = content.find(start_marker)
s2 = content.find(end_marker)

if s1 != -1 and s2 != -1:
    # Need to find the last {% endif %} before end_marker
    block_before = content[:s2]
    last_endif_pos = block_before.rfind("{% endif %}")
    
    if last_endif_pos != -1 and last_endif_pos > s1:
        # Include the {% endif %} in the removed section
        end_pos = last_endif_pos + len("{% endif %}")
        
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
                                    <i class="fas fa-paper-plane me-2"></i> Submit Phase
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
        removals = content[s1:end_pos]
        modified_content = content.replace(removals, new_gates_html)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        print("REPLACED EXACT BLOCK WITH SLICE METHOD")
    else:
        print("COULD NOT FIND ENDIF")
else:
    print(f"COULD NOT FIND MARKERS {s1} {s2}")
