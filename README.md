# Workshop Organizer Web API

Bienvenue sur Workshop Organizer Web API. Cette API facilite l’organisation d’ateliers ouverts au public (inscriptions, sessions, ressources).

## Sommaire

1. Contexte
2. Vue technique
3. Exécution en local (sans Docker)
4. Exécution avec Docker (compose)
5. Configuration
6. Tests
7. CI/CD (GitHub Actions)
8. Images Docker & publication sur GHCR

1) Contexte

Les workshops sont un excellent moyen de favoriser l’apprentissage et la collaboration. Cette API vise à simplifier la gestion des participants, des sessions et des ressources.

2) Vue technique

- JDK / Runtime : l’image d’exécution Docker utilise Eclipse Temurin JRE 21.
- Build : multi-stage Docker avec Gradle 8.7 + JDK 21 , et le projet utilise Gradle.
- Spring Boot : Spring Boot 3.2.4.
- Base de données : PostgreSQL 16 Alpine.
- Port API : exposé 8080.

3) Exécution en local (sans Docker)

* Prérequis :

- JDK 21
- Gradle via wrapper (./gradlew)
- Compiler : 
```bash
./gradlew clean compileJava
```

- Lancer : 
```bash
./gradlew bootRun
```

4) Exécution avec Docker (docker compose)

- Démarrer l’API + PostgreSQL
```bash
docker compose up -d
```

API : http://localhost:8080

PostgreSQL : conteneur workshop-db (données persistées via volume pgdata)

- Arrêter
```bash
docker compose down
```

- Supprimer aussi les données (volume)
```bash
docker compose down -v
```

5) Configuration

* Variables principales (Spring) :

- SPRING_DATASOURCE_URL (ex : jdbc:postgresql://db:5432/workshopsdb)
- SPRING_DATASOURCE_USERNAME
- SPRING_DATASOURCE_PASSWORD

* En exécution Docker Compose, les valeurs par défaut sont déjà définies dans docker-compose.yml :

- DB : workshopsdb
- user : workshops_user
- password : oc2024

6) Tests
* Tests Gradle (local)
```bash
./gradlew clean test
```

* Rapports JUnit générés par Gradle :

- build/test-results/test/*.xml (structure standard Gradle)

* Script unifié de tests

- Le dépôt inclut un script run-tests.py qui :
  - détecte le type de projet
  - exécute les tests
  - copie les rapports JUnit XML dans ./test-results/

- Exécution :
```bash
python run-tests.py
```

Exemple de résultats copiés (côté Gradle) :
- test-results/build/test-results/test/*.xml

7) CI/CD (GitHub Actions)

Le workflow CI est générique : il fonctionne pour ce repo Java/Gradle (et peut être identique côté Angular avec le même principe).

* Job test
- installe ce qu’il faut (Java/Gradle ou Node selon le repo)
- lance python run-tests.py
- publie les rapports JUnit (fichiers XML sous test-results/**/*.xml)

* Job build
- build l’image Docker à partir du Dockerfile
- push sur GitHub Container Registry (GHCR) avec un tag lisible :
- branche-SHA (ex : main-<sha>)

* Job release
- s’exécute sur main
- lance semantic-release
- crée une GitHub Release (tag vX.Y.Z)
- push aussi une image Docker taggée avec la version sémantique : X.Y.Z

8) Images Docker & publication sur GHCR

* Nom de l’image

- Le workflow pousse l’image sous :

  - ghcr.io/<owner>/<repo> (calculé automatiquement dans le workflow)
  - Tags publiés
  - branche-SHA (ex : ci-test-<sha>, main-<sha>)
  - X.Y.Z (après release)

* Pré-requis côté GitHub (important)

Pour que le push GHCR + la release fonctionnent, le repo doit autoriser le token GitHub Actions :
- Settings → Actions → General → Workflow permissions → Read and write permissions
- Notes “qualité”
- docker-compose.yml utilise un healthcheck PostgreSQL (pg_isready) et depends_on: condition: service_healthy pour éviter que l’app démarre avant la DB.
- Le Dockerfile backend est multi-stage (build puis runtime), ce qui évite d’embarquer Gradle dans l’image finale.