#!/usr/bin/env python3
"""
run-tests.py — Exercice 2 (OpenClassrooms)

Je fais ce script pour :
- détecter automatiquement si le projet est Angular/Node ou Java/Gradle
- exécuter les tests unitaires
- récupérer les rapports JUnit XML et les mettre dans ./test-results/
- nettoyer les anciens résultats
- renvoyer un code de sortie :
    0 = tests OK
    1 = tests KO
    2 = prérequis manquants / projet non détecté
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Tuple


# Je considère la racine du projet comme le dossier où se trouve ce fichier.
ROOT = Path(__file__).resolve().parent

# Je standardise l'emplacement des résultats comme demandé : ./test-results/
TEST_RESULTS = ROOT / "test-results"


def which(cmd: str) -> Optional[str]:
    """Je vérifie si une commande (npm / gradle) existe dans le PATH."""
    return shutil.which(cmd)


def die(msg: str, code: int = 2) -> int:
    """J'affiche une erreur et je renvoie un code 2 (problème de prérequis)."""
    print(f"ERROR: {msg}")
    return code


def run(cmd: List[str], cwd: Path = ROOT, extra_env: Optional[dict] = None) -> int:
    """
    J'exécute une commande (npm/gradle) et je renvoie son code de sortie.

    Note Windows :
    - npm est souvent un fichier .cmd ; pour l'exécuter proprement, je passe par "cmd /c".
    """
    env = os.environ.copy()
    env.setdefault("CI", "true")
    if extra_env:
        env.update(extra_env)

    real_cmd = cmd
    if os.name == "nt":
        real_cmd = ["cmd", "/c", *cmd]

    print(f"\n$ ({cwd}) {' '.join(real_cmd)}")
    try:
        proc = subprocess.run(real_cmd, cwd=str(cwd), env=env, text=True)
        return proc.returncode
    except FileNotFoundError:
        return die(f"Commande introuvable: {cmd[0]}")
    except Exception as e:
        return die(f"Erreur lors de l'exécution de {' '.join(cmd)}: {e}")


def clean_test_results() -> None:
    """Je supprime ./test-results/ pour repartir propre (artefacts précédents)."""
    if TEST_RESULTS.exists():
        shutil.rmtree(TEST_RESULTS)
    TEST_RESULTS.mkdir(parents=True, exist_ok=True)


def iter_xml_matches(globs: Iterable[str]) -> List[Path]:
    """Je cherche les fichiers .xml (JUnit) correspondant à des patterns glob."""
    matches: List[Path] = []
    for g in globs:
        matches.extend([p for p in ROOT.glob(g) if p.is_file() and p.suffix.lower() == ".xml"])

    # Je dédoublonne pour éviter de copier deux fois le même fichier.
    uniq: List[Path] = []
    seen = set()
    for p in matches:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def copy_xml_preserve_relative(xml_files: List[Path], dest_root: Path) -> int:
    """
    Je copie les XML dans test-results en gardant leur chemin relatif.
    Ça évite les collisions si plusieurs fichiers ont le même nom.
    """
    copied = 0
    for src in xml_files:
        rel = src.relative_to(ROOT)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        copied += 1
    return copied


def has_any(*names: str) -> bool:
    """Je vérifie si au moins un fichier attendu existe (pour détecter le projet)."""
    return any((ROOT / n).exists() for n in names)


def detect_project() -> Tuple[bool, bool]:
    """
    Je détecte le type de projet.
    - Angular/Node : package.json
    - Java/Gradle : build.gradle/settings.gradle/gradlew
    """
    is_node = (ROOT / "package.json").exists()
    is_gradle = (
        has_any("build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts")
        or (ROOT / "gradlew").exists()
        or (ROOT / "gradlew.bat").exists()
    )
    return is_node, is_gradle


def run_node_tests() -> int:
    """
    Projet Angular/Node :
    - j'installe les dépendances
    - je lance les tests
    - je copie les XML JUnit (reports/**/*.xml) vers ./test-results/
    """
    print("\n== Projet détecté : Angular/Node ==")

    if which("npm") is None:
        return die("npm n'est pas disponible dans le PATH (installe Node.js).")

    install_cmd = ["npm", "ci"] if (ROOT / "package-lock.json").exists() else ["npm", "install"]
    rc_install = run(install_cmd)

    try:
        if rc_install != 0:
            return rc_install
        return run(["npm", "test"])
    finally:
        xmls = iter_xml_matches(["reports/**/*.xml"])
        xmls = [p for p in xmls if not str(p).startswith(str(TEST_RESULTS))]  # j'évite la boucle
        copied = copy_xml_preserve_relative(xmls, TEST_RESULTS)
        print(f"JUnit Angular copiés: {copied} fichier(s) -> {TEST_RESULTS}")


def gradle_wrapper_path() -> Optional[Path]:
    """Je choisis le wrapper Gradle selon l'OS (gradlew ou gradlew.bat)."""
    if os.name == "nt":
        p = ROOT / "gradlew.bat"
        return p if p.exists() else None
    p = ROOT / "gradlew"
    return p if p.exists() else None


def run_gradle_tests() -> int:
    """
    Projet Java/Gradle :
    - je lance les tests avec le wrapper Gradle
    - je copie les XML JUnit (build/test-results/test/**/*.xml) vers ./test-results/
    """
    print("\n== Projet détecté : Java/Gradle ==")

    wrapper = gradle_wrapper_path()
    if wrapper is None:
        if which("gradle") is None:
            return die("gradlew introuvable et gradle n'est pas disponible.")
        cmd = ["gradle", "test"]
    else:
        if os.name != "nt":
            try:
                wrapper.chmod(wrapper.stat().st_mode | 0o111)
            except Exception:
                pass
        cmd = [str(wrapper), "test"]

    try:
        return run(cmd)
    finally:
        xmls = iter_xml_matches(["build/test-results/test/**/*.xml"])
        copied = copy_xml_preserve_relative(xmls, TEST_RESULTS)
        print(f"JUnit Gradle copiés: {copied} fichier(s) -> {TEST_RESULTS}")


def main() -> int:
    """Je pilote l'exécution : nettoyage -> détection -> tests -> code de sortie."""
    clean_test_results()

    is_node, is_gradle = detect_project()
    if not is_node and not is_gradle:
        return die("Projet non détecté (ni package.json, ni fichiers Gradle).")

    exit_codes: List[int] = []
    if is_node:
        exit_codes.append(run_node_tests())
    if is_gradle:
        exit_codes.append(run_gradle_tests())

    # Je respecte le contrat 0/1/2 :
    # - si j'ai un 2 : prérequis
    # - sinon si j'ai un non-zéro : tests KO
    # - sinon : OK
    if any(code == 2 for code in exit_codes):
        final_code = 2
    elif any(code != 0 for code in exit_codes):
        final_code = 1
    else:
        final_code = 0

    print(f"\n== Résultat final: {'SUCCESS' if final_code == 0 else 'FAILURE'} ==")
    print(f"Résultats JUnit: {TEST_RESULTS.resolve()}")
    return final_code

if __name__ == "__main__":
    sys.exit(main())
