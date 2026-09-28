package com.example.chesscoach

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.weight
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Psychology
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { ChessMentorApp() }
    }
}

private val Ink = Color(0xFF17212B)
private val Navy = Color(0xFF1D3557)
private val Mint = Color(0xFF83D6C6)
private val BoardLight = Color(0xFFF0D9B5)
private val BoardDark = Color(0xFFB58863)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChessMentorApp() {
    var page by remember { mutableStateOf(0) }
    MaterialTheme(colorScheme = MaterialTheme.colorScheme.copy(primary = Navy, secondary = Mint)) {
        Scaffold(
            topBar = { TopAppBar(title = { Text("Chess Mentor", fontWeight = FontWeight.Bold) }) },
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(selected = page == 0, onClick = { page = 0 }, icon = { Icon(Icons.Outlined.Psychology, null) }, label = { Text("Analiz") })
                    NavigationBarItem(selected = page == 1, onClick = { page = 1 }, icon = { Icon(Icons.Outlined.MenuBook, null) }, label = { Text("Açılışlar") })
                    NavigationBarItem(selected = page == 2, onClick = { page = 2 }, icon = { Icon(Icons.Outlined.Settings, null) }, label = { Text("Ayarlar") })
                }
            }
        ) { padding ->
            Surface(modifier = Modifier.fillMaxSize().padding(padding), color = MaterialTheme.colorScheme.surface) {
                when (page) {
                    0 -> AnalysisScreen()
                    1 -> OpeningsScreen()
                    else -> SettingsScreen()
                }
            }
        }
    }
}

@Composable
private fun AnalysisScreen() {
    var board by remember { mutableStateOf(startingBoard()) }
    var selected by remember { mutableStateOf<String?>(null) }
    var showFen by remember { mutableStateOf(false) }
    var status by remember { mutableStateOf("Başlangıç konumu · Beyaz oynar") }
    val suggestion = when {
        board["e4"] == "♙" -> "♞f6 — Gelişimi tamamlayın ve e4 piyonuna baskı yapın."
        board["d4"] == "♙" -> "♞f6 — Merkeze karşı esnek bir gelişim hamlesi."
        else -> "e4 — Merkezi kontrol edin ve filiniz için yol açın."
    }
    LazyColumn(modifier = Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
        item {
            Text("Tahta analizi", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold, color = Ink)
            Text("Konumu dokunarak kurun veya FEN ile içe aktarın.", color = Color(0xFF59636E))
        }
        item { ChessBoard(board, selected) { square ->
            val piece = board[square]
            if (selected == null && piece != null) {
                selected = square
                status = "$square karesi seçildi. Hedef kareye dokunun."
            } else if (selected != null) {
                val from = selected!!
                board = board.toMutableMap().apply { put(square, remove(from)!!) }
                selected = null
                status = "$from → $square işlendi · Sıra rakipte"
            }
        } }
        item { Text(status, modifier = Modifier.fillMaxWidth(), textAlign = TextAlign.Center, color = Navy, fontWeight = FontWeight.Medium) }
        item {
            Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFE6F5F1)), shape = RoundedCornerShape(18.dp)) {
                Column(Modifier.padding(18.dp)) {
                    Text("Önerilen hamle", color = Navy, fontWeight = FontWeight.Bold)
                    Spacer(Modifier.height(5.dp))
                    Text(suggestion, fontSize = 17.sp, fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(8.dp))
                    Text("İpucu: Şah güvenliğini koruyun, taşlarınızı geliştirin ve aynı taşı gereksiz yere iki kez oynamayın.")
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp), modifier = Modifier.fillMaxWidth()) {
                Button(onClick = { showFen = true }, modifier = Modifier.weight(1f)) { Text("FEN gir") }
                OutlinedButton(onClick = { board = startingBoard(); status = "Tahta başlangıç konumuna döndü" }, modifier = Modifier.weight(1f)) { Text("Sıfırla") }
            }
        }
        item { SafetyNote() }
    }
    if (showFen) FenDialog(onDismiss = { showFen = false }, onImport = { imported -> board = imported; status = "FEN konumu içe aktarıldı"; showFen = false })
}

