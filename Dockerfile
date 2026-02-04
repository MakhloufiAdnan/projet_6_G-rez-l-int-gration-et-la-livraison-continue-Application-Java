# ===== ÉTAPE 1 — BUILD DE L’APPLICATION =====

# Image officielle Gradle avec JDK 21, utilisation de la version 9.3 impossible pour éviter les incompatibilités liées aux changements majeurs de Gradle 9
FROM gradle:8.7-jdk21-alpine AS build

# Répertoire de travail dans le conteneur
WORKDIR /app

# Copie des fichiers Gradle nécessaires au build
COPY gradlew gradlew
COPY gradle gradle
COPY build.gradle settings.gradle ./

# Téléchargement des dépendances sans lancer l’application
RUN gradle dependencies --no-daemon

# Copie du code source Java
COPY src src

# Compilation de l’application Spring Boot
RUN gradle bootJar --no-daemon

# ===== ÉTAPE 2 — IMAGE D’EXÉCUTION =====

# Image runtime légère avec JRE 21 (sans outils de build)
FROM eclipse-temurin:21-jre-alpine-3.21

# Répertoire de travail pour l’exécution
WORKDIR /app

# Copie uniquement du JAR compilé depuis l’étape de build
COPY --from=build /app/build/libs/*.jar app.jar

# Port utilisé par l’application Spring Boot
EXPOSE 8080

# Commande de démarrage du conteneur
ENTRYPOINT ["java", "-jar", "app.jar"]
