package com.hackaton.re_cicla2.ui.screens

import android.Manifest
import android.util.Log
import android.view.ViewGroup
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import com.hackaton.re_cicla2.auth.AuthViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ScannerScreen(
    viewModel: AuthViewModel,
    onNavigateBack: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var detectedLabel by remember { mutableStateOf("Buscando material...") }
    var detectedType by remember { mutableStateOf<String?>(null) }
    var quantity by remember { mutableIntStateOf(1) }
    var showSuccessDialog by remember { mutableStateOf(false) }

    // Opciones para selección manual si falla la IA
    val materialOptions = listOf("Plástico", "Papel/Cartón", "Vidrio", "Metal")
    var showManualSelection by remember { mutableStateOf(false) }

    // Pedir permiso de cámara
    val permissionLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestPermission()
    ) { }

    LaunchedEffect(Unit) {
        permissionLauncher.launch(Manifest.permission.CAMERA)
    }

    if (showSuccessDialog) {
        AlertDialog(
            onDismissRequest = { 
                showSuccessDialog = false
                onNavigateBack() 
            },
            confirmButton = {
                TextButton(onClick = { 
                    showSuccessDialog = false
                    onNavigateBack() 
                }) { Text("Volver al Inicio", color = MaterialTheme.colorScheme.primary) }
            },
            title = { Text("¡Puntos Sumados!", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface) },
            text = { Text("Has sumado puntos por reciclar $quantity unidad(es) de ${detectedType ?: "este material"}.", color = MaterialTheme.colorScheme.onSurface) },
            shape = RoundedCornerShape(20.dp),
            containerColor = MaterialTheme.colorScheme.surface
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Escanear Residuo", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface) },
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
            // Camera Preview
            AndroidView(
                factory = { ctx ->
                    val previewView = PreviewView(ctx).apply {
                        layoutParams = ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT
                        )
                    }
                    val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)
                    cameraProviderFuture.addListener({
                        val cameraProvider = cameraProviderFuture.get()
                        val preview = Preview.Builder().build().also {
                            it.surfaceProvider = previewView.surfaceProvider
                        }
                        
                        val imageAnalyzer = ImageAnalysis.Builder()
                            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                            .build()
                            .also { analyzer ->
                                analyzer.setAnalyzer(ContextCompat.getMainExecutor(ctx)) { imageProxy ->
                                    processImageProxy(imageProxy) { label, type ->
                                        detectedLabel = label
                                        detectedType = type
                                    }
                                }
                            }

                        try {
                            cameraProvider.unbindAll()
                            cameraProvider.bindToLifecycle(
                                lifecycleOwner,
                                CameraSelector.DEFAULT_BACK_CAMERA,
                                preview,
                                imageAnalyzer
                            )
                        } catch (e: Exception) {
                            Log.e("ScannerScreen", "Camera binding failed", e)
                        }
                    }, ContextCompat.getMainExecutor(ctx))
                    previewView
                },
                modifier = Modifier.fillMaxSize()
            )

            // Overlay de Control
            Column(
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .fillMaxWidth()
                    .padding(24.dp)
                    .background(
                        MaterialTheme.colorScheme.surface.copy(alpha = 0.9f), 
                        RoundedCornerShape(24.dp)
                    )
                    .padding(20.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = if (detectedType != null) "Material Detectado:" else "Analizando...",
                    style = MaterialTheme.typography.labelLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = detectedType ?: detectedLabel,
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.ExtraBold,
                    color = if (detectedType != null) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
                )

                if (detectedType == null) {
                    TextButton(onClick = { showManualSelection = !showManualSelection }) {
                        Text(
                            if (showManualSelection) "Ocultar opciones" else "¿No se reconoce? Seleccionar manualmente", 
                            color = MaterialTheme.colorScheme.primary,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                if (showManualSelection && detectedType == null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly) {
                        materialOptions.forEach { option ->
                            SuggestionChip(
                                onClick = { 
                                    detectedType = option
                                    showManualSelection = false
                                },
                                label = { Text(option, fontSize = 10.sp) },
                                colors = SuggestionChipDefaults.suggestionChipColors(
                                    labelColor = MaterialTheme.colorScheme.onSurface
                                )
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    IconButton(onClick = { if (quantity > 1) quantity-- }) {
                        Icon(Icons.Default.Remove, contentDescription = null, tint = MaterialTheme.colorScheme.onSurface)
                    }
                    Text(
                        text = "$quantity",
                        color = MaterialTheme.colorScheme.onSurface,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 16.dp)
                    )
                    IconButton(onClick = { quantity++ }) {
                        Icon(Icons.Default.Add, contentDescription = null, tint = MaterialTheme.colorScheme.onSurface)
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                Button(
                    onClick = {
                        val material = detectedType ?: detectedLabel
                        val pointsToAdd = when {
                            material.contains("Plástico", true) || material.contains("bottle", true) -> 10 * quantity
                            material.contains("Papel", true) || material.contains("paper", true) -> 5 * quantity
                            material.contains("Vidrio", true) || material.contains("glass", true) -> 20 * quantity
                            material.contains("Metal", true) || material.contains("can", true) -> 15 * quantity
                            else -> 5 * quantity
                        }
                        viewModel.addPointsFromScanner(material, pointsToAdd)
                        showSuccessDialog = true
                    },
                    enabled = detectedType != null || (detectedLabel != "Buscando material..." && detectedLabel != "Buscando..."),
                    modifier = Modifier.fillMaxWidth().height(56.dp),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = MaterialTheme.colorScheme.primary,
                        contentColor = Color.White
                    )
                ) {
                    Text("Confirmar y Reciclar", fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
private fun processImageProxy(
    imageProxy: ImageProxy,
    onLabelDetected: (String, String?) -> Unit
) {
    val mediaImage = imageProxy.image
    if (mediaImage != null) {
        val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
        
        // Configuramos el labeler con un umbral de confianza más alto
        val options = ImageLabelerOptions.Builder()
            .setConfidenceThreshold(0.6f)
            .build()
        val labeler = ImageLabeling.getClient(options)
        
        labeler.process(image)
            .addOnSuccessListener { labels ->
                val topLabel = labels.firstOrNull()
                val labelText = topLabel?.text ?: "Analizando..."
                
                // Mapeo inteligente con traducción a español
                val (translatedLabel, type) = when {
                    labelText.lowercase().contains("bottle") || labelText.lowercase().contains("plastic") -> "Plástico" to "Plástico"
                    labelText.lowercase().contains("paper") || labelText.lowercase().contains("box") || labelText.lowercase().contains("cardboard") -> "Papel/Cartón" to "Papel/Cartón"
                    labelText.lowercase().contains("glass") -> "Vidrio" to "Vidrio"
                    labelText.lowercase().contains("can") || labelText.lowercase().contains("tin") || labelText.lowercase().contains("metal") -> "Metal" to "Metal"
                    else -> "Objeto no reciclable" to null
                }
                
                onLabelDetected(translatedLabel, type)
            }
            .addOnCompleteListener {
                imageProxy.close()
            }
    } else {
        imageProxy.close()
    }
}
