import sys
import os
import pefile
from capstone import *
from groq import Groq

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QSplitter, QTextEdit, QLineEdit, 
                             QPushButton, QFileDialog, QListWidget, QLabel, 
                             QGraphicsView, QGraphicsScene, QGraphicsItem, 
                             QMenuBar, QMenu, QStatusBar, QMessageBox, QFrame,
                             QComboBox)
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath
from PyQt6.QtCore import Qt, QRectF, QPointF, QThread, pyqtSignal

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

# AI Worker Thread to keep UI responsive
class GroqWorker(QThread):
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, messages):
        super().__init__()
        self.messages = messages

    def run(self):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=self.messages,
                temperature=0.3,
                max_tokens=2500
            )
            self.response_received.emit(completion.choices[0].message.content)
        except Exception as e:
            self.error_occurred.emit(str(e))


# Custom Vector Graphics Node representing basic assembly block
class NodeItem(QGraphicsItem):
    def __init__(self, title, instructions, x, y):
        super().__init__()
        self.title = title
        self.instructions = instructions
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        
        self.width = 300
        self.line_height = 18
        self.header_height = 28
        self.height = self.header_height + len(instructions) * self.line_height + 15
        self.rect = QRectF(0, 0, self.width, self.height)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Node Box Styling
        brush = QBrush(QColor("#161920"))
        pen = QPen(QColor("#2B2F3A"), 1.5)
        if self.isSelected():
            pen = QPen(QColor("#00FF66"), 2)  # Glowing border if selected
        
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(self.rect, 8, 8)
        
        # Node Title Header
        header_rect = QRectF(0, 0, self.width, self.header_height)
        painter.setBrush(QBrush(QColor("#202530")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(header_rect, 8, 8)
        painter.drawRect(QRectF(0, self.header_height - 5, self.width, 5))  # Corner correction
        
        # Header Text
        painter.setPen(QColor("#00FF66"))
        font = QFont("Consolas", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(header_rect.adjusted(12, 0, -12, 0), Qt.AlignmentFlag.AlignVCenter, self.title)
        
        # Instructions Syntax Highlighting
        y_offset = self.header_height + 8
        painter.setFont(QFont("Consolas", 9))
        for addr, mnem, op in self.instructions:
            # Address Field
            painter.setPen(QColor("#8F93A2"))
            painter.drawText(10, y_offset, f"0x{addr:08X}:")
            
            # Mnemonic Field
            painter.setPen(QColor("#FF4A6B"))
            painter.drawText(105, y_offset, mnem)
            
            # Operands Field
            painter.setPen(QColor("#F0F4FF"))
            painter.drawText(155, y_offset, op)
            
            y_offset += self.line_height


# Custom Vector Connection/Edge Item
class EdgeItem(QGraphicsItem):
    def __init__(self, start_item, end_item, color=QColor("#8F93A2")):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.color = color
        self.setZValue(-1)

    def boundingRect(self):
        return QRectF(self.start_item.pos(), self.end_item.pos()).normalized().adjusted(-40, -40, 40, 40)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        start_rect = self.start_item.rect
        end_rect = self.end_item.rect
        
        p1 = self.start_item.pos() + QPointF(start_rect.width() / 2, start_rect.height())
        p2 = self.end_item.pos() + QPointF(end_rect.width() / 2, 0)
        
        # Cubic Bezier Path for aesthetic routing
        path = QPainterPath()
        path.moveTo(p1)
        ctrl1 = QPointF(p1.x(), p1.y() + 60)
        ctrl2 = QPointF(p2.x(), p2.y() - 60)
        path.cubicTo(ctrl1, ctrl2, p2)
        
        pen = QPen(self.color, 1.8)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Directional Arrowhead
        painter.setBrush(QBrush(self.color))
        arrow = QPainterPath()
        arrow.moveTo(p2)
        arrow.lineTo(p2.x() - 6, p2.y() - 10)
        arrow.lineTo(p2.x() + 6, p2.y() - 10)
        arrow.closeSubpath()
        painter.drawPath(arrow)


# Zoomable/Pannable Viewport Area
class GraphView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setBackgroundBrush(QBrush(QColor("#0B0D11")))
        self.setFrameShape(QFrame.Shape.NoFrame)

    def wheelEvent(self, event):
        factor = 1.15
        if event.angleDelta().y() < 0:
            factor = 1.0 / factor
        self.scale(factor, factor)


# Main GUI Architecture
class NovaREApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NovaRE AI - Premium Reverse Engineering Engine")
        self.resize(1300, 850)
        self.current_blocks = MOCK_BLOCKS
        self.current_file_path = ""
        self.chat_history = []
        
        self.init_ui()
        self.apply_dark_theme()
        self.draw_graph(self.current_blocks)

    def init_ui(self):
        # Menu Bar setup
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = file_menu.addAction("Open Binary Target File")
        open_action.triggered.connect(self.select_file)
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        analysis_menu = menubar.addMenu("Analysis")
        anal_action = analysis_menu.addAction("Refresh Flow-Chart View")
        anal_action.triggered.connect(lambda: self.draw_graph(self.current_blocks))

        ai_menu = menubar.addMenu("AI Tools")
        report_action = ai_menu.addAction("Generate Comprehensive AI Report")
        report_action.triggered.connect(self.run_ai_audit)

        # Central Layout Splitters
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(main_splitter)

        # LEFT PANE: Directory & Metadata Information
        left_pane = QFrame()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        left_layout.addWidget(QLabel("TARGET ANALYSIS FILE"))
        self.file_label = QLabel("No Target Loaded (Using Welcome Demo Graph)")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet("color: #00FF66; font-size: 11px;")
        left_layout.addWidget(self.file_label)
        
        left_layout.addWidget(QLabel("ANALYSIS DEPTH"))
        self.depth_selector = QComboBox()
        self.depth_selector.addItems(["1 KB (Recommended)", "4 KB (Medium)", "16 KB (Deep)"])
        left_layout.addWidget(self.depth_selector)

        left_layout.addWidget(QLabel("EXTRACTED SYMBOL BLOCKS"))
        self.block_list = QListWidget()
        self.block_list.itemClicked.connect(self.jump_to_block)
        left_layout.addWidget(self.block_list)

        # CENTER PANE: Flow Chart Engine Graph View
        center_pane = QFrame()
        center_layout = QVBoxLayout(center_pane)
        center_layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.graph_view = GraphView(self.scene)
        center_layout.addWidget(self.graph_view)

        # RIGHT PANE: Dynamic AI Assistant Portal
        right_pane = QFrame()
        right_layout = QVBoxLayout(right_pane)
        right_layout.setContentsMargins(10, 10, 10, 10)
        
        right_layout.addWidget(QLabel("NOVARE LLAMA-3.3 INTELLIGENT AI"))
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setHtml(
            "<span style='color: #8F93A2;'>Welcome to NovaRE AI! Drag and drop or open a binary to reverse-engineer it using AI-powered Control Flow Analysis. Let's inspect the target.</span>"
        )
        right_layout.addWidget(self.chat_area)
        
        chat_input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask AI about disassembly logic, vulnerabilities...")
        self.chat_input.returnPressed.connect(self.send_chat_message)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_chat_message)
        chat_input_layout.addWidget(self.chat_input)
        chat_input_layout.addWidget(self.send_btn)
        right_layout.addLayout(chat_input_layout)

        # Audit Accelerator Button
        self.audit_btn = QPushButton("🚀 Run Deep Cyber Audit (AI)")
        self.audit_btn.clicked.connect(self.run_ai_audit)
        right_layout.addWidget(self.audit_btn)

        # Splitter Layout allocation
        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(center_pane)
        main_splitter.addWidget(right_pane)
        main_splitter.setSizes([260, 680, 360])

        # Bottom Bar setup
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Engine Idle. Ready to parse x86_64 target files.")

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Executable File", "", "All Files (*)")
        if file_path:
            self.current_file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.status_bar.showMessage(f"Disassembling {file_path}...")
            
            try:
                self.parse_and_disassemble(file_path)
                self.status_bar.showMessage(f"Successfully disassembled and generated flowchart blocks for {os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Disassembler Error", f"Failed to parse binary structure: {str(e)}")
                self.status_bar.showMessage("Decompilation aborted.")

    def parse_and_disassemble(self, file_path):
        # Extract entrypoint or fallbacks
        entry_offset = 0
        pe_extracted = False
        try:
            pe = pefile.PE(file_path)
            entry_offset = pe.OPTIONAL_HEADER.AddressOfEntryPoint
            for section in pe.sections:
                if section.VirtualAddress <= entry_offset < section.VirtualAddress + section.Misc_VirtualSize:
                    entry_offset = section.PointerToRawData + (entry_offset - section.VirtualAddress)
                    break
            pe_extracted = True
        except Exception:
            entry_offset = 0

        # Read binary chunk from selected depth
        depth_map = {0: 1024, 1: 4096, 2: 16384}
        chunk_size = depth_map.get(self.depth_selector.currentIndex(), 1024)
        
        with open(file_path, 'rb') as f:
            f.seek(entry_offset)
            raw_bytes = f.read(chunk_size)

        # Capstone disassembler engine setup
        md = Cs(CS_ARCH_X86, CS_MODE_64)
        instructions = list(md.disasm(raw_bytes, entry_offset))

        if not instructions:
            raise ValueError("No valid x86/x64 instructions extracted from file.")

        # Rebuild Basic Control Blocks (Control Flow Graph Parser)
        blocks = []
        current_list = []
        block_idx = 0

        for inst in instructions:
            current_list.append((inst.address, inst.mnemonic, inst.op_str))
            
            # Check for conditional and unconditional branch conditions
            is_control_flow = inst.mnemonic in [
                'jmp', 'je', 'jne', 'jz', 'jnz', 'jg', 'jge', 'jl', 'jle', 
                'call', 'ret', 'loop', 'js', 'jns', 'jo', 'jno', 'jb', 'ja'
            ]
            
            if is_control_flow or len(current_list) >= 14:
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

        # Relational flow linker mappings
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
        self.draw_graph(self.current_blocks)

    def parse_operand_address(self, op_str):
        try:
            if op_str.startswith("0x"):
                return int(op_str, 16)
            return int(op_str)
        except ValueError:
            return None

    def draw_graph(self, blocks):
        self.scene.clear()
        self.block_list.clear()
        
        if not blocks:
            return

        # Simple hierarchical graph auto-layout algorithm
        levels = {}
        def compute_depth(node_id, current_level, visited):
            if node_id in visited:
                return
            visited.add(node_id)
            levels[node_id] = max(levels.get(node_id, 0), current_level)
            for target_id, _ in blocks[node_id]["next_blocks"]:
                compute_depth(target_id, current_level + 1, visited.copy())

        compute_depth(0, 0, set())

        level_groups = {}
        for b_id in range(len(blocks)):
            lvl = levels.get(b_id, 0)
            if lvl not in level_groups:
                level_groups[lvl] = []
            level_groups[lvl].append(b_id)

        pos_map = {}
        node_width = 300
        gap_x = 80
        gap_y = 190

        # Position nodes neatly in their respective depth tier
        for lvl, b_ids in level_groups.items():
            count = len(b_ids)
            total_w = count * node_width + (count - 1) * gap_x
            offset_x = -total_w / 2
            
            for idx, b_id in enumerate(b_ids):
                x = offset_x + idx * (node_width + gap_x)
                y = lvl * gap_y
                pos_map[b_id] = (x, y)

        self.node_items = {}
        for b in blocks:
            b_id = b["id"]
            x, y = pos_map[b_id]
            node = NodeItem(b["title"], b["instructions"], x, y)
            self.scene.addItem(node)
            self.node_items[b_id] = node
            self.block_list.addItem(b["title"])

        # Link blocks visually based on computed flow
        for b in blocks:
            b_id = b["id"]
            for target_id, link_type in b["next_blocks"]:
                if target_id in self.node_items:
                    color = QColor("#5C6370")
                    if link_type == "true":
                        color = QColor("#00FF66")  # Green for positive evaluation paths
                    elif link_type == "false":
                        color = QColor("#FF4A6B")  # Red for negative evaluation paths
                    elif link_type == "unconditional":
                        color = QColor("#00C0FF")  # Cyan for unconditional loops/jumps
                    
                    edge = EdgeItem(self.node_items[b_id], self.node_items[target_id], color)
                    self.scene.addItem(edge)

        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-150, -150, 150, 150))

    def jump_to_block(self, item):
        title = item.text()
        for b_id, node in self.node_items.items():
            if node.title == title:
                self.graph_view.centerOn(node)
       