@Composable
private fun ChessBoard(board: Map<String, String>, selected: String?, onSquare: (String) -> Unit) {
    Column(Modifier.fillMaxWidth().semantics { contentDescription = "İnteraktif satranç tahtası" }) {
        for (rank in 8 downTo 1) {
            Row(Modifier.fillMaxWidth()) {
                for (file in "abcdefgh") {
                    val square = "$file$rank"
                    val dark = ((file.code - 'a'.code) + rank) % 2 == 1
                    Box(
                        modifier = Modifier.weight(1f).aspectSquare().background(if (dark) BoardDark else BoardLight)
                            .then(if (selected == square) Modifier.border(3.dp, Mint) else Modifier)
                            .clickable { onSquare(square) }.semantics { contentDescription = "$square ${board[square] ?: "boş"}" },
                        contentAlignment = Alignment.Center
                    ) { Text(board[square] ?: "", fontSize = 30.sp) }
                }
            }
        }
        Row(Modifier.fillMaxWidth()) { "a b c d e f g h".split(" ").forEach { Text(it, Modifier.weight(1f), textAlign = TextAlign.Center, color = Color.Gray) } }
    }
}

private fun Modifier.aspectSquare() = this.then(Modifier.height(45.dp))

@Composable
private fun FenDialog(onDismiss: () -> Unit, onImport: (Map<String, String>) -> Unit) {
    var fen by remember { mutableStateOf("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1") }
    AlertDialog(onDismissRequest = onDismiss, title = { Text("FEN konumu gir") }, text = {
        Column { Text("Ekrandaki konumu FEN olarak buraya yapıştırın. Uygulama başka uygulamaları okumaz.", fontSize = 13.sp); OutlinedTextField(fen, { fen = it }, label = { Text("FEN") }, minLines = 3) }
    }, confirmButton = { Button(onClick = { parseFen(fen)?.let(onImport) }) { Text("İçe aktar") } }, dismissButton = { OutlinedButton(onClick = onDismiss) { Text("Vazgeç") } })
}

@Composable private fun OpeningsScreen() = LazyColumn(Modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
    item { Text("Açılış rehberi", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold) }
    item { OpeningCard("İtalyan", "1. e4 e5 2. Af3 Ac6 3. Fc4", "Hızlı gelişim ve f7 karesine baskı.") }
    item { OpeningCard("Sicilya", "1. e4 c5", "Beyaza karşı dinamik, asimetrik mücadele.") }
    item { OpeningCard("Vezir Gambiti", "1. d4 d5 2. c4", "Merkez alanı ve uzun vadeli baskı.") }
}
@Composable private fun OpeningCard(name: String, moves: String, description: String) = Card { Column(Modifier.padding(16.dp)) { Text(name, fontWeight = FontWeight.Bold, fontSize = 18.sp); Text(moves, color = Navy, fontWeight = FontWeight.SemiBold); Text(description) } }
@Composable private fun SettingsScreen() = Column(Modifier.fillMaxSize().padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) { Text("Uygulama ayarları", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold); Text("Chess Mentor, konumları yalnızca sizin uygulama içinde girdiğiniz veriden analiz eder."); SafetyNote() }
@Composable private fun SafetyNote() = Card(colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF4D8))) { Text("Adil oyun notu: Bu araç eğitim ve maç sonrası analiz içindir. Çevrimiçi oyun sırasında sitelerin yardım/engine kurallarına uyun.", Modifier.padding(14.dp), fontSize = 13.sp) }

private fun startingBoard(): Map<String, String> = buildMap {
    "abcdefgh".forEachIndexed { i, f -> put("$f2", "♙"); put("$f7", "♟"); put("$f1", "♖♘♗♕♔♗♘♖"[i].toString()); put("$f8", "♜♞♝♛♚♝♞♜"[i].toString()) }
}
private fun parseFen(fen: String): Map<String, String>? = runCatching {
    val result = mutableMapOf<String, String>(); val rows = fen.trim().split(" ").first().split("/"); require(rows.size == 8)
    rows.forEachIndexed { rowIndex, row -> var file = 0; row.forEach { char -> if (char.isDigit()) file += char.digitToInt() else { require(file < 8); result["${('a'.code + file).toChar()}${8 - rowIndex}"] = piece(char); file++ } }; require(file == 8) }; result
}.getOrNull()
private fun piece(c: Char) = mapOf('P' to "♙", 'N' to "♘", 'B' to "♗", 'R' to "♖", 'Q' to "♕", 'K' to "♔", 'p' to "♟", 'n' to "♞", 'b' to "♝", 'r' to "♜", 'q' to "♛", 'k' to "♚").getValue(c)
