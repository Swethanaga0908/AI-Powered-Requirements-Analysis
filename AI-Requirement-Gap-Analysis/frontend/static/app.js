const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

let currentUser = localStorage.getItem('reqNova_current_user') || null;

let state = {
    analyses: [],
    current: null
};


// =========================================================
// USER-SPECIFIC STORAGE
// =========================================================

function storageKey() {
    return `reqNova_analyses_${currentUser}`;
}

function loadUserData() {
    if (!currentUser) {
        state.analyses = [];
        return;
    }

    state.analyses = JSON.parse(
        localStorage.getItem(storageKey()) || '[]'
    );
}

function save() {
    if (!currentUser) return;

    localStorage.setItem(
        storageKey(),
        JSON.stringify(state.analyses)
    );
}


// =========================================================
// TOAST
// =========================================================

function toast(msg) {
    let t = $('#toast');

    t.textContent = msg;
    t.classList.add('show');

    setTimeout(() => {
        t.classList.remove('show');
    }, 2200);
}


// =========================================================
// PAGE NAVIGATION
// =========================================================

function showPage(name) {

    $$('.page').forEach(x => {
        x.classList.add('hidden');
    });

    $('#' + name + 'Page').classList.remove('hidden');

    $('#pageTitle').textContent =
        name === 'new'
            ? 'New analysis'
            : name[0].toUpperCase() + name.slice(1);

    $$('.nav[data-page]').forEach(x => {
        x.classList.toggle(
            'active',
            x.dataset.page === name
        );
    });

    if (name === 'dashboard') {
        renderDashboard();
    }

    if (name === 'history') {
        renderHistory();
    }

    if (name === 'reports') {
        renderReports();
    }
}


// =========================================================
// DASHBOARD
// =========================================================

function renderDashboard() {

    let a = state.analyses;

    $('#projectCount').textContent = a.length;

    $('#analysisCount').textContent = a.length;

    $('#gapCount').textContent = a.reduce(
        (n, x) =>
            n +
            (
                x.summary
                    ? Object.values(x.summary).reduce(
                        (s, v) => s + v,
                        0
                    )
                    : 0
            ),
        0
    );

    $('#avgScore').textContent =
        a.length
            ? Math.round(
                a.reduce((n, x) => n + x.score, 0) / a.length
            )
            : '—';

    $('#recent').innerHTML =
        a.slice(0, 3).map(card).join('') ||
        '<div class="panel"><p>No analyses yet. Start your first one.</p></div>';
}


// =========================================================
// ANALYSIS CARD
// =========================================================

function card(x) {

    return `
        <div class="analysis-card">
            <span class="score">${x.score}/100</span>
            <strong>${esc(x.project)}</strong>
            <p class="muted" style="margin-top:8px">
                ${x.requirement_count} requirements · ${x.grade}
            </p>
        </div>
    `;
}


// =========================================================
// HISTORY
// =========================================================

function renderHistory() {

    $('#historyList').innerHTML =
        state.analyses.map((x, i) => `
            <div class="analysis-card" style="margin:10px 0">
                <span class="score">${x.score}/100</span>

                <strong>${esc(x.project)}</strong>

                <p class="muted">
                    ${x.requirement_count} requirements · ${x.grade}
                </p>

                <button
                    class="text-btn"
                    onclick="openSaved(${i})"
                >
                    View analysis →
                </button>
            </div>
        `).join('') ||
        '<p class="muted">No saved analyses.</p>';
}


// =========================================================
// REPORTS
// =========================================================

function renderReports() {

    $('#reportList').innerHTML =
        state.analyses.map(x => `
            <div class="analysis-card" style="margin:10px 0">
                <strong>${esc(x.project)}</strong>

                <p class="muted">
                    Score ${x.score}/100 ·
                    ${x.requirement_count} requirements
                </p>
            </div>
        `).join('') ||
        '<p class="muted">No reports yet.</p>';
}


// =========================================================
// ESCAPE HTML
// =========================================================

function esc(s) {

    return String(s || '').replace(
        /[&<>"']/g,
        c => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[c])
    );
}


// =========================================================
// RESULT PAGE
// =========================================================

function renderResult(r) {

    state.current = r;

    showPage('results');

    $('#resultHeader').innerHTML = `
        <div class="section-head">
            <div>
                <span class="eyebrow">
                    ANALYSIS RESULT
                </span>

                <h2 style="font:700 25px 'Space Grotesk';margin:5px 0">
                    ${esc(r.project)}
                </h2>

                <p>
                    ${r.requirement_count} requirements reviewed
                </p>
            </div>

            <button
                class="secondary"
                onclick="showPage('new')"
            >
                ← New analysis
            </button>
        </div>
    `;

    $('#scoreValue').textContent = r.score;

    $('#scoreGrade').textContent = r.grade;

    let deg = r.score * 3.6;

    $('#scoreRing').style.background =
        `conic-gradient(#5c7c68 ${deg}deg,#e7ede9 ${deg}deg)`;


    let labels = [
        ['Missing', r.summary.missing],
        ['Ambiguous', r.summary.ambiguous],
        ['Incomplete', r.summary.incomplete],
        ['Conflicts', r.summary.conflicts],
        ['Edge cases', r.summary.edge_cases],
        ['Security', r.summary.security],
        ['Acceptance', r.summary.acceptance]
    ];

    $('#gapSummary').innerHTML =
        labels.map(x => `
            <div class="gap-item">
                <b>${x[1]}</b>
                <span>${x[0]}</span>
            </div>
        `).join('');


    let groups = [
        ['Missing', r.missing],
        ['Ambiguous', r.ambiguous],
        ['Incomplete', r.incomplete],
        ['Conflicts', r.conflicts],
        ['Edge case', r.edge_cases],
        ['Security', r.security_gaps],
        ['Acceptance', r.acceptance_gaps]
    ];

    $('#issueList').innerHTML =
        groups
            .flatMap(g =>
                g[1].map(v => `
                    <div class="issue">
                        <span class="tag">${g[0]}</span>

                        <p>
                            <b>
                                ${esc(
                                    v.requirement ||
                                    v.area ||
                                    'Potential conflict'
                                )}
                            </b>

                            <br>

                            ${esc(v.reason)}
                        </p>
                    </div>
                `)
            )
            .join('') ||
        '<p class="muted">No significant gaps detected.</p>';


    $('#questions').innerHTML =
        (r.questions || [])
            .map(q => `
                <div class="question">
                    ? ${esc(q)}
                </div>
            `)
            .join('') ||
        '<p class="muted">No clarification questions generated.</p>';
}


