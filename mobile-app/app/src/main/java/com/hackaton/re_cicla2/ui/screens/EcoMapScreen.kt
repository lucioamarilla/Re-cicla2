package com.hackaton.re_cicla2.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.google.android.gms.maps.model.CameraPosition
import com.google.android.gms.maps.model.LatLng
import com.google.maps.android.compose.*

data class EcoPunto(
    val name: String,
    val location: LatLng
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EcoMapScreen(onNavigateBack: () -> Unit) {
    // Lista de EcoPuntos extraídos del CSV oficial de Posadas, Misiones
    val ecoPuntos = listOf(
        EcoPunto("EcoPunto Av. Urquiza", LatLng(-27.360188, -55.915428)),
        EcoPunto("Cascada Artificial", LatLng(-27.382625, -55.887976)),
        EcoPunto("Itaembé Miní", LatLng(-27.414570, -55.955911)),
        EcoPunto("Itaembé Guazú", LatLng(-27.408196, -55.984417)),
        EcoPunto("Parque Sarmiento", LatLng(-27.366101, -55.945117)),
        EcoPunto("Feria Puente Chacabuco", LatLng(-27.370316, -55.885132)),
        EcoPunto("Av. Martín Fierro & Av. Aguado", LatLng(-27.381243, -55.926309)),
        EcoPunto("Avenida Juan Domingo Perón & América Latina", LatLng(-27.430654, -55.883281)),
        EcoPunto("EcoPunto Barrio Los Álamos", LatLng(-27.414691, -55.930462)),
        EcoPunto("EcoPunto Dolores Sur", LatLng(-27.433390, -55.914755))
    )

    val posadas = LatLng(-27.3671, -55.8961)
    val cameraPositionState = rememberCameraPositionState {
        position = CameraPosition.fromLatLngZoom(posadas, 12f)
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("EcoPuntos en Misiones", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = null, tint = MaterialTheme.colorScheme.onSurface)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { padding ->
        Box(modifier = Modifier.fillMaxSize().padding(padding)) {
            GoogleMap(
                modifier = Modifier.fillMaxSize(),
                cameraPositionState = cameraPositionState
            ) {
                ecoPuntos.forEach { punto ->
                    Marker(
                        state = MarkerState(position = punto.location),
                        title = punto.name,
                        snippet = "Punto de reciclaje"
                    )
                }
            }

            // Mensaje de ayuda si el mapa no carga
            Surface(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(24.dp),
                shape = RoundedCornerShape(12.dp),
                color = MaterialTheme.colorScheme.surface.copy(alpha = 0.9f)
            ) {
                Text(
                    text = "Si no ves el mapa, verifica tu API Key de Google Maps en AndroidManifest.xml",
                    color = MaterialTheme.colorScheme.onSurface,
                    modifier = Modifier.padding(12.dp),
                    fontSize = 12.sp,
                    textAlign = androidx.compose.ui.text.style.TextAlign.Center
                )
            }
        }
    }
}
