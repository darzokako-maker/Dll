package com.example.chesscoach

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.AutoAwesome
import androidx.compose.material.icons.outlined.MenuBook
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel

private val Ink = Color(0xFF0E1512)
private val Moss = Color(0xFF1C2B22)
private val Gold = Color(0xFFD7B56D)
private val Cream = Color(0xFFF5F0E5)
private const val STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) = super.onCreate(savedInstanceState)
        setContent { ChessCoachTheme { ChessCoachApp() } }
}

@Composable private fun ChessCoachTheme(content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = darkColorScheme(primary = Gold, secondary = Color(0xFF9BBE8A), surface = Moss, onSurface = Cream), content = content)
}

private enum class Screen { ANALYSE, LIBRARY, SETTINGS }

@Composable private fun ChessCoachApp(model: AnalysisViewModel = viewModel()) {
    var screen by rememberSaveable { mutableStateOf(Screen.ANALYSE) }
    Scaffold(
        containerColor = Ink,
        bottomBar = {
            NavigationBar(containerColor = Moss) {
                listOf(
                    Screen.ANALYSE to "Analyse", Screen.LIBRARY to "Library", Screen.SETTINGS to "Settings"
                ).forEach { (item, label) ->
                    NavigationBarItem(selected = item == screen, onClick = { screen = item }, label = { Text(label) }, icon = {
                        when (item) { Screen.ANALYSE -> Icon(Icons.Outlined.AutoAwesome, null); Screen.LIBRARY -> Icon(Icons.Outlined.MenuBook, null); Screen.SETTINGS -> Icon(Icons.Outlined.Settings, null) }
                    })
                }
            }
        }
    ) { padding ->
        when (screen) {
            Screen.ANALYSE -> AnalyseScreen(model, Modifier.padding(padding))
            Screen.LIBRARY -> PlaceholderScreen("Study library", "Saved positions and your own game notes will appear here.", Modifier.padding(padding))
            Screen.SETTINGS -> PlaceholderScreen("Settings", "Configure a local UCI engine adapter before analysing serious positions.", Modifier.padding(padding))
        }
    }
}

@Composable private fun AnalyseScreen(model: AnalysisViewModel, modifier: Modifier) {
    val state by model.state.collectAsState()
    Column(modifier.fillMaxSize().padding(horizontal = 20.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        Spacer(Modifier.height(8.dp))
        Text("CHESS COACH", color = Gold, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
        Text("Position analysis", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Text("Private, local analysis for study positions you control.", color = Cream.copy(alpha = .72f))
        ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = Moss), shape = RoundedCornerShape(20.dp)) {
            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text("FEN position", fontWeight = FontWeight.SemiBold)
                OutlinedTextField(value = state.fen, onValueChange = model::setFen, modifier = Modifier.fillMaxWidth(), minLines = 3, label = { Text("Paste FEN") }, supportingText = { Text(state.error ?: "The position stays on this device.") })
                Button(onClick = model::analyse, modifier = Modifier.fillMaxWidth(), enabled = !state.loading, colors = ButtonDefaults.buttonColors(containerColor = Gold, contentColor = Ink)) {
                    Text(if (state.loading) "Analysing…" else "Analyse position", fontWeight = FontWeight.Bold)
                }
            }
        }
        state.result?.let { ResultCard(it) }
        Text("No screen capture · No overlays · No input automation", modifier = Modifier.fillMaxWidth(), color = Cream.copy(alpha = .55f), textAlign = TextAlign.Center, style = MaterialTheme.typography.labelMedium)
    }
}

@Composable private fun ResultCard(result: EngineResult) {
    ElevatedCard(colors = CardDefaults.elevatedCardColors(containerColor = Color(0xFF23362A)), shape = RoundedCornerShape(20.dp)) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("ENGINE RECOMMENDATION", color = Gold, style = MaterialTheme.typography.labelLarge, fontWeight = FontWeight.Bold)
            Text(result.move, style = MaterialTheme.typography.displaySmall, fontWeight = FontWeight.Bold)
            Text(result.explanation, color = Cream.copy(alpha = .8f))
            Text("Depth ${result.depth}  •  ${result.evaluation}", color = Color(0xFFB7D6A8), style = MaterialTheme.typography.labelMedium)
        }
    }
}

@Composable private fun PlaceholderScreen(title: String, detail: String, modifier: Modifier) {
    Column(modifier.fillMaxSize().padding(28.dp), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
        Text(title, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(12.dp)); Text(detail, textAlign = TextAlign.Center, color = Cream.copy(alpha = .7f))
    }
}
