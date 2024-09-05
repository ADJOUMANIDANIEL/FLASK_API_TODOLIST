from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Namespace, Resource, fields
from flask_marshmallow import Marshmallow
import pymysql
from datetime import datetime
# from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash
# from app import db, api, ns_taches  
# from app.models import Tache, Utilisateur  

# Instanciation de l'application Flask
app = Flask(__name__)
# Instanciation de la base de données et du modèle d'affichage des données
db = SQLAlchemy()
ma = Marshmallow()
# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/todo'
db.init_app(app)
# Création des tables dans la base de données
with app.app_context():
    db.create_all()

##### Creation des modèles des differentes tables ------------------------------------------------------------------------
# 1- Création du modèle de la table utilisateurs
class Utilisateurs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50),unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    def __init__(self, nom, email, mot_de_passe):
        self.nom = nom
        self.email = email
        self.mot_de_passe = mot_de_passe
# Création du modèle d'affichage des données avce la biblotheque marshmallow
class UtilisateurSchema(ma.Schema):
    class Meta:
        fields = ("id", "nom", "email", "mot_de_passe")
# Instanciation du modèle d'affichage
utilisateur_schema = UtilisateurSchema(many=False)  # Quand on veut afficher un seul utilisateur
utilisateurs_schema = UtilisateurSchema(many=True)  # Quand on veut afficher plusieurs utilisateurs

