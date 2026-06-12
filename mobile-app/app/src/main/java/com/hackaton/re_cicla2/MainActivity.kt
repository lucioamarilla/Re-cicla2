package com.hackaton.re_cicla2

import android.content.Intent
import android.os.Bundle
import android.util.Log
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.common.api.ApiException
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.runtime.LaunchedEffect
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.hackaton.re_cicla2.auth.AuthState
import com.hackaton.re_cicla2.auth.AuthViewModel
import com.hackaton.re_cicla2.ui.screens.*
import com.hackaton.re_cicla2.ui.theme.Recicla2Theme

class MainActivity : ComponentActivity() {
    private lateinit var authViewModel: AuthViewModel

    private val googleSignInLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        val task = GoogleSignIn.getSignedInAccountFromIntent(result.data)
        try {
            val account = task.getResult(ApiException::class.java)
            authViewModel.handleGoogleSignInResult(account)
        } catch (e: ApiException) {
            authViewModel.onGoogleSignInError(e)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            authViewModel = viewModel()
            Recicla2Theme {
                MainApp(authViewModel, googleSignInLauncher)
            }
        }
    }
}

@Composable
fun MainApp(authViewModel: AuthViewModel, googleSignInLauncher: androidx.activity.result.ActivityResultLauncher<Intent>) {
    val navController = rememberNavController()
    val authState by authViewModel.authState.collectAsState()

    val startDestination = remember {
        if (authViewModel.isUserLoggedIn()) "home" else "login"
    }

    LaunchedEffect(authState) {
        if (authState is AuthState.Idle) {
            navController.navigate("login") {
                popUpTo(0) { inclusive = true }
            }
        }
    }

    NavHost(navController = navController, startDestination = startDestination) {
        composable("login") {
            LoginScreen(
                viewModel = authViewModel,
                googleSignInLauncher = googleSignInLauncher,
                onNavigateToRegister = { navController.navigate("register") },
                onLoginSuccess = { _, _ ->
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }
        composable("register") {
            RegisterScreen(
                viewModel = authViewModel,
                googleSignInLauncher = googleSignInLauncher,
                onNavigateToLogin = { navController.popBackStack() },
                onRegisterSuccess = { _, _ ->
                    navController.navigate("home") {
                        popUpTo("login") { inclusive = true }
                    }
                }
            )
        }
        composable("home") {
            val successState = authState as? AuthState.Success
            HomeScreen(
                userName = successState?.userName,
                codigo = successState?.codigo ?: "",
                saldo = successState?.saldo ?: 0,
                transactions = successState?.transactions ?: emptyList(),
                viewModel = authViewModel,
                onSignOut = { },
                onNavigateToRewards = { navController.navigate("rewards") },
                onNavigateToQr = { navController.navigate("qr") },
                onNavigateToScanner = { navController.navigate("scanner") },
                onNavigateToMap = { navController.navigate("map") }
            )
        }
        composable("qr") {
            val successState = authState as? AuthState.Success
            QrCodeScreen(
                userName = successState?.userName,
                codigo = successState?.codigo ?: "",
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable("rewards") {
            val successState = authState as? AuthState.Success
            RewardsScreen(
                saldo = successState?.saldo ?: 0,
                viewModel = authViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable("scanner") {
            ScannerScreen(
                viewModel = authViewModel,
                onNavigateBack = { navController.popBackStack() }
            )
        }
        composable("map") {
            EcoMapScreen(onNavigateBack = { navController.popBackStack() })
        }
    }
}
