import sys
import os
import pefile
from capstone import *
from groq import Groq
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading

# Groq API Configuration
GROQ_API_KEY = "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"
GROQ_MODEL = "llama-3.3-70b-versatile"

# CustomTkinter Theme configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green") # Neon Green Matrix/Cyber vibe!

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

class NovaREAppCustomTk:
    def __init__(self, root):
        self.root = root
        self.root.title("NovaRE AI - Premium CustomTkinter Static Analyzer")
        self.root.geometry("1300, 780")
        
        # States
        self.current_blocks = MOCK_BLOCKS
        self.current_file_path = ""
        self.chat_history = []
        
        # Color definitions for Vector drawing
        self.bg_color = "#0B0D11"
        self.pane_color = "#161920"
        self.border_color = "#2D313E"
        self.text_color = "#E2E8F0"
        self.accent_green = "#22C55E"
        self.accent_red = "#EF4444"
        self.accent_blue = "#3B82F6"
        
        self.setup_menu()
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

    def build_ui(self):
        # Configure Grid Layout
        self.root.columnconfigure(0, weight=1, minsize=260) # Left
        self.root.columnconfigure(1, weight=3, minsize=550) # Center
        self.root.columnconfigure(2, weight=2, minsize=370) # Right
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        # LEFT PANEL: Meta info & Block List (CustomTkinter Frame)
        left_pane = ctk.CTkFrame(self.root, fg_color=self.pane_color, corner_radius=10, border_color=self.border_color, border_width=1)
        left_pane.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(left_pane, text="TARGET ANALYSIS FILE", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#8F93A2").pack(anchor="w", padx=15, pady=(15, 2))
        self.file_label = ctk.CTkLabel(left_pane, text="No Target Loaded\n(Using Demo Graph)", font=ctk.CTkFont(family="Consolas", size=10), text_color=self.accent_green, justify="left", wraplength=230)
        self.file_label.pack(anchor="w", padx=15, pady=2)
        
        ctk.CTkLabel(left_pane, text="ANALYSIS DEPTH", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#8F93A2").pack(anchor="w", padx=15, pady=(20, 2))
        self.depth_selector = ctk.CTkComboBox(left_pane, values=["1 KB (Recommended)", "4 KB (Medium)", "16 KB (Deep)"], font=ctk.CTkFont(family="Consolas", size=11))
        self.depth_selector.set("1 KB (Recommended)")
        self.depth_selector.pack(fill="x", padx=15, pady=2)
        
        ctk.CTkLabel(left_pane, text="EXTRACTED SYMBOL BLOCKS", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#8F93A2").pack(anchor="w", padx=15, pady=(20, 2))
        
        # Standard Listbox packaged nicely for seamless selection handling
        self.block_list = tk.Listbox(left_pane, bg=self.bg_color, fg=self.text_color, bd=1, relief="solid", highlightcolor=self.accent_green, selectbackground="#1B2130", selectforeground=self.accent_green, font=("Consolas", 10))
        self.block_list.pack(fill="both", expand=True, padx=15, pady=10)
        self.block_list.bind("<<ListboxSelect>>", self.jump_to_block)

        # CENTER PANEL: Canvas (Software-Render Graph View - Winlator Safe)
        center_pane = ctk.CTkFrame(self.root, fg_color=self.bg_color, corner_radius=10, border_color=self.border_color, border_width=1)
        center_pane.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        self.canvas = tk.Canvas(center_pane, bg=self.bg_color, bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Custom Pan/Drag bindings for mouse/touch translation
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.pan)

        # RIGHT PANEL: AI Conversation Center
        right_pane = ctk.CTkFrame(self.root, fg_color=self.pane_color, corner_radius=10, border_color=self.border_color, border_width=1)
        right_pane.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        ctk.CTkLabel(right_pane, text="NOVARE LLAMA-3.3 INTELLIGENT AI", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color=self.accent_blue).pack(anchor="w", padx=15, pady=(15, 5))
        
        # Rich Text Chat Box
        self.chat_area = ctk.CTkTextbox(right_pane, fg_color=self.bg_color, font=ctk.CTkFont(family="Consolas", size=11), text_color=self.text_color, border_color=self.border_color, border_width=1, wrap="word")
        self.chat_area.pack(fill="both", expand=True, padx=15, pady=5)
        self.chat_area.insert(tk.END, "Welcome to NovaRE CustomTkinter Edition!\nAsk me anything about binary engineering or click Deep Audit below.\n\n")
        self.chat_area.configure(state="disabled")
        
        chat_input_frame = ctk.CTkFrame(right_pane, fg_color="transparent")
        chat_input_frame.pack(fill="x", padx=15, pady=10)
        
        self.chat_input = ctk.CTkEntry(chat_input_frame, placeholder_text="Ask logic explanation...", font=ctk.CTkFont(family="Consolas", size=11), fg_color=self.bg_color, border_color=self.border_color)
        self.chat_input.pack(side="left", fill="x", expand=True, ipady=3)
        self.chat_input.bind("<Return>", lambda e: self.send_chat_message())
        
        send_btn = ctk.CTkButton(chat_input_frame, text="Send", width=70, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), command=self.send_chat_message)
        send_btn.pack(side="right", padx=(8, 0))
        
        self.audit_btn = ctk.CTkButton(right_pane, text="🚀 Run Deep Cyber Audit (AI)", font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), fg_color="#10B981", hover_color="#059669", text_color="#FFFFFF", command=self.run_ai_audit)
        self.audit_btn.pack(fill="x", padx=15, pady=(0, 15))

        # STATUS BAR
        self.status_label = ctk.CTkLabel(self.root, text="Engine Idle. Ready to parse x86_64 target files.", font=ctk.CTkFont(family="Consolas", size=10), text_color="#8F93A2", fg_color=self.pane_color, anchor="w")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky="we", ipady=4)

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Open Executable File")
        if file_path:
            self.current_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
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

        depth_map = {"1 KB (Recommended)": 1024, "4 KB (Medium)": 4096, "16 KB (Deep)": 16384}
        chunk_size = depth_map.get(self.depth_selector.get(), 1024)
        
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

        for lvl, b_ids in level_groups.items():
            count = len(b_ids)
            total_w = count * node_width + (count - 1) * gap_x
            offset_x = 400 - (total_w / 2)
            
            for idx, b_id in enumerate(b_ids):
                x = offset_x + idx * (node_width + gap_x)
                y = 40 + lvl * gap_y
                pos_map[b_id] = (x, y)

        self.block_coords = {}
        
        # Render Blocks on Vector Canvas
        for b in self.current_blocks:
            b_id = b["id"]
            x, y = pos_map[b_id]
            
            self.block_list.insert(tk.END, b["title"])
            
            text_lines = [b["title"]]
            for addr, mnem, op in b["instructions"]:
                text_lines.append(f"0x{addr:08X}: {mnem} {op}")
            
            node_height = len(text_lines) * 16 + 20
            self.block_coords[b_id] = (x, y, node_width, node_height)
            
            # Rounded Block outline using canvas polygons
            self.draw_rounded_rect(x, y, x + node_width, y + node_height, 8, fill="#161920", outline=self.border_color, width=2, tags=f"node_{b_id}")
            # Header block
            self.draw_rounded_rect(x + 2, y + 2, x + node_width - 2, y + 22, 6, fill="#202530", outline="", tags=f"node_{b_id}")
            
            # Header Text
            self.canvas.create_text(x + 12, y + 12, text=b["title"], fill=self.accent_green, font=("Consolas", 10, "bold"), anchor="w")
            
            # Instruction print loop
            line_y = y + 36
            for addr, mnem, op in b["instructions"]:
                inst_text = f"0x{addr:08X}  {mnem:<6} {op}"
                self.canvas.create_text(x + 12, line_y, text=inst_text, fill=self.text_color, font=("Consolas", 9), anchor="w")
                line_y += 16

        # Render Flowlines between blocks
        for b in self.current_blocks:
            b_id = b["id"]
            if b_id not in self.block_coords:
                continue
            x1, y1, w1, h1 = self.block_coords[b_id]
            start_pt = (x1 + w1 / 2, y1 + h1)
            
            for target_id, link_type in b["next_blocks"]:
                if target_id in self.block_coords:
                    x2, y2, w2, h2 = self.block_coords[target_id]
                    end_pt = (x2 + w2 / 2, y2)
                    
                    color = "#5C6370"
                    if link_type == "true":
                        color = self.accent_green
                    elif link_type == "false":
                        color = self.accent_red
                    elif link_type == "unconditional":
                        color = self.accent_blue
                    
                    # Draw connection line with arrow head pointing to children
                    self.canvas.create_line(start_pt[0], start_pt[1], end_pt[0], end_pt[1], fill=color, width=2, arrow=tk.LAST, smooth=True)

        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    # Helper function to render rounded blocks without native Windows API dependencies
    def draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r,
            x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2,
            x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1
        ]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def jump_to_block(self, event):
        selection = self.block_list.curselection()
        if selection:
            idx = selection[0]
            title = self.block_list.get(idx)
            for b_id, b in enumerate(self.current_blocks):
                if b["title"] == title:
                    x, y, w, h = self.block_coords[b_id]
                    self.canvas.xview_moveto((x - 100) / self.canvas.winfo_width())
                    self.canvas.yview_moveto((y - 100) / self.canvas.winfo_height())
                    
                    # Target highlight
                    self.canvas.itemconfig(f"node_{b_id}", outline=self.accent_green)
                    for other_id in range(len(self.current_blocks)):
                        if other_id != b_id:
                            self.canvas.itemconfig(f"node_{other_id}", outline=self.border_color)
                    break

    def build_ai_context(self):
        context = "Current Code Control-Flow Architecture:\n"
        for b in self.current_blocks:
            context += f"## {b['title']}\n"
            for addr, mnem, op in b['instructions']:
                context += f"0x{addr:08X}: {mnem} {op}\n"
            context += f"Connections: {b['next_blocks']}\n\n"
        return context

    def send_chat_message(self):
        user_msg = self.chat_input.get().strip()
        if not user_msg:
            return
        
        self.chat_input.delete(0, tk.END)
        self.append_chat("User", user_msg)
        self.update_status("AI is processing disassembly context and query...")

        system_instruction = (
            "You are NovaRE, a sovereign AI Reverse Engineering assistant. "
            "You have direct system telemetry access to the decompiled basic blocks control flow graph (CFG). "
            "Answer users technical questions, explain blocks, variables, stack frames, decryption loops, and overall logic accurately. "
            "Analyze user request context and keep 
