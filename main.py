import sys
import os
import pefile
import webbrowser
import threading
from capstone import *
from groq import Groq
from flask import Flask, request, jsonify, render_template_string

# Groq API Configuration
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"

app = Flask(__name__)

# Embedded Cyberpunk HTML/CSS/JS Template (Tüm kaçış karakteri hataları temizlendi)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NovaRE AI - Web Static Analyzer</title>
    <style>
        :root {
            --bg-color: #0B0D11;
            --pane-color: #161920;
            --border-color: #2D313E;
            --text-color: #E2E8F0;
            --accent-green: #22C55E;
            --accent-red: #EF4444;
            --accent-blue: #3B82F6;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Consolas', monospace;
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        header {
            background-color: var(--pane-color);
            border-bottom: 1px solid var(--border-color);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        header h1 {
            font-size: 16px;
            color: var(--accent-green);
        }
        .main-container {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        .sidebar-left {
            width: 280px;
            background-color: var(--pane-color);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 15px;
        }
        .panel-title {
            font-size: 11px;
            font-weight: bold;
            color: #8F93A2;
            margin-bottom: 8px;
            text-transform: uppercase;
        }
        .file-upload-box {
            border: 1px dashed var(--accent-green);
            padding: 15px;
            text-align: center;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 15px;
        }
        .file-upload-box input {
            display: none;
        }
        .file-label {
            font-size: 11px;
            color: var(--text-color);
            word-break: break-all;
        }
        select {
            background-color: var(--bg-color);
            color: var(--text-color);
            border: 1px solid var(--border-color);
            padding: 8px;
            border-radius: 4px;
            width: 100%;
            margin-bottom: 20px;
            outline: none;
            font-family: inherit;
        }
        .block-list {
            flex: 1;
            border: 1px solid var(--border-color);
            background-color: var(--bg-color);
            border-radius: 4px;
            overflow-y: auto;
            list-style: none;
        }
        .block-list li {
            padding: 8px 12px;
            font-size: 12px;
            border-bottom: 1px solid var(--border-color);
            cursor: pointer;
            transition: background 0.2s;
        }
        .block-list li:hover {
            background-color: #1B2130;
            color: var(--accent-green);
        }
        .center-graph {
            flex: 1;
            overflow: auto;
            background-color: var(--bg-color);
            position: relative;
            padding: 30px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .node-card {
            background-color: var(--pane-color);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            width: 320px;
            margin-bottom: 40px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            position: relative;
        }
        .node-header {
            background-color: #202530;
            padding: 8px 12px;
            font-size: 12px;
            font-weight: bold;
            color: var(--accent-green);
            border-bottom: 1px solid var(--border-color);
        }
        .node-body {
            padding: 10px;
            font-size: 11px;
            white-space: pre-line;
            line-height: 1.5;
        }
        .flow-indicator {
            text-align: center;
            font-size: 11px;
            font-weight: bold;
            margin-top: -35px;
            margin-bottom: 15px;
            padding: 2px 8px;
            border-radius: 4px;
            display: inline-block;
        }
        .flow-true { color: var(--accent-green); }
        .flow-false { color: var(--accent-red); }
        .flow-unconditional { color: var(--accent-blue); }

        .sidebar-right {
            width: 380px;
            background-color: var(--pane-color);
            border-left: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            padding: 15px;
        }
        .chat-area {
            flex: 1;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 12px;
            overflow-y: auto;
            margin-bottom: 10px;
            font-size: 12px;
            line-height: 1.4;
        }
        .chat-msg {
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #1F2430;
        }
        .msg-role-User { color: var(--accent-green); font-weight: bold; }
        .msg-role-AI { color: var(--accent-blue); font-weight: bold; }
        .msg-role-System { color: #8F93A2; font-weight: bold; }
        
        .chat-input-box {
            display: flex;
            margin-bottom: 10px;
        }
        .chat-input-box input {
            flex: 1;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            color: #FFFFFF;
            padding: 8px;
            border-radius: 4px;
            outline: none;
            font-family: inherit;
        }
        .chat-input-box button {
            background-color: #161A26;
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 5px;
            font-family: inherit;
            font-weight: bold;
        }
        .chat-input-box button:hover {
            background-color: var(--accent-green);
            color: var(--bg-color);
        }
        .audit-btn {
            background-color: #10B981;
            color: #FFFFFF;
            border: none;
            padding: 10px;
            border-radius: 4px;
            cursor: pointer;
            font-family: inherit;
            font-weight: bold;
            width: 100%;
        }
        .audit-btn:hover {
            background-color: #059669;
        }
        footer {
            background-color: var(--pane-color);
            border-top: 1px solid var(--border-color);
            padding: 6px 20px;
            font-size: 11px;
            color: #8F93A2;
        }
    </style>
</head>
<body>
    <header>
        <h1>NovaRE AI - Web Binary Static Analyzer</h1>
        <div id="status-text" style="font-size: 11px; color:#8F93A2;">Engine Ready</div>
    </header>

    <div class="main-container">
        <div class="sidebar-left">
            <div class="panel-title">Target Analysis File</div>
            <div class="file-upload-box" onclick="document.getElementById('file-input').click()">
                <span class="file-label" id="file-label-text">Click to Select Binary</span>
                <input type="file" id="file-input" onchange="uploadFile()">
            </div>

            <div class="panel-title">Analysis Depth</div>
            <select id="depth-select">
                <option value="1 KB">1 KB (Recommended)</option>
                <option value="4 KB">4 KB (Medium)</option>
                <option value="16 KB">16 KB (Deep)</option>
            </select>

            <div class="panel-title">Extracted Symbol Blocks</div>
            <ul class="block-list" id="block-list-container"></ul>
        </div>

        <div class="center-graph" id="graph-view-container"></div>

        <div class="sidebar-right">
            <div class="panel-title" style="color: var(--accent-blue);">AI Conversation Portal</div>
            <div class="chat-area" id="chat-box">
                <div class="chat-msg">
                    <span class="msg-role-System">System:</span> Welcome to NovaRE Web Engine. Upload a target to inspect decompiled execution.
                </div>
            </div>
            <div class="chat-input-box">
                <input type="text" id="chat-input" placeholder="Ask AI about logic flow..." onkeydown="if(event.key === 'Enter') sendChatMessage()">
                <button onclick="sendChatMessage()">Send</button>
            </div>
            <button class="audit-btn" onclick="runAiAudit()">🚀 Run Deep Cyber Audit</button>
        </div>
    </div>

    <footer>
        Local Server Connection Status: Connected (127.0.0.1:5000)
    </footer>

    <script>
        var currentBlocks = [];

        function uploadFile() {
            var fileInput = document.getElementById('file-input');
            var depth = document.getElementById('depth-select').value;
            var file = fileInput.files[0];
            if (!file) return;

            document.getElementById('file-label-text').innerText = file.name;
            document.getElementById('status-text').innerText = "Disassembling " + file.name + "...";

            var formData = new FormData();
            formData.append('file', file);
            formData.append('depth', depth);

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.error) {
                    alert(data.error);
                    document.getElementById('status-text').innerText = "Decompilation failed.";
                } else {
                    currentBlocks = data.blocks;
                    renderGraph(data.blocks);
                    document.getElementById('status-text').innerText = "Successfully parsed blocks.";
                }
            })
            .catch(function(err) {
                console.error(err);
                document.getElementById('status-text').innerText = "Network upload error.";
            });
        }

        function renderGraph(blocks) {
            var listContainer = document.getElementById('block-list-container');
            var graphContainer = document.getElementById('graph-view-container');
            listContainer.innerHTML = "";
            graphContainer.innerHTML = "";

            blocks.forEach(function(block, idx) {
                var li = document.createElement('li');
                li.innerText = block.title;
                li.onclick = function() {
                    document.getElementById("node-card-" + block.id).scrollIntoView({ behavior: 'smooth' });
                };
                listContainer.appendChild(li);

                if (idx > 0) {
                    var prevBlock = blocks[idx - 1];
                    var linkType = "fallthrough";
                    prevBlock.next_blocks.forEach(function(link) {
                        if (link[0] === block.id) {
                            linkType = link[1];
                        }
                    });

                    var flowDiv = document.createElement('div');
                    flowDiv.className = "flow-indicator flow-" + linkType;
                    flowDiv.innerText = "▼ Link: [" + linkType.toUpperCase() + "]";
                    graphContainer.appendChild(flowDiv);
                }

                var card = document.createElement('div');
                card.className = "node-card";
                card.id = "node-card-" + block.id;

                var header = document.createElement('div');
                header.className = "node-header";
                header.innerText = block.title;
                card.appendChild(header);

                var body = document.createElement('div');
                body.className = "node-body";
                
                var instText = "";
                block.instructions.forEach(function(inst) {
                    instText += "0x" + inst[0].toString(16).toUpperCase() + ":  " + inst[1] + " " + inst[2] + "\\n";
                });
                body.innerText = instText;
                card.appendChild(body);

                graphContainer.appendChild(card);
            });
        }

        function appendChatMsg(sender, text) {
            var chatBox = document.getElementById('chat-box');
            var roleClass = "msg-role-System";
            if (sender === "User") {
                roleClass = "msg-role-User";
            } else if (sender === "NovaRE AI") {
                roleClass = "msg-role-AI";
            }
            
            var msgDiv = document.createElement('div');
            msgDiv.className = "chat-msg";
            
            var formattedText = text.split('\\n').join('<br>');
            msgDiv.innerHTML = "<span class='" + roleClass + "'>" + sender + ":</span> " + formattedText;
            
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function sendChatMessage() {
            var input = document.getElementById('chat-input');
            var message = input.value.strip ? input.value.strip() : input.value.trim();
            if (!message) return;

            input.value = "";
            appendChatMsg("User", message);
            document.getElementById('status-text').innerText = "AI is thinking...";

            fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: message, blocks: currentBlocks })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                appendChatMsg("NovaRE AI", data.response);
                document.getElementById('status-text').innerText = "Response completed.";
            })
            .catch(function(err) {
                appendChatMsg("System", "Error communicating with Groq API.");
            });
        }

        function runAiAudit() {
            appendChatMsg("System", "Initializing deep cyber static audit report...");
            document.getElementById('status-text').innerText = "Running deep static audit...";

            fetch('/api/audit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ blocks: currentBlocks })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                appendChatMsg("NovaRE AI", data.response);
                document.getElementById('status-text').innerText = "Audit completed.";
            })
            .catch(function(err) {
                appendChatMsg("System", "Error performing static audit.");
            });
        }
    </script>
