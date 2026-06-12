package com.hackaton.re_cicla2.auth

import android.content.Context
import android.content.Intent
import android.util.Log
import androidx.credentials.ClearCredentialStateRequest
import androidx.credentials.CredentialManager
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.android.gms.auth.api.signin.GoogleSignIn
import com.google.android.gms.auth.api.signin.GoogleSignInAccount
import com.google.android.gms.auth.api.signin.GoogleSignInOptions
import com.google.android.gms.common.api.ApiException
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.GoogleAuthProvider
import com.google.firebase.auth.UserProfileChangeRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await

import java.util.Date
import java.text.SimpleDateFormat
import java.util.Locale

data class Transaction(
    val id: String,
    val title: String,
    val amount: Int, // Positivo para ganar, Negativo para gastar
    val date: String,
    val isGain: Boolean
)

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Success(
        val userName: String?, 
        val userCode: String,
        val userId: String = "",
        val points: Int = 1284,
        val transactions: List<Transaction> = emptyList()
    ) : AuthState()
    data class Error(val message: String) : AuthState()
}

class AuthViewModel : ViewModel() {
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
    
    // Web Client ID from google-services.json
    private val webClientId = "593104803620-2kmac7ofanlr7lp6r7a9fs3tcm8bs97e.apps.googleusercontent.com"
    
    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState

    // Almacenamos los puntos y transacciones fuera del AuthState para que no se pierdan al cerrar sesión
    private var persistedPoints = 1284
    private var persistedTransactions = getDummyTransactions()

    init {
        val currentUser = auth.currentUser
        Log.d("AuthViewModel", "Init: Current user is ${currentUser?.uid}")
        if (currentUser != null) {
            _authState.value = AuthState.Success(
                userName = currentUser.displayName ?: currentUser.email,
                userCode = generateUserCode(currentUser.uid),
                userId = currentUser.uid,
                points = persistedPoints,
                transactions = persistedTransactions
            )
        }
    }

    private fun getDummyTransactions(): List<Transaction> {
        val sdf = SimpleDateFormat("dd MMM, yyyy - HH:mm", Locale("es", "ES"))
        return listOf(
            Transaction("1", "Reciclaje de Botellas PET", 150, sdf.format(Date()), true),
            Transaction("2", "Canje: Carga SUBE", -100, "11 Jun, 2026 - 10:30", false),
            Transaction("3", "Reciclaje de Cartón", 85, "10 Jun, 2026 - 15:15", true),
            Transaction("4", "Canje: Saldo SEM", -150, "09 Jun, 2026 - 18:45", false)
        )
    }

    private fun generateUserCode(uid: String): String {
        // Genera un código corto basado en los últimos 5 caracteres del UID
        val suffix = uid.takeLast(5).uppercase()
        return "RE-$suffix"
    }

    fun register(name: String, email: String, pass: String) {
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            _authState.value = AuthState.Error("Por favor ingresa un correo válido")
            return
        }
        
