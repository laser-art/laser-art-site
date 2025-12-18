# Laser Art — site vitrine

Site statique (HTML/CSS/JS) pour l'atelier Laser Art.

## Structure
- `index.html` : accueil
- `realisations.html` : galerie et références
- `services.html` : détail des prestations
- `apropos.html` : présentation de l'équipe et de la démarche
- `contact.html` : coordonnées et formulaire simulé
- `css/style.css` : styles globaux
- `js/script.js` : interactions de base (menu mobile, surlignage de navigation, message de formulaire)
- `assets/` : visuels de remplissage

## Utilisation locale
```bash
# ouvrir le site dans votre navigateur depuis le répertoire racine
python -m http.server 8000
# puis rendez-vous sur http://localhost:8000/
```

## Déploiement sur Cloudflare Pages
1. Créez un projet Pages et connectez ce dépôt.
2. Paramétrez :
   - **Framework preset** : "None"
   - **Build command** : (vide)
   - **Build output directory** : `/` (racine) ou laissez vide pour servir tous les fichiers.
3. Déployez. Les pages HTML statiques seront servies directement.

## SEO et performance
- Pages en français, encodage UTF-8 et balises meta description + canonical sur chaque page.
- Design responsive sans framework pour limiter le poids.
