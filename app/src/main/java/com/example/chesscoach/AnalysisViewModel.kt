package com.example.chesscoach

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow

data class AnalysisState(val fen: String = STARTING_FEN, val loading: Boolean = false, val error: String? = null, val result: EngineResult? = null)
data class EngineResult(val move: String, val evaluation: String, val depth: Int, val explanation: String)

/** Boundary for a local UCI adapter. It never interacts with other apps or the system input layer. */
interface LocalEngine { suspend fun bestMove(fen: String): EngineResult }

class DemoEngine : LocalEngine {
    override suspend fun bestMove(fen: String) = EngineResult("e2–e4", "+0.20", 12, "Controls the centre and opens lines for development.")
}

class AnalysisViewModel(private val engine: LocalEngine = DemoEngine()) : ViewModel() {
    private val _state = MutableStateFlow(AnalysisState())
    val state = _state.asStateFlow()
    fun setFen(value: String) { _state.value = _state.value.copy(fen = value, error = null, result = null) }
    fun analyse() {
        val fen = _state.value.fen.trim()
        if (!isValidFen(fen)) { _state.value = _state.value.copy(error = "Enter a complete six-field FEN position."); return }
        _state.value = _state.value.copy(loading = true, error = null)
        viewModelScope.launch {
            val recommendation = engine.bestMove(fen)
            _state.value = _state.value.copy(loading = false, result = recommendation)
        }
    }
    private fun isValidFen(fen: String): Boolean = fen.split(Regex("\\s+")).size == 6 && fen.substringBefore(' ').split('/').size == 8
}