        Log.d("AuthViewModel", "Starting registration for email: $email, name: $name")
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            try {
                val result = auth.createUserWithEmailAndPassword(email, pass).await()
                val user = result.user
                
                // Enviar correo de verificación
                user?.sendEmailVerification()?.await()
                
                val profileUpdates = UserProfileChangeRequest.Builder()
                    .setDisplayName(name)
                    .build()
                user?.updateProfile(profileUpdates)?.await()
                
                _authState.value = AuthState.Success(
                    userName = name, 
                    userCode = generateUserCode(user?.uid ?: ""),
                    userId = user?.uid ?: "",
                    points = persistedPoints,
                    transactions = persistedTransactions
                )
            } catch (e: Exception) {
                Log.e("AuthViewModel", "Registration failed", e)
                _authState.value = AuthState.Error(e.message ?: "Registration failed")
            }
        }
    }

    fun login(email: String, pass: String) {
        Log.d("AuthViewModel", "Starting login for email: $email")
        viewModelScope.launch {
            _authState.value = AuthState.Loading
            try {
                val result = auth.signInWithEmailAndPassword(email, pass).await()
                val user = result.user
                
                _authState.value = AuthState.Success(
                    userName = user?.displayName ?: user?.email,
                    userCode = generateUserCode(user?.uid ?: ""),
                    userId = user?.uid ?: "",
                    points = persistedPoints,
                    transactions = persistedTransactions
                )
            } catch (e: Exception) {
                Log.e("AuthViewModel", "Login failed", e)
                _authState.value = AuthState.Error("Credenciales incorrectas o error de red")
            }
        }
    }

    fun signInWithGoogle(context: Context, launcher: androidx.activity.result.ActivityResultLauncher<Intent>) {
        Log.d("AuthViewModel", "Starting Google Sign-In (Legacy Flow)")
        _authState.value = AuthState.Loading
        
        val gso = GoogleSignInOptions.Builder(GoogleSignInOptions.DEFAULT_SIGN_IN)
            .requestIdToken(webClientId)
            .requestEmail()
            .build()

        val googleSignInClient = GoogleSignIn.getClient(context, gso)
        val intent = googleSignInClient.signInIntent
        launcher.launch(intent)
    }

    fun handleGoogleSignInResult(account: GoogleSignInAccount?) {
        if (account == null) {
            Log.e("AuthViewModel", "Google account is null")
            _authState.value = AuthState.Error("No se pudo obtener la cuenta de Google")
            return
        }

        viewModelScope.launch {
            try {
                val credential = GoogleAuthProvider.getCredential(account.idToken, null)
                val result = auth.signInWithCredential(credential).await()
                val user = result.user
                Log.d("AuthViewModel", "Firebase login success: ${user?.uid}")
                _authState.value = AuthState.Success(
                    userName = user?.displayName,
                    userCode = generateUserCode(user?.uid ?: ""),
                    userId = user?.uid ?: "",
                    points = persistedPoints,
                    transactions = persistedTransactions
                )
            } catch (e: Exception) {
                Log.e("AuthViewModel", "Firebase auth failed", e)
                _authState.value = AuthState.Error("Error en Firebase: ${e.message}")
            }
        }
    }

    fun onGoogleSignInError(apiException: ApiException) {
        Log.e("AuthViewModel", "Google Sign-In failed: code ${apiException.statusCode}")
        val message = when (apiException.statusCode) {
            7 -> "Error de red. Verifica tu conexión."
            10 -> "Error de configuración (Developer Error). Revisa el SHA-1 en Firebase."
            12500 -> "Error de actualización de Google Play Services."
            12501 -> "Inicio de sesión cancelado por el usuario."
            else -> "Error de Google (${apiException.statusCode}): ${apiException.message}"
        }
        _authState.value = AuthState.Error(message)
    }

    fun signOut(context: Context) {
        Log.d("AuthViewModel", "Signing out...")
        // 1. Limpiar el estado INMEDIATAMENTE para que la UI reaccione
        _authState.value = AuthState.Idle
        
        // 2. Cerrar sesión en Firebase
        auth.signOut()
        
        // 3. Limpiar Credential Manager en segundo plano
        viewModelScope.launch {
            try {
                val credentialManager = CredentialManager.create(context)
                credentialManager.clearCredentialState(ClearCredentialStateRequest())
                Log.d("AuthViewModel", "Credential state cleared")
            } catch (e: Exception) {
                Log.e("AuthViewModel", "Error clearing credential state", e)
            }
        }
    }

    fun isUserLoggedIn(): Boolean {
        return auth.currentUser != null
    }

    fun addPointsFromScanner(material: String, pointsToAdd: Int) {
        val currentState = _authState.value
        if (currentState is AuthState.Success) {
            viewModelScope.launch {
                try {
                    persistedPoints += pointsToAdd
                    val sdf = SimpleDateFormat("dd MMM, yyyy - HH:mm", Locale("es", "ES"))
                    val newTransaction = Transaction(
                        id = System.currentTimeMillis().toString(),
                        title = "Reciclaje: $material",
                        amount = pointsToAdd,
                        date = sdf.format(Date()),
                        isGain = true
                    )
                    
                    persistedTransactions = listOf(newTransaction) + persistedTransactions
                    
                    _authState.value = currentState.copy(
                        points = persistedPoints,
                        transactions = persistedTransactions
                    )
                    Log.d("AuthViewModel", "Points added. New balance: $persistedPoints")
                } catch (e: Exception) {
                    Log.e("AuthViewModel", "Failed to add points", e)
                }
            }
        }
    }

    fun redeemPoints(rewardTitle: String, cost: Int) {
        val currentState = _authState.value
        if (currentState is AuthState.Success) {
            if (currentState.points >= cost) {
                viewModelScope.launch {
                    try {
                        persistedPoints -= cost
                        val sdf = SimpleDateFormat("dd MMM, yyyy - HH:mm", Locale("es", "ES"))
                        val newTransaction = Transaction(
                            id = System.currentTimeMillis().toString(),
                            title = "Canje: $rewardTitle",
                            amount = -cost,
                            date = sdf.format(Date()),
                            isGain = false
                        )
                        
                        persistedTransactions = listOf(newTransaction) + persistedTransactions
                        
                        _authState.value = currentState.copy(
                            points = persistedPoints,
                            transactions = persistedTransactions
                        )
                        Log.d("AuthViewModel", "Redeem success: $rewardTitle. New balance: $persistedPoints")
                    } catch (e: Exception) {
                        Log.e("AuthViewModel", "Redeem failed", e)
                    }
                }
            }
        }
    }
}
