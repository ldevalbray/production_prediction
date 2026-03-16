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
    
    def __init__(self, server_url="http://127.0.0.1:5001", on_quit=None):
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
        # Créer une image avec support de transparence (RGBA) pour macOS
        # Taille recommandée pour macOS: 22x22 pour la barre de menu
        size = 22
        image = Image.new('RGBA', (size, size), color=(0, 0, 0, 0))  # Transparent
        draw = ImageDraw.Draw(image)
        
        # Dessiner un fond vert arrondi pour la visibilité
        margin = 2
        draw.ellipse([margin, margin, size-margin, size-margin], fill=(34, 197, 94, 255), outline=(255, 255, 255, 255), width=1)
        
        # Dessiner un simple symbole (feuille/plante) en blanc
        # Feuille simplifiée
        leaf_size = 8
        leaf_x = (size - leaf_size) // 2
        leaf_y = (size - leaf_size) // 2 - 2
        draw.ellipse([leaf_x, leaf_y, leaf_x + leaf_size, leaf_y + leaf_size], fill=(255, 255, 255, 255))
        
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
            # Sur macOS, utiliser 'open' pour forcer l'ouverture même si le navigateur est déjà ouvert
            if sys.platform == "darwin":
                import os
                os.system(f'open "{self.server_url}" &')
            else:
                webbrowser.open(self.server_url)
            logger.info(f"Ouverture du navigateur vers {self.server_url}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du navigateur : {e}")
            # Fallback: essayer avec os.system sur macOS
            if sys.platform == "darwin":
                try:
                    import os
                    os.system(f'open "{self.server_url}" &')
                except Exception:
                    pass
    
    def _quit(self, icon=None, item=None):
        """Ferme l'application proprement."""
        logger.info("Fermeture de l'application depuis l'icône système")
        if self.on_quit:
            self.on_quit()
        if self.icon:
            self.icon.stop()
        # Forcer la sortie après un court délai
        threading.Timer(0.5, lambda: os._exit(0)).start()
    
    def _on_clicked(self, icon, item):
        """Gère le clic sur l'icône (ouvre l'application)."""
        self._open_browser()
    
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
                    "Pépinière Valbray - Automatisations récolte\nCliquez pour ouvrir l'application",
                    menu,
                    default_action=self._open_browser  # Action par défaut au clic
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

