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
import com.google.firebase.firestore.ListenerRegistration
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

data class Transaction(
    val id: String,
    val title: String,
    val amount: Int,
    val date: String,
    val isGain: Boolean
)

sealed class AuthState {
    object Idle : AuthState()
    object Loading : AuthState()
    data class Success(
        val userName: String?,
        val email: String?,
        val userId: String = "",
        val codigo: String = "",
        val saldo: Int = 0,
        val transactions: List<Transaction> = emptyList()
    ) : AuthState()
    data class Error(val message: String) : AuthState()
}

class AuthViewModel : ViewModel() {
    private val auth: FirebaseAuth = FirebaseAuth.getInstance()
    private val firestoreRepo = FirestoreRepository()

    private val webClientId = "593104803620-2kmac7ofanlr7lp6r7a9fs3tcm8bs97e.apps.googleusercontent.com"

    private val _authState = MutableStateFlow<AuthState>(AuthState.Idle)
    val authState: StateFlow<AuthState> = _authState

    private var userListener: ListenerRegistration? = null
    private var txListener: ListenerRegistration? = null

    init {
        val currentUser = auth.currentUser
        Log.d("AuthViewModel", "Init: Current user is ${currentUser?.uid}")
        if (currentUser != null) {
            _authState.value = AuthState.Loading
            viewModelScope.launch {
                firestoreRepo.createUserDocument(
                    currentUser.uid,
                    currentUser.email ?: "",
                    currentUser.displayName ?: currentUser.email ?: ""
                )
                startFirestoreListeners(currentUser.uid, currentUser.displayName ?: currentUser.email)
            }
        }
    }

    private fun startFirestoreListeners(uid: String, displayName: String?) {
        userListener?.remove()
        userListener = firestoreRepo.listenUser(uid) { saldo, nombre, email, codigo ->
            val current = _authState.value
            val name = nombre ?: displayName
            val currentCodigo = codigo ?: (current as? AuthState.Success)?.codigo ?: ""
            val currentTxs = if (current is AuthState.Success) current.transactions else emptyList()
            _authState.value = AuthState.Success(
                userName = name,
                email = email,
                userId = uid,
                codigo = currentCodigo,
                saldo = saldo,
                transactions = currentTxs
            )
        }

        txListener?.remove()
        txListener = firestoreRepo.listenTransactions(uid) { txs ->
            val current = _authState.value
            if (current is AuthState.Success) {
                _authState.value = current.copy(transactions = txs)
            }
        }
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
                user?.sendEmailVerification()?.await()
                val profileUpdates = UserProfileChangeRequest.Builder()
                    .setDisplayName(name)
                    .build()
                user?.updateProfile(profileUpdates)?.await()

                val uid = user?.uid ?: return@launch
                val codigo = firestoreRepo.createUserDocument(uid, email, name).await()
                startFirestoreListeners(uid, name)

                _authState.value = AuthState.Success(
                    userName = name,
                    email = email,
                    userId = uid,
                    codigo = codigo,
                    saldo = 0,
                    transactions = emptyList()
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
                val uid = user?.uid ?: return@launch
                val codigo = firestoreRepo.createUserDocument(uid, user.email ?: "", user.displayName ?: user.email ?: "").await()
                startFirestoreListeners(uid, user.displayName ?: user.email)

                _authState.value = AuthState.Success(
                    userName = user?.displayName ?: user?.email,
                    email = user?.email,
                    userId = uid,
                    codigo = codigo,
                    saldo = 0,
                    transactions = emptyList()
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
                val uid = user?.uid ?: return@launch
                val codigo = firestoreRepo.createUserDocument(uid, account.email ?: "", account.displayName ?: account.email ?: "").await()
                startFirestoreListeners(uid, account.displayName ?: account.email)

                _authState.value = AuthState.Success(
                    userName = user?.displayName,
                    email = user?.email,
                    userId = uid,
                    codigo = codigo,
                    saldo = 0,
                    transactions = emptyList()
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
        userListener?.remove()
        txListener?.remove()
        userListener = null
        txListener = null
        _authState.value = AuthState.Idle
        auth.signOut()
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
            val nombre = currentState.userName ?: ""
            firestoreRepo.addLocalDeposit(currentState.userId, material, pointsToAdd, nombre)
        }
    }

    fun redeemPoints(rewardTitle: String, cost: Int) {
        val currentState = _authState.value
        if (currentState is AuthState.Success) {
            if (currentState.saldo >= cost) {
                val nombre = currentState.userName ?: ""
                val uid = currentState.userId
                val userRef = com.google.firebase.firestore.FirebaseFirestore.getInstance()
                    .collection("users").document(uid)
                val txRef = com.google.firebase.firestore.FirebaseFirestore.getInstance()
                    .collection("transactions").document()

                com.google.firebase.firestore.FirebaseFirestore.getInstance()
                    .runBatch { batch ->
                        batch.update(userRef, "saldo", com.google.firebase.firestore.FieldValue.increment(-cost.toLong()))
                        batch.set(txRef, hashMapOf(
                            "userId" to uid,
                            "nombre" to nombre,
                            "material" to "canje:$rewardTitle",
                            "puntos" to -cost,
                            "confidence" to 1.0,
                            "timestamp" to com.google.firebase.firestore.FieldValue.serverTimestamp(),
                            "tipo" to "canje"
                        ))
                    }
                    .addOnFailureListener { e ->
                        Log.e("AuthViewModel", "Redeem failed", e)
                    }
            }
        }
    }
}
