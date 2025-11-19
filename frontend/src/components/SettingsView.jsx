import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Settings, Sprout, Trash2, Plus, Save, X, Edit2, Calendar, ChevronDown } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.15 }
};

function SettingsView() {
  const [activeTab, setActiveTab] = useState('parcelles');
  const [parametres, setParametres] = useState([]);
  const [plantsParAnnee, setPlantsParAnnee] = useState([]);
  const [recolteQuotidienne, setRecolteQuotidienne] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingParamId, setEditingParamId] = useState(null);
  const [editingPlantsId, setEditingPlantsId] = useState(null);
  const [editingRecolteQuotidienneId, setEditingRecolteQuotidienneId] = useState(null);
  const [varieties, setVarieties] = useState([]);

  // Formulaires
  const [parametreForm, setParametreForm] = useState({
    parcelle: '',
    variety: '',
    nb_rangees: 10,
    saison_debut: '',
    saison_fin: ''
  });

  const [plantsForm, setPlantsForm] = useState({
    variety: '',
    annee: new Date().getFullYear(),
    nb_plants: ''
  });

  const [recolteQuotidienneForm, setRecolteQuotidienneForm] = useState({
    jour_semaine: '',
    jour_semaine_num: '',
    fraction_fraiseraie: '',
    description: ''
  });

  useEffect(() => {
    if (activeTab === 'parcelles') {
      loadParametres();
    } else if (activeTab === 'plants') {
      loadPlants();
      loadVarieties();
    } else if (activeTab === 'recolte-quotidienne') {
      loadRecolteQuotidienne();
    }
  }, [activeTab]);

  const loadVarieties = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parametres`);
      const params = response.data.data || [];
      const uniqueVarieties = [...new Set(params.map(p => p.variety).filter(Boolean))].sort();
      setVarieties(uniqueVarieties);
    } catch (error) {
      console.error('Erreur lors du chargement des variétés:', error);
    }
  };

  const loadParametres = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/parametres`);
      const data = response.data?.data || [];
      setParametres(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Erreur lors du chargement des paramètres:', error);
      alert('Erreur lors du chargement des paramètres: ' + (error.response?.data?.error || error.message));
      setParametres([]);
    } finally {
      setLoading(false);
    }
  };

  const loadPlants = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/plants-par-annee`);
      setPlantsParAnnee(response.data.data || []);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      alert('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const loadRecolteQuotidienne = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/recolte-quotidienne`);
      setRecolteQuotidienne(response.data.data || []);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      alert('Erreur lors du chargement de la récolte quotidienne');
    } finally {
      setLoading(false);
    }
  };

  const handleAddParametre = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/parametres`, {
        ...parametreForm,
        saison_debut: parametreForm.saison_debut ? parseInt(parametreForm.saison_debut) : null,
        saison_fin: parametreForm.saison_fin ? parseInt(parametreForm.saison_fin) : null
      });
      setParametreForm({
        parcelle: '',
        variety: '',
        nb_rangees: 10,
        saison_debut: '',
        saison_fin: ''
      });
      loadParametres();
      alert('Paramètre ajouté avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'ajout du paramètre');
    }
  };

  const handleEditParametre = (param) => {
    setEditingParamId(param.id);
    setParametreForm({
      parcelle: param.parcelle,
      variety: param.variety,
      nb_rangees: param.nb_rangees,
      saison_debut: param.saison_debut || '',
      saison_fin: param.saison_fin || ''
    });
  };

  const handleUpdateParametre = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API_BASE}/parametres/${editingParamId}`, {
        ...parametreForm,
        saison_debut: parametreForm.saison_debut ? parseInt(parametreForm.saison_debut) : null,
        saison_fin: parametreForm.saison_fin ? parseInt(parametreForm.saison_fin) : null
      });
      setParametreForm({
        parcelle: '',
        variety: '',
        nb_rangees: 10,
        saison_debut: '',
        saison_fin: ''
      });
      setEditingParamId(null);
      // Recharger immédiatement les paramètres
      await loadParametres();
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la modification: ' + (error.response?.data?.error || error.message));
    }
  };

  const handleDeleteParametre = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce paramètre ?')) return;
    try {
      await axios.delete(`${API_BASE}/parametres/${id}`);
      loadParametres();
      alert('Paramètre supprimé');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleAddPlants = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/plants-par-annee`, plantsForm);
      setPlantsForm({
        variety: '',
        annee: new Date().getFullYear(),
        nb_plants: ''
      });
      setEditingPlantsId(null);
      loadPlants();
      alert('Plants par année ajoutés avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'ajout des plants');
    }
  };

  const handleEditPlants = (plants) => {
    setEditingPlantsId(plants.id);
    setPlantsForm({
      variety: plants.variety,
      annee: plants.annee,
      nb_plants: plants.nb_plants
    });
  };

  const handleUpdatePlants = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/plants-par-annee`, plantsForm);
      setPlantsForm({
        variety: '',
        annee: new Date().getFullYear(),
        nb_plants: ''
      });
      setEditingPlantsId(null);
      loadPlants();
      alert('Plants par année modifiés avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la modification');
    }
  };

  const handleDeletePlants = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet enregistrement ?')) return;
    try {
      await axios.delete(`${API_BASE}/plants-par-annee/${id}`);
      loadPlants();
      alert('Enregistrement supprimé');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleEditRecolteQuotidienne = (recolte) => {
    // Utiliser un identifiant unique même si l'id est null (jour non configuré)
    setEditingRecolteQuotidienneId(recolte.id || `new-${recolte.jour_semaine_num}`);
    setRecolteQuotidienneForm({
      jour_semaine: recolte.jour_semaine,
      jour_semaine_num: recolte.jour_semaine_num.toString(),
      fraction_fraiseraie: recolte.fraction_fraiseraie || '',
      description: recolte.description || ''
    });
  };

  // Créer une liste complète des 7 jours avec les données existantes
  const getJoursSemaineComplets = () => {
    const jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
    return jours.map((nom, index) => {
      const existant = recolteQuotidienne.find(r => r.jour_semaine_num === index);
      return existant || {
        id: null,
        jour_semaine: nom,
        jour_semaine_num: index,
        fraction_fraiseraie: 0,
        description: ''
      };
    });
  };

  const handleUpdateRecolteQuotidienne = async (e) => {
    e.preventDefault();
    try {
      // Utiliser POST pour créer ou mettre à jour (l'API gère les deux cas)
      await axios.post(`${API_BASE}/recolte-quotidienne`, {
        ...recolteQuotidienneForm,
        jour_semaine_num: parseInt(recolteQuotidienneForm.jour_semaine_num),
        fraction_fraiseraie: parseFloat(recolteQuotidienneForm.fraction_fraiseraie)
      });
      setRecolteQuotidienneForm({
        jour_semaine: '',
        jour_semaine_num: '',
        fraction_fraiseraie: '',
        description: ''
      });
      setEditingRecolteQuotidienneId(null);
      loadRecolteQuotidienne();
      alert('Configuration enregistrée avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'enregistrement');
    }
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <motion.div {...fadeIn} className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Paramètres</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Gérez les paramètres de l'application
          </p>
        </div>
      </motion.div>

      {/* Contenu principal */}
      <motion.div {...fadeIn} transition={{ delay: 0.05 }}>
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="parcelles">
                  <Settings className="mr-2 h-4 w-4" />
                  Parcelles
                </TabsTrigger>
                <TabsTrigger value="plants">
                  <Sprout className="mr-2 h-4 w-4" />
                  Plants par année
                </TabsTrigger>
                <TabsTrigger value="recolte-quotidienne">
                  <Calendar className="mr-2 h-4 w-4" />
                  Récolte quotidienne
                </TabsTrigger>
              </TabsList>

              {/* Parcelles */}
              <TabsContent value="parcelles" className="mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="border-border/50">
                    <CardHeader>
                      <CardTitle>
                        {editingParamId ? 'Modifier le paramètre' : 'Ajouter un paramètre'}
                      </CardTitle>
                      <CardDescription>
                        {editingParamId ? 'Modifiez les informations' : 'Configurez une parcelle/variété'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={editingParamId ? handleUpdateParametre : handleAddParametre} className="space-y-4">
                        <div>
                          <Label htmlFor="parcelle">Parcelle</Label>
                          <input
                            id="parcelle"
                            type="text"
                            value={parametreForm.parcelle}
                            onChange={(e) => setParametreForm({ ...parametreForm, parcelle: e.target.value })}
                            className="w-full mt-1 px-3 py-2 border rounded-md"
                            placeholder="ex: Parcelle_1"
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="variety_param">Variété</Label>
                          <input
                            id="variety_param"
                            type="text"
                            value={parametreForm.variety}
                            onChange={(e) => setParametreForm({ ...parametreForm, variety: e.target.value })}
                            className="w-full mt-1 px-3 py-2 border rounded-md"
                            placeholder="ex: clery"
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="nb_rangees">Nombre de rangées</Label>
                          <input
                            id="nb_rangees"
                            type="number"
                            value={parametreForm.nb_rangees}
                            onChange={(e) => setParametreForm({ ...parametreForm, nb_rangees: parseInt(e.target.value) })}
                            className="w-full mt-1 px-3 py-2 border rounded-md"
                            min="1"
                            required
                          />
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <Label htmlFor="saison_debut">Début de saison (mois)</Label>
                            <input
                              id="saison_debut"
                              type="number"
                              value={parametreForm.saison_debut}
                              onChange={(e) => setParametreForm({ ...parametreForm, saison_debut: e.target.value })}
                              className="w-full mt-1 px-3 py-2 border rounded-md"
                              min="1"
                              max="12"
                              placeholder="ex: 3 (mars)"
                            />
                            <p className="text-xs text-muted-foreground mt-1">Mois de début (1-12)</p>
                          </div>
                          <div>
                            <Label htmlFor="saison_fin">Fin de saison (mois)</Label>
                            <input
                              id="saison_fin"
                              type="number"
                              value={parametreForm.saison_fin}
                              onChange={(e) => setParametreForm({ ...parametreForm, saison_fin: e.target.value })}
                              className="w-full mt-1 px-3 py-2 border rounded-md"
                              min="1"
                              max="12"
                              placeholder="ex: 10 (octobre)"
                            />
                            <p className="text-xs text-muted-foreground mt-1">Mois de fin (1-12)</p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <Button type="submit" className="flex-1">
                            {editingParamId ? (
                              <>
                                <Save className="mr-2 h-4 w-4" />
                                Enregistrer
                              </>
                            ) : (
                              <>
                                <Plus className="mr-2 h-4 w-4" />
                                Ajouter
                              </>
                            )}
                          </Button>
                          {editingParamId && (
                              <Button
                                type="button"
                                variant="outline"
                                onClick={() => {
                                  setEditingParamId(null);
                                  setParametreForm({
                                    parcelle: '',
                                    variety: '',
                                    nb_rangees: 10,
                                    saison_debut: '',
                                    saison_fin: ''
                                  });
                                }}
                              >
                                <X className="mr-2 h-4 w-4" />
                                Annuler
                              </Button>
                          )}
                        </div>
                      </form>
                    </CardContent>
                  </Card>

                  <Card className="border-border/50">
                    <CardHeader>
                      <CardTitle>Paramètres configurés</CardTitle>
                      <CardDescription>Parcelles et variétés</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {loading ? (
                        <div className="text-center py-8 text-muted-foreground">Chargement...</div>
                      ) : parametres.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          Aucun paramètre configuré
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-[600px] overflow-y-auto">
                          {parametres.map((param) => (
                            <motion.div
                              key={param.id}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="p-3 border rounded-lg flex items-center justify-between gap-3"
                            >
                              <div className="flex items-center gap-3 flex-1 flex-wrap">
                                <span className="font-medium">{param.parcelle} / {param.variety}</span>
                                <span className="text-sm text-muted-foreground">
                                  {param.nb_rangees} rangées
                                </span>
                                {(param.saison_debut || param.saison_fin) && (
                                  <Badge variant="outline" className="text-xs">
                                    Saison: {param.saison_debut || '?'} - {param.saison_fin || '?'}
                                  </Badge>
                                )}
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEditParametre(param)}
                                  disabled={editingParamId !== null && editingParamId !== param.id}
                                >
                                  <Edit2 className="h-4 w-4 text-blue-500" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeleteParametre(param.id)}
                                  disabled={editingParamId !== null}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Plants par année */}
              <TabsContent value="plants" className="mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card className="border-border/50">
                    <CardHeader>
                      <CardTitle>
                        {editingPlantsId ? 'Modifier les plants' : 'Ajouter des plants par année'}
                      </CardTitle>
                      <CardDescription>
                        {editingPlantsId ? 'Modifiez le nombre de plants' : 'Enregistrez le nombre de plants par variété et année'}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <form onSubmit={editingPlantsId ? handleUpdatePlants : handleAddPlants} className="space-y-4">
                        <div>
                          <Label htmlFor="variety_plants">Variété</Label>
                          {varieties.length > 0 ? (
                            <div className="relative">
                              <select
                                id="variety_plants"
                                value={plantsForm.variety}
                                onChange={(e) => setPlantsForm({ ...plantsForm, variety: e.target.value })}
                                className="w-full mt-1 px-3 py-2 pr-10 border rounded-md appearance-none bg-background cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                required
                              >
                                <option value="">Sélectionnez une variété</option>
                                {varieties.map((v) => (
                                  <option key={v} value={v}>
                                    {v}
                                  </option>
                                ))}
                              </select>
                              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 opacity-50 pointer-events-none" />
                            </div>
                          ) : (
                            <input
                              id="variety_plants"
                              type="text"
                              value={plantsForm.variety}
                              onChange={(e) => setPlantsForm({ ...plantsForm, variety: e.target.value })}
                              className="w-full mt-1 px-3 py-2 border rounded-md"
                              placeholder="ex: clery"
                              required
                            />
                          )}
                        </div>
                        <div>
                          <Label htmlFor="annee">Année</Label>
                          <input
                            id="annee"
                            type="number"
                            value={plantsForm.annee}
                            onChange={(e) => setPlantsForm({ ...plantsForm, annee: parseInt(e.target.value) })}
                            className="w-full mt-1 px-3 py-2 border rounded-md"
                            min="2020"
                            max="2100"
                            required
                          />
                        </div>
                        <div>
                          <Label htmlFor="nb_plants">Nombre de plants</Label>
                          <input
                            id="nb_plants"
                            type="number"
                            value={plantsForm.nb_plants}
                            onChange={(e) => setPlantsForm({ ...plantsForm, nb_plants: e.target.value })}
                            className="w-full mt-1 px-3 py-2 border rounded-md"
                            min="1"
                            required
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button type="submit" className="flex-1">
                            {editingPlantsId ? (
                              <>
                                <Save className="mr-2 h-4 w-4" />
                                Enregistrer
                              </>
                            ) : (
                              <>
                                <Plus className="mr-2 h-4 w-4" />
                                Ajouter
                              </>
                            )}
                          </Button>
                          {editingPlantsId && (
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => {
                                setEditingPlantsId(null);
                                setPlantsForm({
                                  variety: '',
                                  annee: new Date().getFullYear(),
                                  nb_plants: ''
                                });
                              }}
                            >
                              <X className="mr-2 h-4 w-4" />
                              Annuler
                            </Button>
                          )}
                        </div>
                      </form>
                    </CardContent>
                  </Card>

                  <Card className="border-border/50">
                    <CardHeader>
                      <CardTitle>Plants par année</CardTitle>
                      <CardDescription>
                        {plantsParAnnee.length} enregistrement{plantsParAnnee.length > 1 ? 's' : ''}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {loading ? (
                        <div className="text-center py-8 text-muted-foreground">Chargement...</div>
                      ) : plantsParAnnee.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground">
                          Aucun enregistrement
                        </div>
                      ) : (
                        <div className="space-y-2 max-h-[600px] overflow-y-auto">
                          {plantsParAnnee.map((plants) => (
                            <motion.div
                              key={plants.id}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`p-3 border rounded-lg flex items-center justify-between gap-3 ${
                                editingPlantsId === plants.id ? 'bg-muted' : ''
                              }`}
                            >
                              <div className="flex items-center gap-3 flex-1">
                                <Badge variant="outline">{plants.annee}</Badge>
                                <span className="font-medium">{plants.variety}</span>
                                <span className="text-sm text-muted-foreground">
                                  {plants.nb_plants} plants
                                </span>
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEditPlants(plants)}
                                  disabled={editingPlantsId !== null && editingPlantsId !== plants.id}
                                >
                                  <Edit2 className="h-4 w-4 text-blue-500" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeletePlants(plants.id)}
                                  disabled={editingPlantsId !== null}
                                >
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              {/* Récolte quotidienne */}
              <TabsContent value="recolte-quotidienne" className="mt-6">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {editingRecolteQuotidienneId && (
                    <Card className="border-border/50">
                      <CardHeader>
                        <CardTitle>Modifier la configuration</CardTitle>
                        <CardDescription>
                          Modifiez la configuration du jour sélectionné
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <form onSubmit={handleUpdateRecolteQuotidienne} className="space-y-4">
                          <div>
                            <Label htmlFor="jour_semaine">Jour de la semaine</Label>
                            <div className="relative">
                              <select
                                id="jour_semaine"
                                value={recolteQuotidienneForm.jour_semaine}
                                onChange={(e) => {
                                  const jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
                                  const index = jours.indexOf(e.target.value);
                                  setRecolteQuotidienneForm({
                                    ...recolteQuotidienneForm,
                                    jour_semaine: e.target.value,
                                    jour_semaine_num: index !== -1 ? index.toString() : recolteQuotidienneForm.jour_semaine_num
                                  });
                                }}
                                className="w-full mt-1 px-3 py-2 pr-10 border rounded-md appearance-none bg-background cursor-pointer focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
                                required
                                disabled
                              >
                                <option value={recolteQuotidienneForm.jour_semaine}>{recolteQuotidienneForm.jour_semaine}</option>
                              </select>
                              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 opacity-50 pointer-events-none" />
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">Le jour ne peut pas être modifié</p>
                          </div>
                          <div>
                            <Label htmlFor="fraction_fraiseraie">Fraction de la fraiseraie</Label>
                            <input
                              id="fraction_fraiseraie"
                              type="number"
                              step="0.01"
                              value={recolteQuotidienneForm.fraction_fraiseraie}
                              onChange={(e) => setRecolteQuotidienneForm({ ...recolteQuotidienneForm, fraction_fraiseraie: e.target.value })}
                              className="w-full mt-1 px-3 py-2 border rounded-md"
                              min="0"
                              max="1"
                              placeholder="ex: 0.33 pour 1/3"
                              required
                            />
                            <p className="text-xs text-muted-foreground mt-1">Valeur entre 0 et 1 (ex: 0.33 = 1/3, 0.5 = 1/2)</p>
                          </div>
                          <div>
                            <Label htmlFor="description">Description (optionnel)</Label>
                            <textarea
                              id="description"
                              value={recolteQuotidienneForm.description}
                              onChange={(e) => setRecolteQuotidienneForm({ ...recolteQuotidienneForm, description: e.target.value })}
                              className="w-full mt-1 px-3 py-2 border rounded-md"
                              rows="3"
                              placeholder="ex: 1/3 de la fraiseraie"
                            />
                          </div>
                          <div className="flex gap-2">
                            <Button type="submit" className="flex-1">
                              <Save className="mr-2 h-4 w-4" />
                              Enregistrer
                            </Button>
                            <Button
                              type="button"
                              variant="outline"
                              onClick={() => {
                                setEditingRecolteQuotidienneId(null);
                                setRecolteQuotidienneForm({
                                  jour_semaine: '',
                                  jour_semaine_num: '',
                                  fraction_fraiseraie: '',
                                  description: ''
                                });
                              }}
                            >
                              <X className="mr-2 h-4 w-4" />
                              Annuler
                            </Button>
                          </div>
                        </form>
                      </CardContent>
                    </Card>
                  )}

                  <Card className={editingRecolteQuotidienneId ? '' : 'lg:col-span-2'}>
                    <CardHeader>
                      <CardTitle>Configuration hebdomadaire</CardTitle>
                      <CardDescription>
                        Cliquez sur un jour pour le modifier. Les 7 jours de la semaine sont toujours présents.
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      {loading ? (
                        <div className="text-center py-8 text-muted-foreground">Chargement...</div>
                      ) : (
                        <div className="space-y-2 max-h-[600px] overflow-y-auto">
                          {getJoursSemaineComplets().map((jour) => (
                            <motion.div
                              key={jour.jour_semaine_num}
                              initial={{ opacity: 0, y: 10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className={`p-3 border rounded-lg flex items-center justify-between gap-3 cursor-pointer hover:bg-muted/30 transition-colors ${
                                editingRecolteQuotidienneId === (jour.id || `new-${jour.jour_semaine_num}`) ? 'bg-muted border-primary' : ''
                              } ${!jour.id ? 'opacity-60' : ''}`}
                              onClick={() => handleEditRecolteQuotidienne(jour)}
                            >
                              <div className="flex items-center gap-3 flex-1">
                                <Badge variant="outline">{jour.jour_semaine}</Badge>
                                <span className="text-sm text-muted-foreground">
                                  Jour #{jour.jour_semaine_num}
                                </span>
                                {jour.id ? (
                                  <>
                                    <span className="font-medium">
                                      {(jour.fraction_fraiseraie * 100).toFixed(0)}% de la fraiseraie
                                    </span>
                                    {jour.description && (
                                      <span className="text-xs text-muted-foreground">
                                        • {jour.description}
                                      </span>
                                    )}
                                  </>
                                ) : (
                                  <span className="text-xs text-muted-foreground italic">
                                    Non configuré - Cliquez pour configurer
                                  </span>
                                )}
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleEditRecolteQuotidienne(jour);
                                  }}
                                  disabled={editingRecolteQuotidienneId !== null && editingRecolteQuotidienneId !== (jour.id || `new-${jour.jour_semaine_num}`)}
                                >
                                  <Edit2 className="h-4 w-4 text-blue-500" />
                                </Button>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

export default SettingsView;