# 2- Création du modèle de la table taches
class Taches(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.Boolean,default=False,nullable=False)
    date_creation=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    date_mise_a_jour=db.Column(db.DateTime,default=datetime.utcnow,nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    def __init__(self, titre, description, statut,date_creation,date_mise_a_jour,utilisateur_id):
        self.titre = titre
        self.description = description
        self.statut = statut
        self.date_creation = date_creation
        self.date_mise_a_jour = date_mise_a_jour 
        self.utilisateur_id = utilisateur_id 
# Création du modèle d'affichage des données
class TacheSchema(ma.Schema):
    class Meta:
        fields = ("id", "titre", "description", "statut", "date_creation","date_mise_a_jour","utilisateur_id")
# Instanciation du modèle d'affichage
tache_schema = TacheSchema(many=False)  # Quand on veut afficher une seule tache
taches_schema = TacheSchema(many=True)  # Quand on veut afficher plusieures taches

# 3- Création du modèle de la table historiques
class Historiques(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(20), nullable=False)
    date_action = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    tache_id = db.Column(db.Integer, db.ForeignKey('taches.id'), nullable=False)
    def __init__(self, action,  date_action,utilisateur_id, tache_id):
        self.action = action
        self.date_action = date_action
        self.utilisateur_id = utilisateur_id
        self.tache_id = tache_id
# Création du modèle d'affichage des données 
class HistoSchema(ma.Schema):
    class Meta:
        fields = ("id", "action", "date_action", "utilisateur_id","tache_id")
# Instanciation du modèle d'affichage
historique_schema = HistoSchema(many=False)  # Quand on veut afficher un seul historiques
historiques_schema = HistoSchema(many=True)  # Quand on veut afficher plusieurs historiques

# Initialisation de Flask-RESTx
api = Api(app, version='1.0', title='API TodoList', description='API pour gérer les taches')
# Namespace pour les utilisateurs
ns_users = Namespace('UTILISATEURS', description='Opérations sur les utilisateurs') # ajout TITRE et la description du titre
api.add_namespace(ns_users, path='/user') # ajout noms sapce et le chemin reccourci à toutes les routes

# Modèle pour les utilisateurs
user_model = api.model('User', {
    'id': fields.Integer(readOnly=True, description='Identifiant unique de l\'utilisateur'),
    'nom': fields.String(required=True, description='Nom de l\'utilisateur'),
    'email': fields.String(required=True, description='Email de l\'utilisateur'),
    'mot_de_passe': fields.String(required=True, description='Mot de passe de l\'utilisateur')
})

# Route pour ajouter un nouveau user
@ns_users.route('/ajouter')
class AddUser(Resource):
    @ns_users.expect(user_model, validate=True)
    def post(self):
        try:
            __json = request.json
            nom = __json["nom"]
            email = __json["email"]
            mot_de_passe = __json["mot_de_passe"]
            # Vérifier si l'adresse e-mail existe déjà
            existing_user = Utilisateurs.query.filter_by(email=email).first()
            if existing_user:
                return jsonify({"message": "L'adresse e-mail est déjà utilisée"}), 400
            hashed_password = generate_password_hash(mot_de_passe)
            new_utilisateur = Utilisateurs(nom=nom, email=email, mot_de_passe=hashed_password)
            db.session.add(new_utilisateur)
            db.session.commit()
            return jsonify(f"Utilisateur ajouté avec succès")
        except Exception as e:
            return jsonify("Mauvaise requête d'insertion d'utilisateur")

# Route pour afficher tous les users
@ns_users.route('/')
class GetUsers(Resource):
    @ns_users.marshal_list_with(user_model)
    def get(self):
        utilisateurs = Utilisateurs.query.all()
        return utilisateurs_schema.dump(utilisateurs)

# Route pour afficher un seul user
@ns_users.route('/afficher_user_ID/<int:id>')
class GetUserById(Resource):
    @ns_users.marshal_with(user_model)
    def get(self, id):
        utilisateur = Utilisateurs.query.get_or_404(id)
        return utilisateur_schema.dump(utilisateur)

# Route pour supprimer un user
@ns_users.route('/supprimer/<int:id>')
class DeleteUser(Resource):
    def delete(self, id):
        utilisateur = Utilisateurs.query.get_or_404(id)
        db.session.delete(utilisateur)
        db.session.commit()
        return jsonify("Utilisateur supprimé avec succès")

# Route pour modifier un user
@ns_users.route('/modifier/<int:id>')
class UpdateUser(Resource):
    @ns_users.expect(user_model, validate=True)
    @ns_users.marshal_with(user_model)
    def put(self, id):
        utilisateur = Utilisateurs.query.get_or_404(id)
        nom = request.json["nom"]
        email = request.json["email"]
        mot_de_passe = request.json["mot_de_passe"]
        utilisateur.nom = nom
        utilisateur.email = email
        utilisateur.mot_de_passe = mot_de_passe
        db.session.commit()
        return utilisateur_schema.dump(utilisateur)
# Fin Namespace utilisateurs --------------------------------------------------------------------------------------

# Namespace pour les taches
ns_taches = Namespace('TACHES', description='Opérations sur les taches') # ajout TITRE et la description du titre
api.add_namespace(ns_taches, path='/tache')  # ajout nom sapce et le chemin reccourci à toutes les routes
# Modèle pour les produits
tache_model = api.model('Tache', {
    'id': fields.Integer(readOnly=True, description='Identifiant unique tache'),
    'titre': fields.String(required=True, description='Description titre'),
    'description': fields.String(required=True, description='Description tache'),
    'statut': fields.Boolean(required=True, description='Satut tache'),
    'date_creation': fields.DateTime(required=True, description='date création'),
    'date_mise_a_jour': fields.DateTime(required=True, description='date mise à jour'),
    'utilisateur_id': fields.Integer(required=True, description='Identifiant de l\'utilisateur')
})

# Route pour ajouter une nouvelle tache
@ns_taches.route('/ajouter')
class AddTache(Resource):
    @ns_taches.expect(tache_model, validate=True)
    def post(self):
        try:
            __json = request.json
            titre = __json["titre"]
            description = __json["description"]
            statut = __json["statut"]
            date_creation = __json["date_creation"]
            date_mise_a_jour = __json["date_mise_a_jour"]
            utilisateur_id = __json["utilisateur_id"]
            # Vérifiez si l'utilisateur existe
            utilisateur = Utilisateurs.query.get(utilisateur_id)
            if not utilisateur:
                return jsonify({"message": "L'utilisateur n'existe pas"}), 404
            new_tache = Taches(titre=titre, description=description, statut=statut,date_creation=date_creation,
            date_mise_a_jour=date_mise_a_jour,utilisateur_id=utilisateur_id)
            db.session.add(new_tache)
            db.session.commit()
            return jsonify(f"Tache ajouté avec succès")
        except Exception as e:
            return jsonify({"message": "Mauvaise requête d'insertion de tâche", "error": str(e)}), 400
            # return jsonify("Mauvaise requête d'insertion de tache")

# Route pour afficher une seule tache
@ns_taches.route('/afficher_tache_ID/<int:id>')
class GetTacheById(Resource):
    @ns_taches.marshal_with(tache_model)
    def get(self, id):
        tache = Taches.query.get_or_404(id)
        return tache_schema.dump(tache)

# Route pour afficher toutes les taches
@ns_taches.route('/')
class GetUsers(Resource):
    @ns_taches.marshal_list_with(tache_model)
    def get(self):
        taches = Taches.query.all()
        return taches_schema.dump(taches)

# Route pour supprimer une seule tache
@ns_taches.route('/supprimer/<int:id>')
class DeleteTache(Resource):
    def delete(self, id):
        tache = Taches.query.get_or_404(id)
        db.session.delete(tache)
        db.session.commit()
        return jsonify("Tache supprimée avec succès")

# Route pour mettre à jour une tache unique
@ns_taches.route('/modifier/<int:id>')
class UpdateTache(Resource):
    @ns_taches.expect(tache_model, validate=True)
    @ns_taches.marshal_with(tache_model)
    def put(self, id):
        tache = Taches.query.get_or_404(id)
        titre = request.json["titre"]
        description = request.json["description"]
        statut = request.json["statut"]
        # date_creation = request.json["date_creation"]
        date_mise_a_jour = request.json["date_mise_a_jour"]
        tache.titre = titre
        tache.description = description
        tache.statut = statut
        # tache.date_creation = date_creation
        tache.date_mise_a_jour = date_mise_a_jour
        db.session.commit()
        return tache_schema.dump(tache)
# Fin Namespace taches --------------------------------------------------------------------------------------

# Namespace pour les historiques
ns_historiques = Namespace('HISTORIQUES', description='Opérations sur les historiques')
api.add_namespace(ns_historiques, path='/historique')

# Modèle pour les historiques
historique_model = api.model('Historique', {
    'id': fields.Integer(readOnly=True, description='Identifiant unique de historique'),
    'action': fields.String(required=True, description='ACtion faite sur la tache'),
    'date_action': fields.DateTime(required=True, description='Date création historique'),
    'utilisateur_id': fields.Integer(required=True, description='Identifiant de l\'utilisateur'),
    'tache_id': fields.Integer(required=True, description='Identifiant de la tache')
})

# Route pour ahouter une historique
@ns_historiques.route('/ajouter')
class AddHistorique(Resource):
    @ns_historiques.expect(historique_model, validate=True)
    def post(self):
        try:
            __json = request.json
            action = __json["action"]
            date_action = __json["date_action"]
            utilisateur_id=__json["utilisateur_id"]
            # Vérifiez si l'utilisateur existe
            utilisateur = Utilisateurs.query.get(utilisateur_id)
            if not utilisateur:
                return jsonify({"message": "L'utilisateur n'existe pas"}), 404
            tache_id =__json["tache_id"]
            # Vérifiez si la tache existe
            tache = Taches.query.get(tache_id)
            if not tache:
                return jsonify({"message": "La tache n'existe pas"}), 404
            new_histo = Historiques(action=action, date_action=date_action, utilisateur_id=utilisateur_id, tache_id=tache_id)
            db.session.add(new_histo)
            db.session.commit()
            return jsonify(f"Historique ajoutée avec succès")
        except Exception as e:
            # return jsonify("Mauvaise requête d'insertion de historique")
            return jsonify({"message": "Mauvaise requête d'insertion de tâche", "error": str(e)}), 400

# # Route pour ajouter une historique
# @ns_historiques.route('/ajouter')
# class AddHistorique(Resource):
#     @ns_historiques.expect(historique_model, validate=True)
#     def post(self):
#         try:
#             __json = request.json
#             action = __json["action"]
#             date_action = __json["date_action"]
#             utilisateur_id = __json["utilisateur_id"]
#             # Vérifiez si l'utilisateur existe
#             utilisateur = db.session.get(Utilisateurs, utilisateur_id)
#             if not utilisateur:
#                 return jsonify({"message": "L'utilisateur n'existe pas"}), 404
#             tache_id = __json["tache_id"]
#             # Vérifiez si la tache existe
#             tache = db.session.get(Taches, tache_id)
#             if not tache:
#                 return jsonify({"message": "La tache n'existe pas"}), 404
#             new_histo = Historiques(action=action, date_action=date_action, utilisateur_id=utilisateur_id, tache_id=tache_id)
#             db.session.add(new_histo)
#             db.session.commit()
#             return jsonify({"message": "Historique ajoutée avec succès"})
#         except Exception as e:
#             return jsonify({"message": "Mauvaise requête d'insertion de tâche", "error": str(e)}), 400
        
# Route pour afficher toutes les historiques
@ns_historiques.route('/')
class GetHistoriques(Resource):
    @ns_historiques.marshal_list_with(historique_model)
    def get(self):
        historiques = Historiques.query.all()
        return historiques_schema.dump(historiques)

@ns_historiques.route('/afficher_histo_user_ID/<int:utilisateur_id>')
class GetTachesByUserId(Resource):
    @ns_historiques.marshal_with(historique_model)
    def get(self, utilisateur_id):
        historiques_user = Historiques.query.filter_by(utilisateur_id=utilisateur_id).all()
        return historique_schema.dump(historiques_user, many=True)

@ns_historiques.route('/afficher_histo_tache_ID/<int:tache_id>')
class GetTachesByTacheId(Resource):
    @ns_historiques.marshal_with(historique_model)
    def get(self, tache_id):
        historiques_user = Historiques.query.filter_by(tache_id=tache_id).all()
        return historique_schema.dump(historiques_user, many=True)
# Fin Namespace historiques --------------------------------------------------------------------------------------

# Activer le débogage de l'application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
