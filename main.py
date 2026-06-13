import sys
import os
import pefile
from capstone import *
from groq import Groq
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

# Groq API Configuration
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"

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

class NovaREAppTk:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaRE AI - Winlator Optimized Static Analyzer")
        self.root.geometry("1280x750")
        
        # Application States
        self.current_blocks = MOCK_BLOCKS
        self.current_file_path = ""
        self.chat_history = []
        
        # Color Scheme (Cyberpunk Dark Mode)
        self.bg_color = "#0B0D11"
        self.pane_color = "#0F121A"
        self.border_color = "#1F2430"
        self.text_color = "#E2E8F0"
        self.accent_green = "#00FF66"
        self.accent_red = "#FF4A6B"
        self.accent_blue = "#00C0FF"
        
        self.root.configure(bg=self.bg_color)
        
        self.setup_menu()
        self.setup_styles()
        self.build_ui()
        self.draw_graph()

    def setup_menu(self):
        menubar = tk.Menu(self.root, bg=self.pane_color, fg=self.text_color, activebackground=self.border_color)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.pane_color, fg=self.text_color)
        file_menu.add_command(label="Open Binary Target File", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        analysis_menu = tk.Menu(menubar, tearoff=0, bg=self.pane_color, fg=self.text_color)
        analysis_menu.add_command(label="Refresh Flow-Chart View", command=self.draw_graph)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        
        ai_menu = tk.Menu(menubar, tearoff=0, bg=self.pane_color, fg=self.text_color)
        ai_menu.add_command(label="Generate Comprehensive AI Report", command=self.run_ai_audit)
        menubar.add_cascade(label="AI Tools", menu=ai_menu)
        
        self.root.config(menu=menubar)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=self.pane_color, foreground=self.text_color, borderwidth=0)
        style.configure("TLabel", background=self.pane_color, foreground="#8F93A2", font=("Consolas", 9, "bold"))
        style.configure("TCombobox", fieldbackground=self.bg_color, background=self.pane_color, foreground=self.text_color, arrowcolor=self.accent_green)
        style.configure("TButton", background="#161A26", foreground=self.accent_green, bordercolor=self.accent_green, font=("Consolas", 10, "bold"))
        style.map("TButton", background=[("active", self.accent_green)], foreground=[("active", self.bg_color)])

    def build_ui(self):
        # Master Grid Layout
        self.root.columnconfigure(0, weight=1, minsize=250) # Left panel
        self.root.columnconfigure(1, weight=3, minsize=500) # Center graph
        self.root.columnconfigure(2, weight=2, minsize=350) # Right AI chat
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0) # Status bar

        # LEFT PANEL: Meta & Selectors
        left_pane = tk.Frame(self.root, bg=self.pane_color, bd=1, relief="solid", highlightbackground=self.border_color)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        tk.Label(left_pane, text="TARGET ANALYSIS FILE", bg=self.pane_color, fg="#8F93A2", font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=(10, 2))
        self.file_label = tk.Label(left_pane, text="No Target Loaded (Demo Graph Mode)", bg=self.pane_color, fg=self.accent_green, font=("Consolas", 9), wraplength=220, justify="left")
        self.file_label.pack(anchor="w", padx=10, pady=2)
        
        tk.Label(left_pane, text="ANALYSIS DEPTH", bg=self.pane_color, fg="#8F93A2", font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=(15, 2))
        self.depth_selector = ttk.Combobox(left_pane, values=["1 KB (Recommended)", "4 KB (Medium)", "16 KB (Deep)"], state="readonly")
        self.depth_selector.current(0)
        self.depth_selector.pack(fill="x", padx=10, pady=2)
        
        tk.Label(left_pane, text="EXTRACTED SYMBOL BLOCKS", bg=self.pane_color, fg="#8F93A2", font=("Consolas", 9, "bold")).pack(anchor="w", padx=10, pady=(15, 2))
        self.block_list = tk.Listbox(left_pane, bg=self.bg_color, fg=self.text_color, bd=1, relief="solid", highlightcolor=self.accent_green, selectbackground="#1B2130", selectforeground=self.accent_green, font=("Consolas", 9))
        self.block_list.pack(fill="both", expand=True, padx=10, pady=5)
        self.block_list.bind("<<ListboxSelect>>", self.jump_to_block)

        # CENTER PANEL: Canvas Graph View
        center_pane = tk.Frame(self.root, bg=self.bg_color, bd=1, relief="solid", highlightbackground=self.border_color)
        center_pane.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        # Lightweight Zoom/Pan Canvas
        self.canvas = tk.Canvas(center_pane, bg=self.bg_color, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Drag to Pan support (Perfect for touchscreens / Winlator mice)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)
        
        # RIGHT PANEL: AI Portal
        right_pane = tk.Frame(self.root, bg=self.pane_color, bd=1, relief="solid", highlightbackground=self.border_color)
        right_pane.grid(row=0, column=2, sticky="nsew", padx=5, pady=5)
        
        tk.Label(right_pane, text="NOVARE LLAMA-3.3 INTELLIGENT AI", bg=self.pane_color, fg=self.accent_blue, font=("Consolas", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.chat_area = scrolledtext.ScrolledText(right_pane, bg=self.bg_color, fg=self.text_color, bd=1, relief="solid", font=("Consolas", 9), wrap="word")
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)
        self.chat_area.insert(tk.END, "Welcome to NovaRE AI! Drag or open a binary to analyze it using AI-powered Control Flow Analysis.\n\n")
        self.chat_area.configure(state="disabled")
        
        chat_input_frame = tk.Frame(right_pane, bg=self.pane_color)
        chat_input_frame.pack(fill="x", padx=10, pady=5)
        
        self.chat_input = tk.Entry(chat_input_frame, bg=self.bg_color, fg="#FFFFFF", insertbackground=self.accent_green, bd=1, relief="solid", font=("Consolas", 10))
        self.chat_input.pack(side="left", fill="x", expand=True, ipady=4)
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())
        
        send_btn = ttk.Button(chat_input_frame, text="Send", command=self.send_chat_message)
        send_btn.pack(side="right", padx=(5, 0))
        
        self.audit_btn = ttk.Button(right_pane, text="🚀 Run Deep Cyber Audit (AI)", command=self.run_ai_audit)
        self.audit_btn.pack(fill="x", padx=10, pady=5)

        # STATUS BAR
        self.status_label = tk.Label(self.root, text="Engine Idle. Ready to parse x86_64 target files.", bg=self.pane_color, fg="#8F93A2", font=("Consolas", 8), anchor="w", padx=10, pady=4)
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="we")

    # Drag to pan canvas events
    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Open Executable File")
        if file_path:
            self.current_file_path = file_path
            self.file_label.config(text=os.path.basename(file_path))
            self.update_status(f"Disassembling {file_path}...")
            
            try:
                self.parse_and_disassemble(file_path)
                self.update_status(f"Successfully disassembled {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Disassembler Error", f"Failed to parse binary structure: {str(e)}")
                self.update_status("Decompilation aborted.")

    def parse_and_disassemble(self, file_path):
        entry_offset = 0
        try:
            pe = pefile.PE(file_path)
            entry_offset = pe.OPTIONAL_HEADER.AddressOfEntryPoint
            for section in pe.sections:
                if section.VirtualAddress <= entry_offset < section.VirtualAddress + section.Misc_VirtualSize:
                    entry_offset = section.PointerToRawData + (entry_offset - section.VirtualAddress)
                    break
        except Exception:
            entry_offset = 0

        depth_map = {0: 1024, 1: 4096, 2: 16384}
        chunk_size = depth_map.get(self.depth_selector.current(), 1024)
        
        with open(file_path, 'rb') as f:
            f.seek(entry_offset)
            raw_bytes = f.read(chunk_size)

        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instructions = list(md.disasm(raw_bytes, entry_offset))

        if not instructions:
            raise ValueError("No valid x86/x64 instructions extracted from file.")

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
                target_val = self.parse_operand_address(op)
                linked = False
                if target_val:
                    for t_idx, b in enumerate(blocks):
                        if b["instructions"] and b["instructions"][0][0] == target_val:
                            blocks[i]["next_blocks"].append((t_idx, "unconditional"))
                            linked = True
                            break
                if not linked and mnem != 'ret':
                    blocks[i]["next_blocks"].append((i + 1, "unconditional"))
            
            elif mnem in ['je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle']:
                target_val = self.parse_operand_address(op)
                linked = False
                if target_val:
                    for t_idx, b in enumerate(blocks):
                        if b["instructions"] and b["instructions"][0][0] == target_val:
                            blocks[i]["next_blocks"].append((t_idx, "true"))
                            linked = True
                            break
                if not linked:
                    mock_idx = (i + 2) if (i + 2) < len(blocks) else i
                    blocks[i]["next_blocks"].append((mock_idx, "true"))
                
                blocks[i]["next_blocks"].append((i + 1, "false"))
            else:
                blocks[i]["next_blocks"].append((i + 1, "fallthrough"))

        self.current_blocks = blocks
        self.draw_graph()

    def parse_operand_address(self, op_str):
        try:
            if op_str.startswith("0x"):
                return int(op_str, 16)
            return int(op_str)
        except ValueError:
            return None

    def draw_graph(self):
        self.canvas.delete("all")
        self.block_list.delete(0, tk.END)
        
        if not self.current_blocks:
            return

        # Simple hierarchical layout engine
        levels = {}
        def compute_depth(node_id, current_level, visited):
            if node_id in visited:
                return
            visited.add(node_id)
            levels[node_id] = max(levels.get(node_id, 0), current_level)
            for target_id, _ in self.current_blocks[node_id]["next_blocks"]:
                compute_depth(target_id, current_level + 1, visited.copy())

        compute_depth(0, 0, set())

        level_groups = {}
        for b_id in range(len(self.current_blocks)):
            lvl = levels.get(b_id, 0)
            level_groups.setdefault(lvl, []).append(b_id)

        pos_map = {}
        node_width = 280
        gap_x = 60
        gap_y = 180

        # Calculate coordinates on canvas
        for lvl, b_ids in level_groups.items():
            count = len(b_ids)
            total_w = count * node_width + (count - 1) * gap_x
            offset_x = 400 - (total_w / 2) # Center around x=400
            
            for idx, b_id in enumerate(b_ids):
                x = offset_x + idx * (node_width + gap_x)
                y = 40 + lvl * gap_y
                pos_map[b_id] = (x, y)

        self.block_coords = {}
        
        # Render Nodes (Blocks)
        for b in self.current_blocks:
            b_id = b["id"]
            x, y = pos_map[b_id]
            self.block_coords[b_id] = (x, y, node_width, 100) # Fallba
