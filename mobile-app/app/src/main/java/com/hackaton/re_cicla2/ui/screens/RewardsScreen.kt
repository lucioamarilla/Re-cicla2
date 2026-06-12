package com.hackaton.re_cicla2.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.CreditCard
import androidx.compose.material.icons.filled.DirectionsBus
import androidx.compose.material.icons.filled.WaterDrop
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.hackaton.re_cicla2.auth.AuthViewModel

data class RewardOption(
    val title: String,
    val description: String,
    val cost: Int,
    val icon: ImageVector
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RewardsScreen(
    points: Int,
    viewModel: AuthViewModel,
    onNavigateBack: () -> Unit
) {
    // Nuevas opciones locales: SUBE, SAMSA, SEM
    val rewards = listOf(
        RewardOption("Carga SUBE Misionera", "Acredita saldo en tu tarjeta", 100, Icons.Default.DirectionsBus),
        RewardOption("Descuento SAMSA", "Cupón para tu factura de agua", 500, Icons.Default.WaterDrop),
        RewardOption("Saldo SEM Posadas", "Carga para estacionamiento medido", 150, Icons.Default.CreditCard)
    )

    var showSuccessDialog by remember { mutableStateOf<String?>(null) }

    if (showSuccessDialog != null) {
        AlertDialog(
            onDismissRequest = { showSuccessDialog = null },
            confirmButton = {
                TextButton(onClick = { showSuccessDialog = null }) {
                    Text("Cerrar", color = MaterialTheme.colorScheme.primary)
                }
            },
            title = { Text("¡Canje Exitoso!", color = MaterialTheme.colorScheme.onSurface) },
            text = { Text("Has canjeado: $showSuccessDialog\nEl beneficio se acreditará en las próximas 24hs.", color = MaterialTheme.colorScheme.onSurface) },
            shape = RoundedCornerShape(20.dp),
            containerColor = MaterialTheme.colorScheme.surface
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Canjear Puntos", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSurface) },
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            // Header con puntos actuales
            Surface(
                modifier = Modifier.fillMaxWidth().padding(16.dp),
                shape = RoundedCornerShape(16.dp),
                color = MaterialTheme.colorScheme.primary
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("Tus puntos disponibles:", color = Color.White)
                    Text("$points pts", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
            }

            Text(
                "Opciones en Misiones",
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onBackground
            )

            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(rewards) { reward ->
                    RewardItem(
                        reward = reward,
                        canAfford = points >= reward.cost,
                        onRedeem = {
                            viewModel.redeemPoints(reward.title, reward.cost)
                            showSuccessDialog = reward.title
                        }
                    )
                }
            }
        }
    }
}

@Composable
fun RewardItem(
    reward: RewardOption,
    canAfford: Boolean,
    onRedeem: () -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = MaterialTheme.colorScheme.surface,
        shadowElevation = 1.dp
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .background(
                        if (canAfford) MaterialTheme.colorScheme.primary.copy(alpha = 0.1f) 
                        else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f), 
                        RoundedCornerShape(12.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    reward.icon,
                    contentDescription = null,
                    tint = if (canAfford) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface.copy(alpha = 0.4f)
                )
            }
            
            Spacer(modifier = Modifier.width(16.dp))
            
            Column(modifier = Modifier.weight(1f)) {
                Text(reward.title, fontWeight = FontWeight.Bold, fontSize = 16.sp, color = MaterialTheme.colorScheme.onSurface)
                Text(reward.description, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text("${reward.cost} pts", fontWeight = FontWeight.SemiBold, color = MaterialTheme.colorScheme.primary, fontSize = 14.sp)
            }
            
            Button(
                onClick = onRedeem,
                enabled = canAfford,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.primary,
                    contentColor = Color.White,
                    disabledContainerColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.1f),
                    disabledContentColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f)
                ),
                shape = RoundedCornerShape(10.dp)
            ) {
                Text("Canjear", fontSize = 12.sp)
            }
        }
    }
}
