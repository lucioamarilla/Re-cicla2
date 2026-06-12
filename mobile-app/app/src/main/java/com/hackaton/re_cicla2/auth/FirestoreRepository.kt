package com.hackaton.re_cicla2.auth

import android.util.Log
import com.google.firebase.firestore.FieldValue
import com.google.firebase.firestore.FirebaseFirestore
import com.google.firebase.firestore.ListenerRegistration
import kotlinx.coroutines.tasks.await
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class FirestoreRepository {
    private val db = FirebaseFirestore.getInstance()

    fun listenUser(uid: String, onUpdate: (saldo: Int, nombre: String?, email: String?, codigo: String?) -> Unit): ListenerRegistration {
        return db.collection("users").document(uid)
            .addSnapshotListener { snapshot, error ->
                if (error != null) {
                    Log.e("FirestoreRepo", "Error listening to user", error)
                    return@addSnapshotListener
                }
                if (snapshot != null && snapshot.exists()) {
                    val saldo = snapshot.getLong("saldo")?.toInt() ?: 0
                    val nombre = snapshot.getString("nombre")
                    val email = snapshot.getString("email")
                    val codigo = snapshot.getString("codigo")
                    onUpdate(saldo, nombre, email, codigo)
                }
            }
    }

    fun listenTransactions(uid: String, onUpdate: (List<Transaction>) -> Unit): ListenerRegistration {
        return db.collection("transactions")
            .whereEqualTo("userId", uid)
            .orderBy("timestamp", com.google.firebase.firestore.Query.Direction.DESCENDING)
            .limit(50)
            .addSnapshotListener { snapshots, error ->
                if (error != null) {
                    Log.e("FirestoreRepo", "Error listening to transactions", error)
                    return@addSnapshotListener
                }
                if (snapshots != null) {
                    val txs = snapshots.documents.mapNotNull { doc ->
                        doc.toObject(FirestoreTransaction::class.java)?.let { data ->
                            val timestamp = data.timestamp?.let { ts ->
                                if (ts is com.google.firebase.Timestamp) {
                                    ts.toDate()
                                } else {
                                    Date()
                                }
                            } ?: Date()
                            val sdf = SimpleDateFormat("dd MMM, yyyy - HH:mm", Locale("es", "ES"))
                            Transaction(
                                id = doc.id,
                                title = if (data.tipo == "canje") "Canje: ${data.material}" else "Reciclaje de ${data.material?.replaceFirstChar { it.uppercase() }}",
                                amount = data.puntos ?: 0,
                                date = sdf.format(timestamp),
                                isGain = data.tipo == "deposito" && (data.puntos ?: 0) > 0
                            )
                        }
                    }
                    onUpdate(txs)
                }
            }
    }

    suspend fun createUserDocument(uid: String, email: String, nombre: String): String {
        val userRef = db.collection("users").document(uid)
        if (!userRef.get().await().exists()) {
            val codigo = generarCodigo()
            userRef.set(
                hashMapOf(
                    "uid" to uid,
                    "codigo" to codigo,
                    "email" to email,
                    "nombre" to nombre,
                    "saldo" to 0,
                    "creado" to FieldValue.serverTimestamp()
                )
            ).await()
            Log.d("FirestoreRepo", "User created: $uid -> $codigo")
            return codigo
        }
        val doc = userRef.get().await()
        return doc.getString("codigo") ?: ""
    }

    private fun generarCodigo(): String {
        val chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        val sufijo = (1..6).map { chars.random() }.joinToString("")
        return "ECO-$sufijo"
    }

    fun addLocalDeposit(uid: String, material: String, pointsToAdd: Int, nombre: String) {
        val userRef = db.collection("users").document(uid)
        val txRef = db.collection("transactions").document()

        db.runBatch { batch ->
            batch.update(userRef, "saldo", FieldValue.increment(pointsToAdd.toLong()))
            batch.set(txRef, hashMapOf(
                "userId" to uid,
                "nombre" to nombre,
                "material" to material.lowercase(),
                "puntos" to pointsToAdd,
                "confidence" to 1.0,
                "timestamp" to FieldValue.serverTimestamp(),
                "tipo" to "deposito"
            ))
        }.addOnSuccessListener {
            Log.d("FirestoreRepo", "Local deposit added: +$pointsToAdd for $material")
        }.addOnFailureListener { e ->
            Log.e("FirestoreRepo", "Error adding local deposit", e)
        }
    }
}

data class FirestoreTransaction(
    val userId: String? = null,
    val nombre: String? = null,
    val material: String? = null,
    val puntos: Int? = null,
    val confidence: Double? = null,
    val timestamp: Any? = null,
    val tipo: String? = null
)
