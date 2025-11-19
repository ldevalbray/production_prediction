"""
Module pour gérer l'icône système (tray icon) de l'application.
Permet de garder l'application accessible même si le navigateur se ferme.
"""
import threading
import webbrowser
import sys
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Essayer d'importer pystray
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    logger.warning("pystray non disponible. L'icône système ne sera pas disponible.")


class SystemTrayManager:
    """Gère l'icône système de l'application."""
    
    def __init__(self, server_url="http://127.0.0.1:5000", on_quit=None):
        """
        Initialise le gestionnaire d'icône système.
        
        Args:
            server_url: URL du serveur Flask
            on_quit: Fonction à appeler lors de la fermeture
        """
        self.server_url = server_url
        self.on_quit = on_quit
        self.icon = None
        self._thread = None
        
    def _create_icon_image(self):
        """Crée une image simple pour l'icône système."""
        # Créer une image 64x64 avec un fond vert (couleur de la pépinière)
        image = Image.new('RGB', (64, 64), color=(34, 197, 94))  # Vert
        draw = ImageDraw.Draw(image)
        
        # Dessiner un simple symbole (feuille/plante)
        # Cercle pour la feuille
        draw.ellipse([20, 15, 44, 35], fill=(255, 255, 255), outline=(255, 255, 255))
        # Tige
        draw.rectangle([30, 35, 34, 50], fill=(255, 255, 255))
        
        return image
    
    def _create_menu(self):
        """Crée le menu contextuel de l'icône."""
        menu_items = [
            pystray.MenuItem(
                "Ouvrir l'application",
                self._open_browser,
                default=True
            ),
            pystray.MenuItem(
                "Quitter",
                self._quit
            )
        ]
        return pystray.Menu(*menu_items)
    
    def _open_browser(self, icon=None, item=None):
        """Ouvre le navigateur vers l'application."""
        try:
            webbrowser.open(self.server_url)
            logger.info(f"Ouverture du navigateur vers {self.server_url}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du navigateur : {e}")
    
    def _quit(self, icon=None, item=None):
        """Ferme l'application proprement."""
        logger.info("Fermeture de l'application depuis l'icône système")
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()
        # Forcer la sortie après un court délai
        threading.Timer(0.5, lambda: os._exit(0)).start()
    
    def start(self):
        """Démarre l'icône système dans un thread séparé."""
        if not PYSTRAY_AVAILABLE:
            logger.warning("pystray non disponible, l'icône système ne sera pas créée")
            return
        
        def run_icon():
            try:
                image = self._create_icon_image()
                menu = self._create_menu()
                self.icon = pystray.Icon(
                    "Pépinière Valbray",
                    image,
                    "Pépinière Valbray - Automatisations récolte",
                    menu
                )
                self.icon.run()
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'icône système : {e}")
        
        self._thread = threading.Thread(target=run_icon, daemon=True)
        self._thread.start()
        logger.info("Icône système démarrée")
    
    def stop(self):
        """Arrête l'icône système."""
        if self.icon:
            self.icon.stop()
            logger.info("Icône système arrêtée")

