#!/usr/bin/env python3
"""Sqlantra Interactive Web Demo V2 - Real System with Ollama, Context Memory, and DB."""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sqlantra_database_v2 as db
import text_to_sql
import context_memory
import hitl_workflow
import llm_client

db.init_database()

OLLAMA_URL = llm_client.OLLAMA_URL
MODEL = llm_client.OLLAMA_MODEL

PORT = 8766

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sqlantra System - Real AI-Powered Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #0a0a0f; --surface: #12121a; --surface-el: #1a1a24; --surface-el2: #222230;
            --border: #2a2a3a; --user: #ff4757; --sqlantra: #00d4ff; --db: #2ed573;
            --data: #a55afe; --gold: #ffd43b; --text: #ffffff; --text-dim: #8888aa;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
        body::before { content: ''; position: fixed; inset: 0; background: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px); background-size: 50px 50px; pointer-events: none; }
        .app { position: relative; z-index: 1; display: flex; flex-direction: column; min-height: 100vh; }
        header { background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; }
        .logo { display: flex; align-items: center; gap: 12px; }
        .logo-icon { width: 40px; height: 40px; background: linear-gradient(135deg, var(--sqlantra), var(--data)); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .logo-text { font-size: 22px; font-weight: 700; background: linear-gradient(90deg, var(--sqlantra), var(--user)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .controls { padding: 16px 32px; display: flex; gap: 12px; background: var(--surface); border-bottom: 1px solid var(--border); flex-wrap: wrap; }
        button { padding: 10px 20px; border: none; border-radius: 8px; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; }
        .btn-reset { background: var(--user); color: white; }
        .btn-reset:hover { background: #ff6b7a; }
        .btn-demo { background: var(--sqlantra); color: var(--bg); }
        .btn-demo:hover { background: #33ddff; }
        .panels { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px 32px; flex: 1; overflow: hidden; }
        .panel { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; max-height: calc(50vh - 80px); }
        .panel-header { padding: 12px 16px; display: flex; align-items: center; gap: 10px; border-bottom: 1px solid var(--border); background: var(--surface-el); }
        .panel-icon { width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; }
        .panel-user .panel-icon { background: var(--user); }
        .panel-sqlantra .panel-icon { background: var(--sqlantra); color: var(--bg); }
        .panel-db .panel-icon { background: var(--db); color: var(--bg); }
        .panel-memory .panel-icon { background: var(--gold); color: var(--bg); }
        .panel-title { font-size: 14px; font-weight: 600; }
        .panel-subtitle { font-size: 11px; color: var(--text-dim); margin-left: auto; }
        .panel-content { flex: 1; padding: 12px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 11px; line-height: 1.5; }
        .log-line { padding: 4px 8px; margin: 2px 0; border-radius: 4px; background: rgba(255,255,255,0.02); word-break: break-word; }
        .log-line.user { border-left: 3px solid var(--user); }
        .log-line.sqlantra { border-left: 3px solid var(--sqlantra); }
        .log-line.db { border-left: 3px solid var(--db); }
        .log-line.memory { border-left: 3px solid var(--gold); }
        .log-line.success { color: var(--sqlantra); }
        .log-line.dim { color: var(--text-dim); }
        .log-line.warning { color: var(--gold); }
        .log-line.error { color: var(--user); }
        .log-section { margin: 12px 0; padding: 8px; background: var(--surface-el); border-radius: 8px; }
        .log-section-title { font-weight: 600; color: var(--sqlantra); margin-bottom: 8px; }
        
        /* User Input Panel */
        .input-area { margin-bottom: 12px; }
        .input-area textarea { width: 100%; padding: 12px; background: var(--surface-el); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-family: 'JetBrains Mono', monospace; font-size: 12px; resize: vertical; min-height: 80px; }
        .input-area textarea:focus { outline: none; border-color: var(--sqlantra); }
        .send-btn { background: var(--sqlantra); color: var(--bg); padding: 10px 24px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; margin-top: 8px; }
        .send-btn:hover { background: #33ddff; }
        
        /* HITL Approval Section */
        .hitl-section { margin-top: 16px; padding: 12px; background: var(--surface-el2); border-radius: 8px; border: 1px solid var(--border); }
        .hitl-title { font-weight: 600; color: var(--gold); margin-bottom: 8px; }
        .hitl-item { padding: 10px; background: var(--surface-el); border-radius: 6px; margin-bottom: 8px; }
        .hitl-item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .hitl-badge { padding: 2px 8px; background: var(--gold); color: var(--bg); border-radius: 4px; font-size: 10px; font-weight: 600; }
        .hitl-details { font-size: 11px; color: var(--text-dim); margin-bottom: 8px; }
        .hitl-actions { display: flex; gap: 8px; }
        .btn-approve { background: var(--db); color: var(--bg); flex: 1; }
        .btn-reject { background: var(--user); color: white; flex: 1; }
        .btn-approve:hover { background: #5aff9e; }
        .btn-reject:hover { background: #ff6b7a; }
        
        /* Database Tables */
        .db-table-select { padding: 8px 12px; background: var(--surface-el); border: 1px solid var(--border); border-radius: 6px; color: var(--text); font-size: 12px; margin-bottom: 8px; width: 100%; }
        .db-table-select:focus { outline: none; border-color: var(--sqlantra); }
        .db-table-select option { background: var(--surface-el); color: var(--text); }
        .db-table { width: 100%; border-collapse: collapse; font-size: 10px; }
        .db-table th { background: var(--surface-el); padding: 6px 8px; text-align: left; border: 1px solid var(--border); font-weight: 600; }
        .db-table td { padding: 4px 8px; border: 1px solid var(--border); max-width: 150px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .db-table tr:hover { background: var(--surface-el); }
        .db-table-highlight { animation: tableHighlight 1s ease-out; }
        @keyframes tableHighlight { 0% { background: rgba(0, 212, 255, 0.3); } 100% { background: transparent; } }
        
        /* Context Memory */
        .memory-empty { color: var(--text-dim); font-style: italic; text-align: center; padding: 20px; }
        .memory-item { padding: 8px; background: var(--surface-el); border-radius: 6px; margin-bottom: 8px; }
        .memory-item.highlight { animation: memoryHighlight 1.5s ease-out; border: 1px solid var(--gold); }
        @keyframes memoryHighlight { 0% { background: rgba(255, 212, 59, 0.4); } 100% { background: var(--surface-el); } }
        .memory-item-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
        .memory-key { font-weight: 600; color: var(--sqlantra); }
        .memory-time { font-size: 10px; color: var(--text-dim); }
        .memory-op { font-size: 10px; padding: 2px 6px; background: var(--surface-el2); border-radius: 3px; color: var(--gold); }
        .memory-value { font-size: 11px; color: var(--text-dim); word-break: break-all; }
        
        /* Sqlantra Workflow Panel */
        .sqlantra-step { padding: 10px; background: var(--surface-el); border-radius: 8px; margin-bottom: 8px; border-left: 3px solid var(--sqlantra); }
        .sqlantra-step-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
        .sqlantra-step-num { width: 24px; height: 24px; background: var(--sqlantra); color: var(--bg); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 600; }
        .sqlantra-step-title { font-weight: 600; color: var(--text); }
        .sqlantra-step-detail { font-size: 11px; color: var(--text-dim); padding-left: 32px; }
        .sqlantra-step.active { border-left: 3px solid var(--gold); background: rgba(255, 212, 59, 0.1); animation: pulse 1s infinite; }
        .sqlantra-step.waiting { border-left: 3px dashed var(--gold); opacity: 0.7; }
        .step-hint { position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%); background: var(--gold); color: var(--bg); padding: 12px 24px; border-radius: 8px; font-weight: 600; z-index: 1000; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(255, 212, 59, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 212, 59, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 212, 59, 0); } }
        .sqlantra-code { background: var(--surface-el2); padding: 8px; border-radius: 6px; font-size: 10px; margin-top: 6px; word-break: break-all; }
        .sqlantra-ollama { color: var(--gold); }
        .sqlantra-success { color: var(--db); }
        .sqlantra-error { color: var(--user); }
        
        footer { padding: 12px 32px; background: var(--surface); border-top: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 12px; color: var(--text-dim); }
        .footer-status { display: flex; gap: 16px; }
        .footer-item { display: flex; align-items: center; gap: 6px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; }
        .status-dot.green { background: var(--db); }
        .status-dot.yellow { background: var(--gold); }
        .status-dot.blue { background: var(--sqlantra); }
    </style>
</head>
<body>
<div class="app">
    <header>
        <div class="logo">
            <div class="logo-icon">🤖</div>
            <div class="logo-text">Sqlantra System V2</div>
        </div>
        <div class="status-badge">Real AI-Powered Enterprise System</div>
    </header>
    
    <div class="controls">
        <button class="btn-reset" onclick="resetSystem()">🔄 Reset System</button>
        <select id="scenario-select" onchange="changeScenario(this.value)">
            <option value="">Select Scenario...</option>
            <option value="user_query">E-commerce Query + SQL</option>
            <option value="pipeline">Data Pipeline (Bronze→Silver→Gold)</option>
            <option value="context_memory">Context Memory</option>
            <option value="full_demo">Full E-commerce Demo</option>
        </select>
        <button class="btn-demo" onclick="runDemo()">▶️ Run Demo</button>
        <span style="margin-left: auto; color: var(--text-dim); font-size: 12px;">
            <span class="status-dot blue"></span> Snowflake-ready: Pipeline Demo
        </span>
    </div>
    
    <div class="panels">
        <!-- Top Left: User Input + Data Pipeline -->
        <div class="panel panel-user">
            <div class="panel-header">
                <div class="panel-icon">👤</div>
                <div class="panel-title">User Input + Pipeline Status</div>
            </div>
            <div class="panel-content" id="user-panel">
                <div class="input-area">
                    <textarea id="query-input" placeholder="Enter your query here... (e.g., Show all completed orders)">Show all completed orders</textarea>
                    <button class="send-btn" onclick="sendQuery()">📤 Send Request</button>
                </div>
                <div id="query-result" class="log-section" style="display: none;">
                    <div class="log-section-title" id="result-title">Query Result</div>
                    <div id="query-result-content"></div>
                </div>
            </div>
        </div>
        
        <!-- Top Right: E-commerce Workflow -->
        <div class="panel panel-sqlantra">
            <div class="panel-header">
                <div class="panel-icon">📊</div>
                <div class="panel-title">E-commerce Data Pipeline</div>
                <div class="panel-subtitle" id="sqlantra-status">Ready</div>
            </div>
            <div class="panel-content" id="sqlantra-panel">
                <div class="log-section">
                    <div class="log-section-title">System Status</div>
                    <div class="log-line dim">E-commerce pipeline ready.</div>
                    <div class="log-line dim">Bronze→Silver→Gold layers active.</div>
                </div>
            </div>
        </div>
        
        <!-- Bottom Left: Database -->
        <div class="panel panel-db">
            <div class="panel-header">
                <div class="panel-icon">🗄️</div>
                <div class="panel-title">Snowflake Data Layers</div>
                <select id="table-select" class="db-table-select" onchange="loadTable(this.value)">
                    <option value="">Select layer...</option>
                </select>
            </div>
            <div class="panel-content" id="db-panel">
                <div class="log-line">Select Bronze, Silver, or Gold layer to view data</div>
            </div>
        </div>
        
        <!-- Bottom Right: Context Memory -->
        <div class="panel panel-memory">
            <div class="panel-header">
                <div class="panel-icon">🧠</div>
                <div class="panel-title">Context Memory System</div>
                <div class="panel-subtitle" id="memory-count">0 entries</div>
            </div>
            <div class="panel-content" id="memory-panel">
                <div class="memory-empty">Context memory tracks pipeline operations.</div>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="footer-status">
            <div class="footer-item"><span class="status-dot green"></span> Snowflake Connected</div>
            <div class="footer-item"><span class="status-dot blue"></span> Pipeline Active</div>
            <div class="footer-item"><span class="status-dot yellow"></span> Gold Metrics Ready</div>
        </div>
        <div id="footer-info">Step: Ready</div>
    </footer>
</div>

<script>
let currentStep = 0;
let pendingApprovals = [];

let highlightTimeouts = {};
let currentScenario = 'user_query';
let isWaitingForApi = false;

// Step-by-step execution mode
let stepMode = false;
let stepData = null;
let stepHint = null;
let lastMemoryCount = 0;

function showStepHint(text) {
    removeStepHint();
    stepHint = document.createElement('div');
    stepHint.className = 'step-hint';
    stepHint.textContent = text;
    document.body.appendChild(stepHint);
}

function removeStepHint() {
    if (stepHint) {
        stepHint.remove();
        stepHint = null;
    }
}

document.addEventListener('keydown', function(e) {
    if (!stepMode) return;
    if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        advanceStep();
    }
});

function advanceStep() {
    if (!stepMode || !stepData) return;
    const steps = stepData.workflow;
    currentStep++;
    if (currentStep > steps.length) {
        showFinalResult();
        return;
    }
    renderCurrentStep();
}

function renderCurrentStep() {
    const steps = stepData.workflow;
    clearPanel('sqlantra-panel');
    
    // Show completed steps (from 0 to currentStep-2)
    for (let i = 0; i < currentStep - 1; i++) {
        const step = steps[i];
        const div = document.createElement('div');
        div.className = 'sqlantra-step';
        div.innerHTML = '<div class="sqlantra-step-header"><span class="sqlantra-step-num">' + step.step + '</span><span class="sqlantra-step-title">' + step.title + '</span></div><div class="sqlantra-step-detail">' + step.detail + '</div>';
        if (step.code) {
            div.innerHTML += '<div class="sqlantra-code">' + step.code + '</div>';
        }
        document.getElementById('sqlantra-panel').appendChild(div);
    }
    
    // Show current step with highlight
    if (currentStep <= steps.length) {
        const activeStep = steps[currentStep - 1];
        const div = document.createElement('div');
        div.className = 'sqlantra-step active';
        div.innerHTML = '<div class="sqlantra-step-header"><span class="sqlantra-step-num">' + activeStep.step + '</span><span class="sqlantra-step-title">' + activeStep.title + '</span></div><div class="sqlantra-step-detail">' + activeStep.detail + '</div>';
        if (activeStep.code) {
            div.innerHTML += '<div class="sqlantra-code">' + activeStep.code + '</div>';
        }
        document.getElementById('sqlantra-panel').appendChild(div);
        document.getElementById('sqlantra-status').textContent = 'Step ' + currentStep + '/' + steps.length;
        showStepHint('Press ENTER or SPACE to continue to next step');
        
        // Auto-select table in database panel when step 5 (Database Execution) is shown
        if (activeStep.step === 5 && activeStep.table) {
            const tableName = activeStep.table;
            // Get panel element
            const panel = document.getElementById('db-panel');
            // Fetch table data directly
            fetch('/api/table/' + tableName).then(r => r.json()).then(result => {
                if (!result.error && result.data) {
                    let html = '<div style="margin-bottom:8px;padding:8px;background:var(--surface-el2);border-radius:6px;font-size:12px">';
                    html += '<span class="status-dot green"></span> DB | ';
                    html += '<span class="status-dot yellow"></span> ' + tableName + ': ' + result.data.length + ' rows</div>';
                    html += '<table class="db-table"><thead><tr>';
                    result.columns.forEach(c => html += '<th>'+c+'</th>');
                    html += '</tr></thead><tbody>';
                    result.data.slice(0,10).forEach(row => {
                        html += '<tr>';
                        result.columns.forEach(c => html += '<td>'+(row[c]||'')+'</td>');
                        html += '</tr>';
                    });
                    html += '</tbody></table>';
                    panel.innerHTML = html;
                }
            });
        }
        
        // Refresh memory panel when step 4 (Context Memory Update) is shown
        if (activeStep.step === 4) {
            refreshMemoryWithHighlight();
        }
    }
}

function showFinalResult() {
    stepMode = false;
    removeStepHint();
    currentStep = 0;
    const result = stepData;
    stepData = null;
    document.getElementById('sqlantra-status').textContent = 'Complete';
    document.getElementById('footer-info').textContent = 'Step: Query Complete';
    clearPanel('sqlantra-panel');
    result.workflow.forEach(step => {
        const div = document.createElement('div');
        div.className = 'sqlantra-step';
        div.innerHTML = '<div class="sqlantra-step-header"><span class="sqlantra-step-num">' + step.step + '</span><span class="sqlantra-step-title">' + step.title + '</span></div><div class="sqlantra-step-detail">' + step.detail + '</div>';
        if (step.code) {
            div.innerHTML += '<div class="sqlantra-code">' + step.code + '</div>';
        }
        document.getElementById('sqlantra-panel').appendChild(div);
    });

    // Show expense result or query result
    // FLOW: Employee submits → Sqlantra processes → Complete → THEN shows Manager pending
    if (result.expense) {
        const resultDiv = document.getElementById('query-result');
        const contentDiv = document.getElementById('query-result-content');
        const titleDiv = document.getElementById('result-title');
        resultDiv.style.display = 'block';
        titleDiv.textContent = 'Expense Request Result';
        
        // ====== EMPLOYEE VIEW (what employee sees) ======
        let html = '<div class="log-section">';
        html += '<div class="log-section-title">👤 Employee View - Submitted</div>';
        html += '<div class="log-line dim">You submitted this expense request:</div>';
        html += '<div class="log-line">Employee: <strong>' + result.expense.employee + '</strong></div>';
        html += '<div class="log-line">Category: <strong>' + result.expense.category + '</strong></div>';
        html += '<div class="log-line">Amount: <strong>$' + result.expense.amount + '</strong></div>';
        html += '<div class="log-line">Description: ' + result.expense.description + '</div>';
        
        if (result.pending) {
            // ====== MANAGER VIEW (appears AFTER workflow complete) ======
            html += '<div class="log-line" style="margin-top:8px">⏳ Submitted - Waiting for approval...</div>';
            html += '</div>';
            
            // Manager approval panel shows AFTER all steps complete
            html += '<div class="log-section" style="margin-top:16px;border:2px solid var(--gold);padding:12px">';
            html += '<div class="log-section-title" style="color:var(--gold)">👨‍💼 Manager View - Pending Approvals</div>';
            html += '<div class="log-line dim" style="margin-bottom:8px">📨 You have new approval request:</div>';
            
            // Get notification from result
            const notif = result.result?.notification || 'Expense reimbursement requested';
            html += '<div class="hitl-item">';
            html += '<div class="hitl-item-header">';
            html += '<span class="hitl-badge">PENDING</span>';
            html += '<span>expense_reimbursement</span>';
            html += '</div>';
            html += '<div class="hitl-details" style="white-space:pre-wrap">' + notif + '</div>';
            html += '<div class="hitl-actions">';
            const approvalId = result.result?.approval_id || '';
            html += '<button class="btn-approve" onclick="approveRequest(\'' + approvalId + '\')">✅ Approve</button>';
            html += '<button class="btn-reject" onclick="rejectRequest(\'' + approvalId + '\')">❌ Reject</button>';
            html += '</div></div>';
            html += '</div>';
        } else {
            html += '<div class="log-line success">✓ Auto-approved (under threshold)</div>';
            html += '</div>';
        }
        contentDiv.innerHTML = html;
    } else if (result.data && result.data.length > 0) {
        let html = '';
        const resultDiv = document.getElementById('query-result');
        const contentDiv = document.getElementById('query-result-content');
        const titleDiv = document.getElementById('result-title');
        resultDiv.style.display = 'block';
        titleDiv.textContent = 'Query Result';
        html += '<div class="log-line dim">' + result.data.length + ' rows returned</div>';
        html += '<table class="db-table" style="margin-top: 8px;"><thead><tr>';
        Object.keys(result.data[0]).forEach(col => html += '<th>' + col + '</th>');
        html += '</tr></thead><tbody>';
        result.data.slice(0, 10).forEach(row => {
            html += '<tr>';
            Object.values(row).forEach(val => {
                html += '<td>' + (val !== null ? val : '') + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        contentDiv.innerHTML = html;
    }
    refreshTables();
    refreshMemory();
    // Don't call refreshHITL here - only show after workflow complete
}

function changeScenario(scenario) {
    currentScenario = scenario || 'user_query';
    const queryInput = document.getElementById('query-input');
    const hitlSection = document.getElementById('hitl-section');
    
    // ALWAYS hide HITL panel when switching scenarios
    hitlSection.style.display = 'none';
    
    // Set default query based on scenario
    switch(scenario) {
        case 'user_query':
            queryInput.value = 'Show all completed orders';
            break;
        case 'pipeline':
            queryInput.value = 'Show all completed orders to process through pipeline';
            break;
        case 'hitl_workflow':
            queryInput.value = 'Submit expense: John Doe, travel, $1200, Flight to NYC';
            break;
        case 'context_memory':
            queryInput.value = 'Show me what we have stored in context memory';
            break;
        case 'full_demo':
            queryInput.value = 'Show all completed orders';
            break;
        default:
            queryInput.value = 'Show all completed orders';
    }
    
    // Clear panels when switching scenarios
    clearPanel('sqlantra-panel');
    document.getElementById('query-result').style.display = 'none';
    document.getElementById('hitl-section').style.display = 'none';
    document.getElementById('sqlantra-status').textContent = `Scenario: ${scenario.replace('_', ' ')}`;
    document.getElementById('footer-info').textContent = `Step: Scenario Selected`;
    
    refreshTables();
    refreshMemory();
}

function addLog(panel, message, type, highlight = false) {
    const el = document.getElementById(panel);
    const line = document.createElement('div');
    line.className = `log-line ${type}`;
    line.innerHTML = message;
    el.appendChild(line);
    el.scrollTop = el.scrollHeight;
    
    // Add highlight effect if requested
    if (highlight) {
        line.style.backgroundColor = 'rgba(255, 212, 59, 0.3)';
        line.style.borderLeft = '3px solid var(--gold)';
        
        // Clear any existing timeout for this panel
        if (highlightTimeouts[panel]) {
            clearTimeout(highlightTimeouts[panel]);
        }
        
        // Remove highlight after 3 seconds
        highlightTimeouts[panel] = setTimeout(() => {
            line.style.backgroundColor = '';
            line.style.borderLeft = '';
        }, 3000);
    }
}

function clearPanel(panel) {
    const el = document.getElementById(panel);
    el.innerHTML = '';
}

async function api(endpoint, options = {}) {
    try {
        const resp = await fetch('/api/' + endpoint, {
            headers: {'Content-Type': 'application/json', ...options.headers},
            ...options
        });
        return await resp.json();
    } catch (e) {
        return {error: e.message};
    }
}

function loadTable(tableName) {
    if (!tableName) return;
    api('table/' + encodeURIComponent(tableName)).then(result => {
        const panel = document.getElementById('db-panel');
        if (result.error) {
            panel.innerHTML = '<div class="log-line error">Error: ' + result.error + '</div>';
            return;
        }
        
        // Add MCP and Ollama status above the table
        let statusHtml = '<div style="margin-bottom: 8px; padding: 8px; background: var(--surface-el2); border-radius: 6px; border: 1px solid var(--border); font-size: 12px;">';
        statusHtml += '<strong>System Status:</strong> ';
        statusHtml += '<span class="status-dot green"></span> DB Connected | ';
        statusHtml += '<span class="status-dot blue"></span> Ollama: ' + MODEL + ' | ';
        statusHtml += '<span class="status-dot yellow"></span> Tables: ' + result.data.length + ' rows';
        statusHtml += '</div>';
        
        let html = statusHtml;
        html += '<table class="db-table"><thead><tr>';
        result.columns.forEach(col => { html += '<th>' + col + '</th>'; });
        html += '</tr></thead><tbody>';
        result.data.forEach(row => {
            html += '<tr>';
            result.columns.forEach(col => {
                let val = row[col];
                if (val !== null && val !== undefined) {
                    if (typeof val === 'object') val = JSON.stringify(val);
                    val = String(val);
                }
                html += '<td title="' + (val || '') + '">' + (val || '') + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        panel.innerHTML = html;
    });
}

function refreshTables() {
    return api('tables').then(tables => {
        const select = document.getElementById('table-select');
        const currentSelection = select.value;
        select.innerHTML = '<option value="">Select table...</option>';
        tables.forEach(t => {
            const selected = (t === currentSelection) ? ' selected' : '';
            select.innerHTML += '<option value="' + t + '"' + selected + '>' + t + '</option>';
        });
        // If no table is selected, load the first one
        if (!currentSelection && tables.length > 0) {
            loadTable(tables[0]);
        }
    });
}

function selectTable(tableName) {
    if (!tableName) return;
    const select = document.getElementById('table-select');
    select.value = tableName;
    loadTable(tableName);
}

function refreshMemory() {
    api('memory').then(result => {
        const panel = document.getElementById('memory-panel');
        const count = document.getElementById('memory-count');
        count.textContent = result.entries.length + ' entries';
        
        if (result.entries.length === 0) {
            panel.innerHTML = '<div class="memory-empty">Context memory is empty. Start a query to populate memory.</div>';
            return;
        }
        
        let html = '';
        // Show newest first
        result.entries.slice().reverse().slice(0, 15).forEach(entry => {
            let displayValue = entry.value;
            if (typeof entry.value === 'string') {
                try {
                    const obj = JSON.parse(entry.value);
                    displayValue = JSON.stringify(obj, null, 2);
                } catch(e) {}
            }
            const valuePreview = displayValue.length > 150 ? displayValue.substring(0, 150) + '...' : displayValue;
            
            html += '<div class="memory-item">';
            html += '<div class="memory-item-header">';
            html += '<span class="memory-key">' + entry.key + '</span>';
            html += '<span class="memory-op">' + entry.operation + '</span>';
            html += '</div>';
            html += '<div class="memory-value" style="white-space:pre-wrap;max-height:80px;overflow:auto">' + valuePreview + '</div>';
            html += '<div class="memory-time">' + (entry.timestamp || entry.created_at || '') + '</div>';
            html += '</div>';
        });
        panel.innerHTML = html;
    });
}

function refreshMemoryWithHighlight() {
    api('memory').then(result => {
        const panel = document.getElementById('memory-panel');
        const count = document.getElementById('memory-count');
        count.textContent = result.entries.length + ' entries';
        
        if (result.entries.length === 0) {
            panel.innerHTML = '<div class="memory-empty">Context memory is empty. Start a query to populate memory.</div>';
            return;
        }
        
        // Get recent entries for highlighting
        const recentEntries = result.entries.slice(-5);
        const newCount = recentEntries.length;
        
        let html = '';
        // Show all entries in reverse order (newest first)
        result.entries.slice().reverse().slice(0, 15).forEach((entry, index) => {
            const isNew = index < newCount;
            const highlightClass = isNew ? ' highlight' : '';
            
            // Format value nicely
            let displayValue = entry.value;
            if (typeof entry.value === 'string') {
                try {
                    const obj = JSON.parse(entry.value);
                    displayValue = JSON.stringify(obj, null, 2);
                } catch(e) {}
            }
            // Truncate for display
            const valuePreview = displayValue.length > 150 ? displayValue.substring(0, 150) + '...' : displayValue;
            
            html += '<div class="memory-item' + highlightClass + '">';
            html += '<div class="memory-item-header">';
            html += '<span class="memory-key">' + entry.key + '</span>';
            html += '<span class="memory-op">' + entry.operation + '</span>';
            html += '</div>';
            html += '<div class="memory-value" style="white-space:pre-wrap;max-height:80px;overflow:auto">' + valuePreview + '</div>';
            html += '<div class="memory-time">' + (entry.timestamp || entry.created_at || '') + '</div>';
            html += '</div>';
        });
        panel.innerHTML = html;
        
        // Scroll to top to show newest
        panel.scrollTop = 0;
    });
}

function refreshHITL() {
    api('hitl/pending').then(result => {
        pendingApprovals = result;
        const section = document.getElementById('hitl-section');
        const container = document.getElementById('hitl-items');
        
        if (result.length === 0) {
            section.style.display = 'none';
            return;
        }
        
        section.style.display = 'block';
        let html = '';
        result.forEach(apr => {
            html += '<div class="hitl-item">';
            html += '<div class="hitl-item-header">';
            html += '<span class="hitl-badge">PENDING</span>';
            html += '<span>' + apr.action_type + '</span>';
            html += '</div>';
            html += '<div class="hitl-details">' + apr.notification + '</div>';
            html += '<div class="hitl-actions">';
            html += '<button class="btn-approve" onclick="approveRequest(\'' + apr.approval_id + '\')">✅ Approve</button>';
            html += '<button class="btn-reject" onclick="rejectRequest(\'' + apr.approval_id + '\')">❌ Reject</button>';
            html += '</div></div>';
        });
        container.innerHTML = html;
    });
}

async function approveRequest(approvalId) {
    console.log('Approve clicked:', approvalId);
    const result = await api('hitl/respond', {
        method: 'POST',
        body: JSON.stringify({approval_id: approvalId, approved: true, comment: 'Approved by user'})
    });
    console.log('API result:', result);
    
    // Show confirmation and update UI
    if (result.manager_message) {
        // Show manager confirmation
        const hitlSection = document.getElementById('hitl-section');
        hitlSection.style.display = 'block';
        hitlSection.innerHTML = '<div class="hitl-title" style="color:var(--db)">Approved</div><div class="log-line success">' + result.manager_message + '</div>';
        
        // Show employee confirmation in query-result
        const queryResult = document.getElementById('query-result');
        const contentDiv = document.getElementById('query-result-content');
        queryResult.style.display = 'block';
        
        // Add confirmation message
        const confDiv = document.createElement('div');
        confDiv.className = 'log-section';
        confDiv.style.border = '2px solid var(--db)';
        confDiv.style.padding = '12px';
        confDiv.innerHTML = '<div class="log-section-title" style="color:var(--db)">Employee View - Status Update</div>';
        confDiv.innerHTML += '<div class="log-line success">' + result.employee_message + '</div>';
        contentDiv.innerHTML = '';
        contentDiv.appendChild(confDiv);
        
        refreshMemory();
    } else {
        alert('Error approving: ' + (result.error || JSON.stringify(result)));
    }
}

async function rejectRequest(approvalId) {
    const result = await api('hitl/respond', {
        method: 'POST',
        body: JSON.stringify({approval_id: approvalId, approved: false, comment: 'Rejected by user'})
    });
    console.log('Reject result:', result);
    
    if (result.manager_message) {
        // Show manager confirmation
        const hitlSection = document.getElementById('hitl-section');
        hitlSection.style.display = 'block';
        hitlSection.innerHTML = '<div class="hitl-title" style="color:var(--user)">Rejected</div><div class="log-line error">' + result.manager_message + '</div>';
        
        // Show employee confirmation in query-result
        const queryResult = document.getElementById('query-result');
        const contentDiv = document.getElementById('query-result-content');
        queryResult.style.display = 'block';
        
        const confDiv = document.createElement('div');
        confDiv.className = 'log-section';
        confDiv.style.border = '2px solid var(--user)';
        confDiv.style.padding = '12px';
        confDiv.innerHTML = '<div class="log-section-title" style="color:var(--user)">Employee View - Status Update</div>';
        confDiv.innerHTML += '<div class="log-line error">' + result.employee_message + '</div>';
        contentDiv.innerHTML = '';
        contentDiv.appendChild(confDiv);
        
        refreshMemory();
    } else {
        alert('Error rejecting: ' + (result.error || JSON.stringify(result)));
    }
}

function showConfirmation(view, message, approved) {
    // Add confirmation to user panel
    const resultDiv = document.getElementById('query-result');
    const contentDiv = document.getElementById('query-result-content');
    
    if (view === 'manager') {
        // Update Manager View section
        const managerSection = contentDiv.querySelector('.manager-confirmation');
        if (managerSection) {
            managerSection.innerHTML = '<div class="log-section-title" style="color:' + (approved ? 'var(--db)' : 'var(--user)') + '">' + message + '</div>';
        }
    } else {
        // Add to Employee View section
        const confDiv = document.createElement('div');
        confDiv.className = 'log-section';
        confDiv.style.marginTop = '16px';
        confDiv.style.border = '2px solid ' + (approved ? 'var(--db)' : 'var(--user)');
        confDiv.style.padding = '12px';
        confDiv.innerHTML = '<div class="log-section-title" style="color:' + (approved ? 'var(--db)' : 'var(--user)') + '">👤 Employee View - Status Update</div>';
        confDiv.innerHTML += '<div class="log-line" style="color:' + (approved ? 'var(--db)' : 'var(--user)') + '">' + message + '</div>';
        
        // Remove old result first
        const oldResult = contentDiv.querySelector('.existing-result');
        if (oldResult) {
            oldResult.remove();
        }
        
        contentDiv.insertBefore(confDiv, contentDiv.firstChild);
    }
}

async function sendQuery() {
        if (isWaitingForApi) return;
        const query = document.getElementById('query-input').value;
        if (!query.trim()) return;
        
        isWaitingForApi = true;
        const label = currentScenario === 'hitl_workflow' ? 'Request:' : 'Query:';
        addLog('user-panel', '<strong>' + label + '</strong> ' + query, 'user', true);
        document.getElementById('sqlantra-status').textContent = 'Processing...';
        document.getElementById('footer-info').textContent = 'Step: Processing ' + (currentScenario === 'pipeline' ? 'Pipeline' : 'Query');
        // Hide previous result when starting new request
        document.getElementById('query-result').style.display = 'none';
        
        try {
            const result = await api('query', {
                method: 'POST',
                body: JSON.stringify({query: query})
            });
            
            if (result.error) {
                addLog('sqlantra-panel', '❌ Error: ' + result.error, 'error');
                document.getElementById('sqlantra-status').textContent = 'Error';
                return;
            }
            
            // Enable step-by-step mode
            stepMode = true;
            stepData = result;
            currentStep = 0;
            
            // Show first step and hint
            renderCurrentStep();
        } finally {
            isWaitingForApi = false;
        }
    }

async function runDemo() {
    const demoQueries = [
        'Show all completed orders',
        'Show daily sales metrics',
        'Show top performing products'
    ];
    
    for (let i = 0; i < demoQueries.length; i++) {
        document.getElementById('query-input').value = demoQueries[i];
        await sendQuery();
        await new Promise(r => setTimeout(r, 1000));
    }
}

async function resetSystem() {
    await api('reset', {method: 'POST'});
    
    // Clear all panels
    clearPanel('sqlantra-panel');
    document.getElementById('sqlantra-panel').innerHTML = '<div class="log-section"><div class="log-section-title">System Status</div><div class="log-line dim">Sqlantra System reset. Ready for new query.</div></div>';
    
    // Reset query result
    const queryResult = document.getElementById('query-result');
    queryResult.style.display = 'none';
    document.getElementById('query-result-content').innerHTML = '';
    
        // Reset input field to default
        const inputField = document.getElementById('query-input');
        inputField.value = 'Show all completed orders';
    
    // Reset HITL panel
    document.getElementById('hitl-section').style.display = 'none';
    document.getElementById('hitl-items').innerHTML = '';
    
    // Reset status displays
    document.getElementById('sqlantra-status').textContent = 'Ready';
    document.getElementById('footer-info').textContent = 'Step: Ready';
    
    // Reset scenario to default
    document.getElementById('scenario-select').value = 'user_query';
    
    // Refresh data
    refreshTables();
    refreshMemory();
}

// Initialize scenario selector
document.getElementById('scenario-select').value = 'user_query';

// ALWAYS hide HITL panel on initial load
document.getElementById('hitl-section').style.display = 'none';

changeScenario('user_query');

refreshTables();
refreshMemory();
// Don't refresh HITL on load - only after user submits expense
// refreshHITL() will be called after workflow completes
setInterval(refreshMemory, 3000);
// Only poll for HITL if in non-HITL scenarios
// setInterval(refreshHITL, 5000); // Disabled - only show after submit
</script>
</body>
</html>
"""


class SqlantraDemoHandler:
    def __init__(self):
        self.db = db
        self.text_sql = text_to_sql
        self.memory = context_memory.SqlantraContextMemory()
        self.memory.set_db_module(db)
        self.hitl = hitl_workflow.HITLWorkflow(db, self.memory)
        self.skills = context_memory.SkillsRegistry()
        self.agents = context_memory.AgentsRegistry()

        self.memory.store(
            "system_start",
            datetime.now().isoformat(),
            "system",
            {"event": "system_startup"},
        )
        self.memory.store("ollama_model", MODEL, "config", {"url": OLLAMA_URL})
        self.memory.store(
            "database_path", db.DB_PATH, "config", {"tables": db.get_all_tables()}
        )

    def call_ollama(self, prompt: str, timeout: int = 60) -> str:
        """Unified LLM call: OpenRouter first, local Ollama fallback."""
        return llm_client.call_llm(prompt, timeout=timeout)

    def handle(self, path: str):
        if path == "/" or path == "":
            return (200, HTML.encode())

        elif path == "/api/tables":
            tables = self.db.get_all_tables()
            return (200, json.dumps(tables).encode())

        elif path.startswith("/api/table/"):
            table_name = path.split("/")[-1]
            result = self.db.get_table_data(table_name)
            return (200, json.dumps(result).encode())

        elif path == "/api/memory":
            entries = self.memory.get_recent_entries(50)
            return (200, json.dumps({"entries": entries}).encode())

        elif path == "/api/hitl/pending":
            pending = self.hitl.get_pending_for_ui()
            return (200, json.dumps(pending).encode())

        elif path == "/api/hitl/respond":
            return (200, json.dumps({"status": "ok"}).encode())

        elif path == "/api/query":
            return (200, json.dumps({"error": "Use POST"}).encode())

        elif path == "/api/reset":
            db.reset_database()
            self.memory.clear()
            self.memory.store(
                "system_reset", datetime.now().isoformat(), "system", {"event": "reset"}
            )
            return (200, json.dumps({"status": "reset"}).encode())

        elif path == "/api/query" and False:
            pass

        return (404, b"Not Found")

    def handle_query(self, query: str) -> dict:
        """Process a user query through the full Sqlantra workflow."""
        self.memory.store("last_query", query, "input", {"type": "user_query"})

        workflow_steps = []

        # Step 0: Sqlantra Start Processing
        step0 = {
            "step": 0,
            "title": "Sqlantra Start Processing",
            "detail": f"Sqlantra system received user request",
            "code": f"Query: {query}",
        }
        workflow_steps.append(step0)

        # Step 1: Skill Matching
        step1 = {
            "step": 1,
            "title": "Skill Matching",
            "detail": f"Matching query to available skills...",
            "code": f"Query: {query}",
        }
        matched_skill = self.skills.match_skill(query)
        if matched_skill:
            step1["detail"] = f"Matched skill: {matched_skill['name']}"
            step1["code"] = (
                f"Skill: {matched_skill['file']}::{matched_skill['function']}"
            )
        workflow_steps.append(step1)
        self.memory.store(
            "matched_skill", matched_skill, "skill_match", {"query": query}
        )

        # Step 2: Agent Routing
        step2 = {
            "step": 2,
            "title": "Agent Routing",
            "detail": f"Selecting appropriate agent...",
        }
        matched_agent = self.agents.match_agent(query)
        if matched_agent:
            step2["detail"] = f"Selected agent: {matched_agent['name']}"
            step2["code"] = (
                f"Agent: {matched_agent['class']} in {matched_agent['file']}"
            )
        workflow_steps.append(step2)
        self.memory.store(
            "matched_agent", matched_agent, "agent_routing", {"query": query}
        )

        # Step 3: Text-to-SQL Generation
        step3 = {
            "step": 3,
            "title": "Text-to-SQL Generation",
            "detail": f"Calling Ollama to generate SQL...",
            "code": f"Model: {MODEL}",
        }
        sql = self.text_sql.text_to_sql(query)
        step3["detail"] = f"Generated SQL query"
        step3["code"] = (
            f"<span class='sqlantra-ollama'>SELECT * FROM ... WHERE ...</span>\n<span class='sqlantra-success'>{sql}</span>"
        )
        workflow_steps.append(step3)
        self.memory.store("generated_sql", sql, "sql_generation", {"query": query})

        # Step 4: Context Memory Update
        step4 = {
            "step": 4,
            "title": "Context Memory Update",
            "detail": f"Storing query context for future recall...",
            "code": f"memory.store('query_{datetime.now().strftime('%H%M%S')}', ...)",
        }
        workflow_steps.append(step4)

        # Step 5: Database Execution
        # Extract table name from SQL
        table_name = "orders"
        import re
        match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if match:
            table_name = match.group(1).lower()
            if table_name not in ['orders', 'products', 'order_items', 'bronze_orders', 'silver_orders', 'gold_daily_sales', 'gold_product_performance', 'gold_customer_360', 'hitl_approvals', 'context_memory_log']:
                table_name = "orders"

        step5 = {
            "step": 5,
            "title": "Database Execution",
            "detail": f"Executing SQL against SQLite database...",
            "code": f"DB: {db.DB_PATH}",
            "table": table_name,
        }
        result = self.db.query_sql(sql)
        if result.get("error"):
            step5["detail"] = f"Error: {result['error']}"
            step5["code"] = f"<span class='sqlantra-error'>{result['error']}</span>"
        else:
            step5["detail"] = f"Retrieved {len(result.get('data', []))} rows from {table_name}"
            step5["code"] = (
                f"<span class='sqlantra-success'>✓ {len(result.get('data', []))} rows</span>"
            )
        workflow_steps.append(step5)
        self.memory.store(
            "query_result",
            result.get("data", []),
            "db_result",
            {"sql": sql, "rows": len(result.get("data", []))},
        )

        # Step 6: Pipeline Processing (E-commerce Orders)
        if "orders" in sql.lower() or "order" in query.lower():
            step6 = {
                "step": 6,
                "title": "Data Pipeline Processing",
                "detail": f"Processing orders through Bronze→Silver→Gold layers...",
                "code": f"Transforming raw order data into business metrics",
            }
            workflow_steps.append(step6)

            # Process bronze layer (raw data ingestion)
            for record in result.get("data", []):
                self.db.insert_bronze_record(record.get("order_id"), record)
            
            # Process silver layer (cleaned data)
            for record in result.get("data", []):
                self.db.insert_silver_record(record)
            
            # Process gold layer (business metrics)
            metrics_result = self.db.process_gold_metrics()
            
            self.memory.store(
                "pipeline_processed",
                len(result.get("data", [])),
                "pipeline",
                {"bronze": "raw_orders", "silver": "clean_orders", "gold": "metrics"},
            )
            
            step6["detail"] = f"✓ Pipeline complete: Bronze→Silver→Gold metrics generated"
            step6["code"] = f"<span class='sqlantra-success'>✓ Daily sales, product performance, customer 360 updated</span>"

        # Step 7: Business Insights (replacing HITL for e-commerce)
        if "orders" in sql.lower() or "sales" in query.lower():
            step7 = {
                "step": 7,
                "title": "Business Insights Generated",
                "detail": f"Gold layer metrics ready for visualization...",
                "code": f"Ready for Tableau/PowerBI dashboard",
                "tables": ["gold_daily_sales", "gold_product_performance", "gold_customer_360"],
            }
            workflow_steps.append(step7)
            
            self.memory.store(
                "business_insights",
                "Gold layer metrics generated",
                "insights",
                {"tables": ["gold_daily_sales", "gold_product_performance", "gold_customer_360"]},
            )

        self.memory.store(
            "workflow_complete",
            datetime.now().isoformat(),
            "workflow",
            {"steps": len(workflow_steps)},
        )

        return {
            "query": query,
            "sql": sql,
            "data": result.get("data", []),
            "workflow": workflow_steps,
            "error": result.get("error"),
        }


    def handle_expense(self, query: str) -> dict:
        """Process expense submission through HITL workflow.

        Format: "Submit expense: Employee, Category, Amount, Description"
        Example: "Submit expense: John Doe, travel, $1200, Flight to NYC"
        """
        import re

        query_clean = query.replace("Submit expense:", "").replace("expense:", "").strip()

        employee = "Unknown"
        category = "other"
        amount = 0.0
        description = query_clean

        parts = [p.strip() for p in query_clean.split(",")]
        if len(parts) >= 1:
            employee = parts[0]
        if len(parts) >= 2:
            category = parts[1].lower()
        if len(parts) >= 3:
            amount_str = parts[2].replace("$", "").strip()
            try:
                amount = float(amount_str)
            except:
                amount = 0.0
        if len(parts) >= 4:
            description = parts[3]

        self.memory.store("expense_submission", query, "input", {"type": "expense_submit"})

        workflow_steps = []

        step0 = {
            "step": 0,
            "title": "Sqlantra Start Processing",
            "detail": f"Processing expense submission",
            "code": f"Employee: {employee}, Category: {category}, Amount: ${amount}",
        }
        workflow_steps.append(step0)

        step1 = {
            "step": 1,
            "title": "Expense Validation",
            "detail": f"Validating expense details...",
            "code": f"Category: {category}, Amount: ${amount:.2f}",
        }
        workflow_steps.append(step1)

        step2 = {
            "step": 2,
            "title": "Threshold Check",
            "detail": f"Checking approval threshold for {category}...",
            "code": f"Threshold: ${hitl_workflow.ExpenseCategory.get_threshold(category)}",
        }
        workflow_steps.append(step2)

        result = self.hitl.submit_expense(employee, category, amount, description)

        if result.get("pending"):
            step3 = {
                "step": 3,
                "title": "HITL Approval Required",
                "detail": f"Amount ${amount:.2f} exceeds ${hitl_workflow.ExpenseCategory.get_threshold(category)} threshold - approval needed",
                "code": f"<span class='sqlantra-warning'>Pending Approval: {result['approval_id']}</span>",
                "trigger_hitl": True,
                "approval_id": result["approval_id"],
            }
            workflow_steps.append(step3)
        else:
            step3 = {
                "step": 3,
                "title": "Auto-Approved",
                "detail": f"Amount ${amount:.2f} is under ${hitl_workflow.ExpenseCategory.get_threshold(category)} threshold",
                "code": f"<span class='sqlantra-success'>Auto-approved</span>",
            }
            workflow_steps.append(step3)

        step4 = {
            "step": 4,
            "title": "Context Memory Update",
            "detail": f"Storing expense submission...",
        }
        workflow_steps.append(step4)

        self.memory.store(
            "expense_result",
            result,
            "expense_result",
            {"employee": employee, "category": category, "amount": amount},
        )

        return {
            "query": query,
            "expense": {
                "employee": employee,
                "category": category,
                "amount": amount,
                "description": description,
            },
            "result": result,
            "workflow": workflow_steps,
            "pending": result.get("pending", False),
        }


_handler = None


def main():
    global _handler
    from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

    _handler = SqlantraDemoHandler()

    print(f"""
╔═════════════════════════════════════════════════════════════════════╗
║         E-commerce Data Pipeline Demo - Snowflake-Ready              ║
╠═════════════════════════════════════════════════════════════════════╣
║  🌐 http://localhost:{PORT}                                          ║
║                                                                   ║
║  Features:                                                          ║
║  • E-commerce orders: Web/App/POS/API channels                     ║
║  • Bronze→Silver→Gold pipeline layers                             ║
║  • Gold metrics: Daily Sales, Product Performance, Customer 360    ║
║  • Text-to-SQL with Snowflake-ready schema                         ║
║  • Context memory tracking pipeline operations                       ║
╚═════════════════════════════════════════════════════════════════════╝
    """)

    class Request(BaseHTTPRequestHandler):
        h = _handler

        def do_GET(self):
            status, body = self.h.handle(self.path)
            self.send_response(status)
            self.send_header(
                "Content-Type", "text/html" if self.path == "/" else "application/json"
            )
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path == "/api/query":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                query = data.get("query", "")

                # Check for expense submission format
                if query.lower().startswith("submit expense:") or "expense:" in query.lower():
                    result = self.h.handle_expense(query)
                else:
                    result = self.h.handle_query(query)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            elif self.path == "/api/reset":
                db.reset_database()
                _handler.memory.clear()
                _handler.memory.store(
                    "system_reset",
                    datetime.now().isoformat(),
                    "system",
                    {"event": "reset"},
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "reset"}).encode())
            elif self.path == "/api/hitl/respond":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode()
                data = json.loads(body)
                approval_id = data.get("approval_id")
                approved = data.get("approved", False)
                comment = data.get("comment", "")

                # Use confirm_and_notify to get confirmation messages
                result = _handler.hitl.confirm_and_notify(approval_id, approved, comment)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            else:
                self.send_response(404)
                self.end_headers()

    server = ThreadingHTTPServer(("", PORT), Request)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