</body>
</html>
"""

# Mock/Welcome Data for initialization
MOCK_BLOCKS = [
    {
        "id": 0,
        "title": "Main Entry (0x00401000)",
        "instructions": [
            (0x00401000, "push", "rbp"),
            (0x00401001, "mov", "rbp, rsp"),
            (0x00401004, "sub", "rsp, 0x20"),
            (0x00401008, "mov", "dword ptr [rbp-4], 0"),
            (0x0040100F, "jmp", "0x00401020")
        ],
        "next_blocks": [(1, "unconditional")]
    },
    {
        "id": 1,
        "title": "Loop Check (0x00401020)",
        "instructions": [
            (0x00401020, "cmp", "dword ptr [rbp-4], 10"),
            (0x00401024, "jge", "0x00401036")
        ],
        "next_blocks": [(3, "true"), (2, "false")]
    },
    {
        "id": 2,
        "title": "Loop Body (0x00401026)",
        "instructions": [
            (0x00401026, "mov", "eax, dword ptr [rbp-4]"),
            (0x00401029, "add", "eax, 1"),
            (0x0040102C, "mov", "dword ptr [rbp-4], eax"),
            (0x0040102F, "jmp", "0x00401020")
        ],
        "next_blocks": [(1, "unconditional")]
    },
    {
        "id": 3,
        "title": "Exit Function (0x00401036)",
        "instructions": [
            (0x00401036, "xor", "eax, eax"),
            (0x00401038, "add", "rsp, 0x20"),
            (0x0040103C, "pop", "rbp"),
            (0x0040103D, "ret", "")
        ],
        "next_blocks": []
    }
]

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file stream"}), 400
    
    file = request.files['file']
    depth_str = request.form.get('depth', '1 KB')
    
    try:
        file_bytes = file.read()
    except Exception as e:
        return jsonify({"error": f"Read failed: {str(e)}"}), 500

    entry_offset = 0
    try:
        pe = pefile.PE(data=file_bytes)
        entry_offset = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        for section in pe.sections:
            if section.VirtualAddress <= entry_offset < section.VirtualAddress + section.Misc_VirtualSize:
                entry_offset = section.PointerToRawData + (entry_offset - section.VirtualAddress)
                break
    except Exception:
        entry_offset = 0

    depth_map = {"1 KB": 1024, "4 KB": 4096, "16 KB": 16384}
    chunk_size = depth_map.get(depth_str, 1024)
    raw_chunk = file_bytes[entry_offset:entry_offset + chunk_size]

    # Assembly Decompilation via Capstone
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    instructions = list(md.disasm(raw_chunk, entry_offset))

    if not instructions:
        # Fallback to standard 32-bit if x64 is empty
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        instructions = list(md.disasm(raw_chunk, entry_offset))

    if not instructions:
        return jsonify({"error": "Empty or unrecognized instruction sequence"}), 400

    blocks = []
    current_list = []
    block_idx = 0

    for inst in instructions:
        current_list.append((inst.address, inst.mnemonic, inst.op_str))
        is_control_flow = inst.mnemonic in [
            'jmp', 'je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 
            'call', 'ret', 'loop', 'js', 'jns', 'jo', 'jno', 'jb', 'ja'
        ]
        if is_control_flow or len(current_list) >= 12:
            blocks.append({
                "id": block_idx,
                "title": f"Block_{block_idx:02d} (0x{current_list[0][0]:X})",
                "instructions": current_list,
                "next_blocks": []
            })
            current_list = []
            block_idx += 1

    if current_list:
        blocks.append({
            "id": block_idx,
            "title": f"Block_{block_idx:02d} (0x{current_list[0][0]:X})",
            "instructions": current_list,
            "next_blocks": []
        })

    for i in range(len(blocks) - 1):
        last_op = blocks[i]["instructions"][-1]
        mnem = last_op[1]
        op = last_op[2]
        
        if mnem in ['jmp', 'ret']:
            blocks[i]["next_blocks"].append((i + 1, "unconditional"))
        elif mnem in ['je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle']:
            blocks[i]["next_blocks"].appe
