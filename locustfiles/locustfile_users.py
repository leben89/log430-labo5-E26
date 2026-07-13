"""
Locustfile pour le test de charge du labo 7.
Scénario testé : création d'un utilisateur Store Manager, puis suppression du même utilisateur.
À lancer via le service Locust du docker-compose du labo 5.
"""
import random
import time
import uuid
from locust import HttpUser, task, between

USER_TYPES = [
    (1, "client"),
    (2, "employee"),
    (3, "manager"),
]


class StoreManagerUserLifecycle(HttpUser):
    """Utilisateur virtuel Locust qui teste POST /users puis DELETE /users/{id}."""

    # Petite pause pour simuler un trafic plus réaliste et éviter un bombardement instantané.
    wait_time = between(0.2, 1.0)

    @task
    def create_then_delete_user(self):
        user_type_id, user_type_label = random.choice(USER_TYPES)
        unique_id = uuid.uuid4().hex[:12]
        payload = {
            "name": f"Locust {user_type_label} {unique_id}",
            "email": f"locust-{user_type_label}-{unique_id}@example.com",
            "user_type_id": user_type_id,
        }

        # Le docker-compose du labo 5 lance Locust avec --host=http://api-gateway:8080.
        with self.client.post(
            "/store-manager-api/users",
            json=payload,
            headers={"Content-Type": "application/json"},
            name="POST /store-manager-api/users",
            catch_response=True,
        ) as response:
            if response.status_code not in (200, 201):
                response.failure(f"Création échouée: HTTP {response.status_code} - {response.text[:300]}")
                return

            try:
                data = response.json()
            except ValueError:
                response.failure(f"Réponse JSON invalide à la création: {response.text[:300]}")
                return

            user_id = data.get("user_id")
            returned_user_type_id = data.get("user_type_id")

            if not user_id:
                response.failure(f"Aucun user_id retourné: {data}")
                return
            if int(returned_user_type_id) != user_type_id:
                response.failure(f"Type utilisateur inattendu: attendu={user_type_id}, reçu={returned_user_type_id}")
                return

            response.success()

        # Légère pause pour éviter que toutes les suppressions arrivent exactement au même instant.
        time.sleep(random.uniform(0.05, 0.2))

        with self.client.delete(
            f"/store-manager-api/users/{user_id}",
            name="DELETE /store-manager-api/users/[id]",
            catch_response=True,
        ) as delete_response:
            if delete_response.status_code != 200:
                delete_response.failure(
                    f"Suppression échouée pour user_id={user_id}: "
                    f"HTTP {delete_response.status_code} - {delete_response.text[:300]}"
                )
                return

            try:
                delete_data = delete_response.json()
            except ValueError:
                delete_response.failure(f"Réponse JSON invalide à la suppression: {delete_response.text[:300]}")
                return

            if delete_data.get("deleted") is True:
                delete_response.success()
            else:
                delete_response.failure(f"Suppression non confirmée pour user_id={user_id}: {delete_data}")
