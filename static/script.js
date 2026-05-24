// Student Career Advisor Chatbot — Frontend Logic

document.addEventListener("DOMContentLoaded", () => {
    // State management
    let advisorData = null;
    let chatHistory = [];
    let roadmapRenderVersion = 0;
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const btnSend = document.getElementById("btn-send");
    
    // Dashboard States
    const dbEmptyState = document.getElementById("dashboard-empty-state");
    const dbActiveState = document.getElementById("dashboard-active-state");
    
    // Dashboard elements
    const dashRoleName = document.getElementById("dash-role-name");
    const dashSampleCount = document.getElementById("dash-sample-count");
    const dashMedianSalary = document.getElementById("dash-median-salary");
    const dashExp25 = document.getElementById("dash-exp-25");
    const dashExpMed = document.getElementById("dash-exp-med");
    const dashExp75 = document.getElementById("dash-exp-75");
    const dashExpBarFill = document.getElementById("dash-exp-bar-fill");
    const dashExpBarDot = document.getElementById("dash-exp-bar-dot");
    const dashSal25 = document.getElementById("dash-sal-25");
    const dashSalMed = document.getElementById("dash-sal-med");
    const dashSal75 = document.getElementById("dash-sal-75");
    const dashSalBarFill = document.getElementById("dash-sal-bar-fill");
    const dashSalBarDot = document.getElementById("dash-sal-bar-dot");
    const dashLanguages = document.getElementById("dash-languages");
    const dashDatabases = document.getElementById("dash-databases");
    const dashEducation = document.getElementById("dash-education");
    const dashEmployment = document.getElementById("dash-employment");
    const roadmapProgressLabel = document.getElementById("roadmap-progress-label");
    const roadmapDiagram = document.getElementById("roadmap-diagram");
    const roadmapEmpty = document.getElementById("roadmap-empty");
    const roadmapNextStep = document.getElementById("roadmap-next-step");
    const roadmapControls = document.getElementById("roadmap-controls");

    // Modal elements
    const compareModal = document.getElementById("compare-modal");
    const btnOpenCompare = document.getElementById("btn-open-compare");
    const btnCloseCompare = document.getElementById("btn-close-compare");
    const selectRole1 = document.getElementById("select-role-1");
    const selectRole2 = document.getElementById("select-role-2");
    const compareResults = document.getElementById("compare-results");

    // 1. Fetch survey database locally on startup
    fetch("/student_advisor_data.json")
        .then(res => {
            if (!res.ok) throw new Error("Could not load survey data file");
            return res.json();
        })
        .then(data => {
            advisorData = data;
            console.log("[*] Survey database loaded successfully.", data);
            populateSelectors();
        })
        .catch(err => {
            console.error("[!] Error loading survey database:", err);
            // Fallback: If not found at root, try loading from preprocessor static served paths
            fetch("student_advisor_data.json")
                .then(res => res.json())
                .then(data => {
                    advisorData = data;
                    populateSelectors();
                })
                .catch(e => console.error("[!] Deep load fallback failed:", e));
        });

    // Configure marked options
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    if (window.mermaid) {
        mermaid.initialize({
            startOnLoad: false,
            theme: "base",
            securityLevel: "strict",
            flowchart: {
                curve: "basis",
                htmlLabels: false
            },
            themeVariables: {
                background: "transparent",
                primaryColor: "#1f2937",
                primaryTextColor: "#f3f4f6",
                primaryBorderColor: "#4b5563",
                lineColor: "#64748b",
                fontFamily: "Inter, sans-serif"
            }
        });
    }

    // 2. Chat logic
    chatForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const msg = chatInput.value.trim();
        if (!msg) return;

        appendMessage("user", msg);
        chatInput.value = "";
        
        // Show typewriter writing indicator
        const indicator = appendWritingIndicator();

        // Prepare request history
        const payloadHistory = chatHistory.map(turn => ({
            role: turn.role,
            content: turn.content
        }));

        fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: msg,
                history: payloadHistory
            })
        })
        .then(res => res.json())
        .then(data => {
            indicator.remove(); // Remove visual typewriter
            
            if (data.error) {
                appendMessage("system", `Error: ${data.error}`);
            } else {
                appendMessage("system", data.reply);
                
                // If backend detected a career matched role, update the dashboard graphs!
                if (data.matched_role) {
                    highlightChip(data.matched_role);
                    renderActiveDashboard(data.matched_role);
                }
            }
        })
        .catch(err => {
            indicator.remove();
            console.error("[!] Chat error:", err);
            appendMessage("system", "Sorry! I encountered a network error communicating with my advisor backend. Please make sure `app.py` is running locally.");
        });
    });

    // Sidebar suggested chip clicks
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const role = chip.getAttribute("data-role");
            if (!role) return;

            // Update active state class in sidebar
            document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
            chip.classList.add("active");

            // Renders active visual stats
            renderActiveDashboard(role);

            // Ask advisor about the path
            appendMessage("user", `Tell me about the requirements and salary for becoming a ${role}.`);
            
            const indicator = appendWritingIndicator();
            const payloadHistory = chatHistory.map(turn => ({
                role: turn.role,
                content: turn.content
            }));

            fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: `Tell me about the requirements and salary for becoming a ${role}.`,
                    history: payloadHistory
                })
            })
            .then(res => res.json())
            .then(data => {
                indicator.remove();
                if (data.error) {
                    appendMessage("system", `Error: ${data.error}`);
                } else {
                    appendMessage("system", data.reply);
                }
            })
            .catch(err => {
                indicator.remove();
                appendMessage("system", "Sorry! Network issue encountered. Check server console logs.");
            });
        });
    });

    // 3. Dynamic Visual Dashboard Renderer
    function renderActiveDashboard(roleName) {
        if (!advisorData || !advisorData.role_profiles[roleName]) return;
        
        const profile = advisorData.role_profiles[roleName];

        // Toggle visibility state
        dbEmptyState.classList.add("hidden");
        dbActiveState.classList.remove("hidden");

        // Set text items
        dashRoleName.textContent = roleName;
        dashSampleCount.textContent = profile.sample_count.toLocaleString();
        
        const medianSalary = profile.salary.median_usd;
        dashMedianSalary.textContent = medianSalary ? `$${medianSalary.toLocaleString()}` : "N/A";

        // Setup Experience Range bar (scales from 0 to 30 years)
        const exp = profile.experience || {};
        const p25Exp = exp.p25_years || 0;
        const medExp = exp.median_years || 0;
        const p75Exp = exp.p75_years || 0;
        
        dashExp25.textContent = p25Exp;
        dashExpMed.textContent = medExp;
        dashExp75.textContent = p75Exp;

        // Visual ratios (capping at max 30 yrs for visually pleasant display)
        const leftPercentExp = Math.min((p25Exp / 30) * 100, 100);
        const rightPercentExp = Math.min(((p75Exp - p25Exp) / 30) * 100, 100);
        const medPercentExp = Math.min((medExp / 30) * 100, 100);

        dashExpBarFill.style.left = `${leftPercentExp}%`;
        dashExpBarFill.style.width = `${rightPercentExp}%`;
        dashExpBarDot.style.left = `${medPercentExp}%`;

        // Setup Salary Distribution Gauge (scales from $0 to $250,000/yr)
        const sal = profile.salary || {};
        const p25Sal = sal.p25_usd || 0;
        const medSal = sal.median_usd || 0;
        const p75Sal = sal.p75_usd || 0;

        dashSal25.textContent = p25Sal ? `$${p25Sal.toLocaleString()}` : "N/A";
        dashSalMed.textContent = medSal ? `$${medSal.toLocaleString()}` : "N/A";
        dashSal75.textContent = p75Sal ? `$${p75Sal.toLocaleString()}` : "N/A";

        const maxScaleSal = 220000;
        const leftPercentSal = Math.min((p25Sal / maxScaleSal) * 100, 100);
        const rightPercentSal = Math.min(((p75Sal - p25Sal) / maxScaleSal) * 100, 100);
        const medPercentSal = Math.min((medSal / maxScaleSal) * 100, 100);

        dashSalBarFill.style.left = `${leftPercentSal}%`;
        dashSalBarFill.style.width = `${rightPercentSal}%`;
        dashSalBarDot.style.left = `${medPercentSal}%`;

        // Draw Language progress bars
        dashLanguages.innerHTML = "";
        const maxLangsCount = profile.languages[0] ? profile.languages[0].count : 1;
        profile.languages.slice(0, 5).forEach(lang => {
            const pct = Math.round((lang.count / profile.sample_count) * 100);
            const fillWidth = Math.round((lang.count / maxLangsCount) * 100);
            
            dashLanguages.appendChild(createProgressBar(lang.name, `${pct}%`, fillWidth));
        });

        // Draw Databases progress bars
        dashDatabases.innerHTML = "";
        const maxDbCount = profile.databases[0] ? profile.databases[0].count : 1;
        profile.databases.slice(0, 5).forEach(db => {
            const pct = Math.round((db.count / profile.sample_count) * 100);
            const fillWidth = Math.round((db.count / maxDbCount) * 100);
            
            dashDatabases.appendChild(createProgressBar(db.name, `${pct}%`, fillWidth));
        });

        // Draw Education background bars
        dashEducation.innerHTML = "";
        const eduTotal = Object.values(profile.education).reduce((a, b) => a + b, 0);
        const sortedEdu = Object.entries(profile.education).sort((a, b) => b[1] - a[1]).slice(0, 3);
        const maxEduCount = sortedEdu[0] ? sortedEdu[1] : 1;
        
        sortedEdu.forEach(([degree, count]) => {
            const pct = Math.round((count / eduTotal) * 100);
            dashEducation.appendChild(createListStatBar(degree, `${pct}%`, pct));
        });

        // Draw Employment split bars
        dashEmployment.innerHTML = "";
        const empTotal = Object.values(profile.employment).reduce((a, b) => a + b, 0);
        const sortedEmp = Object.entries(profile.employment).sort((a, b) => b[1] - a[1]).slice(0, 3);
        
        sortedEmp.forEach(([type, count]) => {
            const pct = Math.round((count / empTotal) * 100);
            dashEmployment.appendChild(createListStatBar(type, `${pct}%`, pct));
        });

        renderRoadmap(roleName);
    }

    function renderRoadmap(roleName) {
        if (!advisorData || !advisorData.role_profiles[roleName]) return;

        const profile = advisorData.role_profiles[roleName];
        const skills = buildRoadmapSkills(profile);

        if (!skills.length) {
            roadmapDiagram.innerHTML = "";
            roadmapControls.innerHTML = "";
            roadmapNextStep.textContent = "Roadmap data is not available for this role yet.";
            roadmapProgressLabel.textContent = "0%";
            roadmapEmpty.classList.remove("hidden");
            return;
        }

        roadmapEmpty.classList.add("hidden");
        const progress = loadRoadmapProgress(roleName, skills);
        renderRoadmapAssessment(roleName, skills, progress);
        renderRoadmapDiagram(roleName, skills, progress);
    }

    function buildRoadmapSkills(profile) {
        const skillGroups = [
            { source: profile.languages, limit: 2, category: "Language" },
            { source: profile.databases, limit: 1, category: "Database" },
            { source: profile.frameworks, limit: 2, category: "Framework" },
            { source: profile.platforms, limit: 2, category: "Tool" }
        ];
        const seen = new Set();
        const skills = [];

        skillGroups.forEach(group => {
            (group.source || []).slice(0, group.limit).forEach(item => {
                const name = normalizeSkillName(item && item.name);
                const key = name.toLowerCase();
                if (!name || seen.has(key) || skills.length >= 6) return;
                seen.add(key);
                skills.push({
                    id: `skill-${skills.length}`,
                    name,
                    category: group.category
                });
            });
        });

        return skills;
    }

    function renderRoadmapAssessment(roleName, skills, progress) {
        updateRoadmapSummary(skills, progress);
        roadmapControls.innerHTML = "";

        skills.forEach(skill => {
            const value = clampProgress(progress[skill.name] || 0);
            const item = document.createElement("div");
            item.className = "roadmap-control";
            item.innerHTML = `
                <div class="roadmap-control-top">
                    <label for="${skill.id}">How confident are you with ${escapeHTML(skill.name)}?</label>
                    <span class="roadmap-value">${value}%</span>
                </div>
                <input id="${skill.id}" type="range" min="0" max="100" step="5" value="${value}" data-skill="${escapeHTML(skill.name)}">
            `;

            const input = item.querySelector("input");
            const valueLabel = item.querySelector(".roadmap-value");
            input.addEventListener("input", () => {
                const nextValue = clampProgress(input.value);
                progress[skill.name] = nextValue;
                valueLabel.textContent = `${nextValue}%`;
                saveRoadmapProgress(roleName, progress);
                updateRoadmapSummary(skills, progress);
                renderRoadmapDiagram(roleName, skills, progress);
            });

            roadmapControls.appendChild(item);
        });
    }

    function updateRoadmapSummary(skills, progress) {
        const average = calculateAverageProgress(skills, progress);
        const nextSkill = getNextRoadmapSkill(skills, progress);

        roadmapProgressLabel.textContent = `${average}%`;
        roadmapNextStep.innerHTML = nextSkill
            ? `<strong>Next priority:</strong> ${escapeHTML(nextSkill.name)}`
            : `<strong>Track ready:</strong> You marked every roadmap skill at 80% or higher.`;
    }

    function renderRoadmapDiagram(roleName, skills, progress) {
        if (!window.mermaid) {
            roadmapDiagram.innerHTML = createFallbackRoadmapList(skills, progress);
            return;
        }

        roadmapRenderVersion += 1;
        const currentRenderVersion = roadmapRenderVersion;
        const diagramId = `roadmap-${safeId(roleName)}-${Date.now()}`;
        const chart = createMermaidRoadmap(skills, progress);
        roadmapDiagram.innerHTML = "";

        mermaid.render(diagramId, chart)
            .then(({ svg }) => {
                if (currentRenderVersion !== roadmapRenderVersion) return;
                roadmapDiagram.innerHTML = svg;
            })
            .catch(err => {
                if (currentRenderVersion !== roadmapRenderVersion) return;
                console.error("[!] Mermaid roadmap render failed:", err);
                roadmapDiagram.innerHTML = createFallbackRoadmapList(skills, progress);
            });
    }

    function createMermaidRoadmap(skills, progress) {
        const lines = [
            "flowchart LR",
            "classDef mastered fill:#065f46,stroke:#10b981,color:#ecfdf5,stroke-width:2px;",
            "classDef learning fill:#164e63,stroke:#06b6d4,color:#ecfeff,stroke-width:2px;",
            "classDef next fill:#78350f,stroke:#f59e0b,color:#fff7ed,stroke-width:3px;",
            "classDef pending fill:#111827,stroke:#475569,color:#cbd5e1,stroke-width:1px;"
        ];

        skills.forEach((skill, index) => {
            lines.push(`n${index}["${escapeMermaidLabel(skill.name)}"]`);
            if (index > 0) lines.push(`n${index - 1} --> n${index}`);
        });

        skills.forEach((skill, index) => {
            lines.push(`class n${index} ${getRoadmapStatus(skill, skills, progress)};`);
        });

        return lines.join("\n");
    }

    function createFallbackRoadmapList(skills, progress) {
        const items = skills.map(skill => {
            const status = getRoadmapStatus(skill, skills, progress);
            return `<li class="roadmap-fallback-${status}">${escapeHTML(skill.name)}</li>`;
        }).join("");

        return `<ol class="roadmap-fallback-list">${items}</ol>`;
    }

    function getRoadmapStatus(skill, skills, progress) {
        const value = clampProgress(progress[skill.name] || 0);
        const nextSkill = getNextRoadmapSkill(skills, progress);

        if (value >= 80) return "mastered";
        if (nextSkill && nextSkill.name === skill.name) return "next";
        if (value >= 40) return "learning";
        return "pending";
    }

    function getNextRoadmapSkill(skills, progress) {
        return skills.find(skill => clampProgress(progress[skill.name] || 0) < 80) || null;
    }

    function calculateAverageProgress(skills, progress) {
        if (!skills.length) return 0;
        const total = skills.reduce((sum, skill) => sum + clampProgress(progress[skill.name] || 0), 0);
        return Math.round(total / skills.length);
    }

    function loadRoadmapProgress(roleName, skills) {
        const saved = localStorage.getItem(getRoadmapStorageKey(roleName));
        let progress = {};

        if (saved) {
            try {
                progress = JSON.parse(saved) || {};
            } catch (err) {
                progress = {};
            }
        }

        skills.forEach(skill => {
            progress[skill.name] = clampProgress(progress[skill.name] || 0);
        });

        return progress;
    }

    function saveRoadmapProgress(roleName, progress) {
        localStorage.setItem(getRoadmapStorageKey(roleName), JSON.stringify(progress));
    }

    function getRoadmapStorageKey(roleName) {
        return `student-advisor-roadmap:${roleName}`;
    }

    function normalizeSkillName(name) {
        return String(name || "")
            .replace(/\s+/g, " ")
            .trim();
    }

    function clampProgress(value) {
        const parsed = Number(value);
        if (Number.isNaN(parsed)) return 0;
        return Math.max(0, Math.min(100, parsed));
    }

    function safeId(value) {
        return String(value || "role").toLowerCase().replace(/[^a-z0-9]+/g, "-");
    }

    function escapeMermaidLabel(value) {
        return String(value || "")
            .replace(/\\/g, "\\\\")
            .replace(/"/g, "&quot;")
            .replace(/\[/g, "(")
            .replace(/\]/g, ")");
    }

    function createProgressBar(name, textPct, barWidthPct) {
        const item = document.createElement("div");
        item.className = "progress-item";
        item.innerHTML = `
            <div class="progress-info">
                <span class="name">${name}</span>
                <span class="percent">${textPct}</span>
            </div>
            <div class="progress-track">
                <div class="progress-fill" style="width: 0%"></div>
            </div>
        `;
        // Animate width after element insertion into the DOM
        setTimeout(() => {
            const fill = item.querySelector(".progress-fill");
            if (fill) fill.style.width = `${barWidthPct}%`;
        }, 100);
        return item;
    }

    function createListStatBar(name, textPct, barWidthPct) {
        const item = document.createElement("div");
        item.className = "list-item-bar";
        
        // Clean long names
        let cleanName = name.replace("degree", "").replace("Bachelor's", "Bachelors").replace("Master's", "Masters").trim();
        if (cleanName.length > 25) cleanName = cleanName.substring(0, 22) + "...";
        
        item.innerHTML = `
            <div class="list-item-info">
                <span class="lbl" title="${name}">${cleanName}</span>
                <span class="val">${textPct}</span>
            </div>
            <div class="item-track">
                <div class="item-fill" style="width: 0%"></div>
            </div>
        `;
        setTimeout(() => {
            const fill = item.querySelector(".item-fill");
            if (fill) fill.style.width = `${barWidthPct}%`;
        }, 100);
        return item;
    }

    function highlightChip(roleName) {
        document.querySelectorAll(".chip").forEach(chip => {
            if (chip.getAttribute("data-role") === roleName) {
                chip.classList.add("active");
            } else {
                chip.classList.remove("active");
            }
        });
    }

    // Append Message helper
    function appendMessage(role, text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${role}`;
        
        const isSystem = role === "system";
        const icon = isSystem ? "fa-user-tie" : "fa-user";
        
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid ${icon}"></i></div>
            <div class="bubble">
                ${isSystem ? marked.parse(text) : `<p>${escapeHTML(text)}</p>`}
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // Keep local message state for histories
        chatHistory.push({ role, content: text });
    }

    // Typewriter writing indicator bubble
    function appendWritingIndicator() {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message system";
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-user-tie"></i></div>
            <div class="bubble writing-bubble">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    function escapeHTML(str) {
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }

    // 4. Modal (Side-by-Side Comparison) Logic
    function populateSelectors() {
        if (!advisorData) return;
        const roles = Object.keys(advisorData.role_profiles).sort();
        
        // Clear options
        selectRole1.innerHTML = '<option value="" disabled selected>Select a career...</option>';
        selectRole2.innerHTML = '<option value="" disabled selected>Select a career...</option>';

        roles.forEach(role => {
            const opt1 = document.createElement("option");
            opt1.value = role;
            opt1.textContent = role;
            selectRole1.appendChild(opt1);

            const opt2 = document.createElement("option");
            opt2.value = role;
            opt2.textContent = role;
            selectRole2.appendChild(opt2);
        });
    }

    btnOpenCompare.addEventListener("click", () => {
        compareModal.classList.remove("hidden");
    });

    btnCloseCompare.addEventListener("click", () => {
        compareModal.classList.add("hidden");
    });

    // Close on click overlay
    document.querySelector(".modal-overlay").addEventListener("click", () => {
        compareModal.classList.add("hidden");
    });

    selectRole1.addEventListener("change", performComparison);
    selectRole2.addEventListener("change", performComparison);

    function performComparison() {
        const roleA = selectRole1.value;
        const roleB = selectRole2.value;

        if (!roleA || !roleB) return;
        
        if (roleA === roleB) {
            compareResults.innerHTML = `
                <div class="compare-placeholder" style="color: #ef4444;">
                    <i class="fa-solid fa-triangle-exclamation" style="font-size: 24px; margin-bottom: 12px; display: block;"></i>
                    Please select two different developer roles to compare.
                </div>
            `;
            return;
        }

        const pA = advisorData.role_profiles[roleA];
        const pB = advisorData.role_profiles[roleB];

        if (!pA || !pB) return;

        // Render clean comparative Grid layout
        compareResults.innerHTML = `
            <div class="comparison-grid">
                <div class="comp-header-cell">Metric</div>
                <div class="comp-header-cell" style="color: var(--accent-indigo);">${roleA}</div>
                <div class="comp-header-cell" style="color: var(--accent-cyan);">${roleB}</div>
                
                <!-- Section: Summary -->
                <div class="comp-row-title">Overview</div>
                <div class="comp-label-cell">Respondents Sample</div>
                <div class="comp-val-cell">${pA.sample_count.toLocaleString()}</div>
                <div class="comp-val-cell">${pB.sample_count.toLocaleString()}</div>
                
                <!-- Section: Salaries -->
                <div class="comp-row-title">Annual Salary (USD)</div>
                <div class="comp-label-cell">Median Salary</div>
                <div class="comp-val-cell" style="color: #10b981; font-weight: 700;">$${pA.salary.median_usd.toLocaleString()}</div>
                <div class="comp-val-cell" style="color: #10b981; font-weight: 700;">$${pB.salary.median_usd.toLocaleString()}</div>
                
                <div class="comp-label-cell">Low Range (25th %)</div>
                <div class="comp-val-cell">$${pA.salary.p25_usd.toLocaleString()}</div>
                <div class="comp-val-cell">$${pB.salary.p25_usd.toLocaleString()}</div>

                <div class="comp-label-cell">High Range (75th %)</div>
                <div class="comp-val-cell">$${pA.salary.p75_usd.toLocaleString()}</div>
                <div class="comp-val-cell">$${pB.salary.p75_usd.toLocaleString()}</div>

                <!-- Section: Experience -->
                <div class="comp-row-title">Experience Profile</div>
                <div class="comp-label-cell">Median Coding Experience</div>
                <div class="comp-val-cell">${pA.experience.median_years} years</div>
                <div class="comp-val-cell">${pB.experience.median_years} years</div>

                <!-- Section: Technology -->
                <div class="comp-row-title">Popular Languages</div>
                <div class="comp-label-cell">Top Tech Languages</div>
                <div class="comp-val-cell">
                    <div class="comp-skills-list">
                        ${pA.languages.slice(0, 4).map(l => `<span class="comp-skill-tag">${l.name}</span>`).join("")}
                    </div>
                </div>
                <div class="comp-val-cell">
                    <div class="comp-skills-list">
                        ${pB.languages.slice(0, 4).map(l => `<span class="comp-skill-tag">${l.name}</span>`).join("")}
                    </div>
                </div>

                <div class="comp-row-title">Popular Web Frameworks</div>
                <div class="comp-label-cell">Top Web Frameworks</div>
                <div class="comp-val-cell">
                    <div class="comp-skills-list">
                        ${pA.frameworks.slice(0, 3).map(f => `<span class="comp-skill-tag">${f.name}</span>`).join("")}
                    </div>
                </div>
                <div class="comp-val-cell">
                    <div class="comp-skills-list">
                        ${pB.frameworks.slice(0, 3).map(f => `<span class="comp-skill-tag">${f.name}</span>`).join("")}
                    </div>
                </div>
            </div>
        `;
    }
});