// =========================================================
// ANALYZE
// =========================================================

async function analyze() {

    let req = $('#requirements').value.trim();

    if (!req) {
        return toast('Add some requirements first.');
    }

    $('#analyzeBtn').disabled = true;

    $('#analyzeBtn').textContent =
        'Analyzing…';

    try {

        let res = await fetch(
            '/api/analyze',
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title:
                        $('#projectName').value.trim() ||
                        'Untitled Project',

                    requirements: req
                })
            }
        );

        let data = await res.json();

        if (!res.ok) {
            throw Error(
                data.detail ||
                'Analysis failed'
            );
        }


        // Save only for current logged-in user
        state.analyses.unshift(data);

        state.analyses =
            state.analyses.slice(0, 30);

        save();

        renderResult(data);

        toast('Analysis complete');

    } catch (e) {

        toast(e.message);

    } finally {

        $('#analyzeBtn').disabled = false;

        $('#analyzeBtn').textContent =
            'Analyze requirements ✦';
    }
}


// =========================================================
// OPEN SAVED ANALYSIS
// =========================================================

function openSaved(i) {

    renderResult(
        state.analyses[i]
    );
}


// =========================================================
// LOGIN
// =========================================================

$('#loginForm').addEventListener(
    'submit',
    e => {

        e.preventDefault();

        let email =
            $('#email').value
                .trim()
                .toLowerCase();

        if (!email) {
            return toast('Enter your email.');
        }


        // Store current logged-in user
        currentUser = email;

        localStorage.setItem(
            'reqNova_current_user',
            currentUser
        );


        // Load only this user's history
        loadUserData();


        $('#auth').classList.add('hidden');

        $('#app').classList.remove('hidden');


        $('#userAvatar').textContent =
            email[0].toUpperCase();


        showPage('dashboard');

        toast(`Welcome back, ${email}`);
    }
);


// =========================================================
// LOGOUT
// =========================================================

$('#logout').onclick = () => {

    // Clear current session only
    localStorage.removeItem(
        'reqNova_current_user'
    );

    currentUser = null;

    state = {
        analyses: [],
        current: null
    };

    // Reload login screen
    location.reload();
};


// =========================================================
// ANALYZE BUTTON
// =========================================================

$('#analyzeBtn').onclick = analyze;


// =========================================================
// WORD COUNT
// =========================================================

$('#requirements').oninput = () => {

    let words =
        $('#requirements')
            .value
            .trim()
            .match(/\S+/g) || [];

    $('#wordCount').textContent =
        words.length + ' words';
};


// =========================================================
// FILE UPLOAD
// =========================================================

$('#fileInput').onchange = async e => {

    let f = e.target.files[0];

    if (!f) return;

    let fd = new FormData();

    fd.append('file', f);

    try {

        let r = await fetch(
            '/api/upload',
            {
                method: 'POST',
                body: fd
            }
        );

        let d = await r.json();

        if (!r.ok) {
            throw Error(d.detail);
        }

        $('#requirements').value =
            d.text;

        $('#wordCount').textContent =
            (
                d.text
                    .trim()
                    .match(/\S+/g) || []
            ).length + ' words';

        toast('File loaded');

    } catch (err) {

        toast(err.message);
    }
};


// =========================================================
// NAVIGATION BUTTONS
// =========================================================

$$('[data-go]').forEach(
    b =>
        b.onclick = () =>
            showPage(b.dataset.go)
);


$$('.nav[data-page]').forEach(
    b =>
        b.onclick = () =>
            showPage(b.dataset.page)
);


// =========================================================
// REPORT DOWNLOAD
// =========================================================

$('#reportBtn').onclick = () => {

    if (!state.current) return;

    let blob = new Blob(
        [
            JSON.stringify(
                state.current,
                null,
                2
            )
        ],
        {
            type: 'application/json'
        }
    );

    let a =
        document.createElement('a');

    a.href =
        URL.createObjectURL(blob);

    a.download =
        (
            state.current.project ||
            'requirement-report'
        ).replace(/\W+/g, '-') +
        '.json';

    a.click();

    toast('Report downloaded');
};


// =========================================================
// INITIALIZE
// =========================================================

if (currentUser) {

    loadUserData();

    $('#auth').classList.add('hidden');

    $('#app').classList.remove('hidden');

    $('#userAvatar').textContent =
        currentUser[0].toUpperCase();

    showPage('dashboard');

} else {

    $('#auth').classList.remove('hidden');

    $('#app').classList.add('hidden');
}