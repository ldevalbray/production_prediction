import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Plus, Trash2, Edit2, Save, X, Download, Package, Settings, Sprout, Sun, Upload } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function DataEntry() {
  const [activeTab, setActiveTab] = useState('recoltes');
  const [recoltes, setRecoltes] = useState([]);
  const [parametres, setParametres] = useState([]);
  const [plantsParAnnee, setPlantsParAnnee] = useState([]);
  const [jourCourant, setJourCourant] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editingPlantsId, setEditingPlantsId] = useState(null);
  const [editingJourId, setEditingJourId] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [importing, setImporting] = useState(false);
  const fileInputRef = React.useRef(null);
  
  // Formulaire de récolte
  const [recolteForm, setRecolteForm] = useState({
    date: new Date().toISOString().split('T')[0],
    variety: '',
    kg_total: '',
    commentaires: ''
  });

  // Formulaire de paramètre
  const [parametreForm, setParametreForm] = useState({
    parcelle: '',
    variety: '',
    nb_rangees: 10
  });

  // Formulaire de plants par année
  const [plantsForm, setPlantsForm] = useState({
    variety: '',
    annee: new Date().getFullYear(),
    nb_plants: ''
  });

  // Formulaire de jour courant
  const [jourCourantForm, setJourCourantForm] = useState({
    date: new Date().toISOString().split('T')[0],
    variety: '',
    kg_premiere_rangee: '',
    commentaires: ''
  });

  // Récupérer les variétés uniques depuis les paramètres
  const varieties = [...new Set(parametres.map(p => p.variety).filter(Boolean))].sort();

  useEffect(() => {
    loadData();
    // Charger aussi les paramètres pour avoir la liste des variétés
    if (activeTab === 'recoltes' || activeTab === 'plants' || activeTab === 'jour-courant') {
      loadParametres();
    }
  }, [activeTab]);

  const loadParametres = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parametres`);
      setParametres(response.data.data || []);
    } catch (error) {
      console.error('Erreur lors du chargement des paramètres:', error);
    }
  };

  const loadData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'recoltes') {
        const response = await axios.get(`${API_BASE}/recoltes`);
        setRecoltes(response.data.data || []);
      } else if (activeTab === 'parametres') {
        const response = await axios.get(`${API_BASE}/parametres`);
        setParametres(response.data.data || []);
      } else if (activeTab === 'plants') {
        const response = await axios.get(`${API_BASE}/plants-par-annee`);
        setPlantsParAnnee(response.data.data || []);
      } else if (activeTab === 'jour-courant') {
        const response = await axios.get(`${API_BASE}/jour-courant`);
        setJourCourant(response.data.data || []);
      }
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      alert('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRecolte = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/recoltes`, recolteForm);
      setRecolteForm({
        date: new Date().toISOString().split('T')[0],
        variety: '',
        kg_total: '',
        commentaires: ''
      });
      setEditingId(null);
      loadData();
      alert('Récolte ajoutée avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'ajout de la récolte');
    }
  };

  const handleEditRecolte = (recolte) => {
    setEditingId(recolte.id);
    setRecolteForm({
      date: recolte.date,
      variety: recolte.variety,
      kg_total: recolte.kg_total,
      commentaires: recolte.commentaires || ''
    });
  };

  const handleUpdateRecolte = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API_BASE}/recoltes/${editingId}`, recolteForm);
      setRecolteForm({
        date: new Date().toISOString().split('T')[0],
        variety: '',
        kg_total: '',
        commentaires: ''
      });
      setEditingId(null);
      loadData();
      alert('Récolte modifiée avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la modification de la récolte');
    }
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setRecolteForm({
      date: new Date().toISOString().split('T')[0],
      variety: '',
      kg_total: '',
      commentaires: ''
    });
  };

  const handleAddParametre = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_BASE}/parametres`, parametreForm);
      setParametreForm({
        parcelle: '',
        variety: '',
        nb_rangees: 10
      });
      loadData();
      alert('Paramètre ajouté avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'ajout du paramètre');
    }
  };

  const handleDeleteRecolte = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette récolte ?')) return;
    try {
      await axios.delete(`${API_BASE}/recoltes/${id}`);
      loadData();
      alert('Récolte supprimée');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleDeleteParametre = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce paramètre ?')) return;
    try {
      await axios.delete(`${API_BASE}/parametres/${id}`);
      loadData();
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
      loadData();
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
      // Note: L'API actuelle ne supporte pas PUT, on doit supprimer et recréer
      // Ou on peut utiliser POST qui fait un upsert
      await axios.post(`${API_BASE}/plants-par-annee`, plantsForm);
      setPlantsForm({
        variety: '',
        annee: new Date().getFullYear(),
        nb_plants: ''
      });
      setEditingPlantsId(null);
      loadData();
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
      loadData();
      alert('Enregistrement supprimé');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleAddJourCourant = async (e) => {
    e.preventDefault();
    try {
      if (editingJourId) {
        // Pour la modification, on utilise POST qui fait un upsert
        await axios.post(`${API_BASE}/jour-courant`, jourCourantForm);
      } else {
        await axios.post(`${API_BASE}/jour-courant`, jourCourantForm);
      }
      setJourCourantForm({
        date: new Date().toISOString().split('T')[0],
        variety: '',
        kg_premiere_rangee: '',
        commentaires: ''
      });
      setEditingJourId(null);
      loadData();
      alert('Données du jour courant enregistrées avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'enregistrement');
    }
  };

  const handleEditJourCourant = (jour) => {
    setEditingJourId(jour.id || `${jour.date}_${jour.variety}`);
    setJourCourantForm({
      date: jour.date,
      variety: jour.variety,
      kg_premiere_rangee: jour.kg_premiere_rangee || '',
      commentaires: jour.commentaires || ''
    });
  };

  const handleDeleteJourCourant = async (date, variety) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ces données ?')) return;
    try {
      await axios.delete(`${API_BASE}/jour-courant?date=${date}`);
      loadData();
      alert('Données supprimées');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de la suppression');
    }
  };

  const handleImportExcel = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
      alert('Veuillez sélectionner un fichier Excel (.xlsx ou .xls)');
      return;
    }
    
    if (!confirm('Voulez-vous vraiment importer ces données ? Les données existantes seront complétées (pas remplacées).')) {
      return;
    }
    
    setImporting(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API_BASE}/db/upload-excel`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      alert(response.data.message || 'Données importées avec succès !');
      // Recharger les données
      loadData();
      loadParametres();
    } catch (error) {
      console.error('Erreur lors de l\'import:', error);
      alert(error.response?.data?.error || 'Erreur lors de l\'import des données');
    } finally {
      setImporting(false);
      // Réinitialiser l'input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      // Exporter vers Excel (template avec données actuelles)
      const response = await fetch(`${API_BASE}/db/export-template`, {
        method: 'GET'
      });
      if (!response.ok) {
        throw new Error('Erreur lors de l\'export');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `recoltes_fraises_template_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      alert('Template Excel exporté avec succès !');
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'export');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Onglets et bouton export */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2 border-b overflow-x-auto">
          <Button
            variant={activeTab === 'recoltes' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('recoltes')}
            className="rounded-b-none"
          >
            <Package className="mr-2 h-4 w-4" />
            Récoltes
          </Button>
          <Button
            variant={activeTab === 'parametres' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('parametres')}
            className="rounded-b-none"
          >
            <Settings className="mr-2 h-4 w-4" />
            Paramètres
          </Button>
          <Button
            variant={activeTab === 'plants' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('plants')}
            className="rounded-b-none"
          >
            <Sprout className="mr-2 h-4 w-4" />
            Plants/Année
          </Button>
          <Button
            variant={activeTab === 'jour-courant' ? 'default' : 'ghost'}
            onClick={() => setActiveTab('jour-courant')}
            className="rounded-b-none"
          >
            <Sun className="mr-2 h-4 w-4" />
            Jour courant
          </Button>
        </div>
        <Button
          variant="outline"
          onClick={handleExport}
          disabled={exporting}
        >
          <Download className="mr-2 h-4 w-4" />
          {exporting ? 'Export en cours...' : 'Exporter vers Excel'}
        </Button>
      </div>

      {/* Formulaire et liste des récoltes */}
      {activeTab === 'recoltes' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulaire */}
          <Card>
            <CardHeader>
              <CardTitle>
                {editingId ? 'Modifier la récolte' : 'Ajouter une récolte'}
              </CardTitle>
              <CardDescription>
                {editingId ? 'Modifiez les informations de la récolte' : 'Enregistrez une nouvelle récolte'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={editingId ? handleUpdateRecolte : handleAddRecolte} className="space-y-4">
                <div>
                  <Label htmlFor="date">Date</Label>
                  <input
                    id="date"
                    type="date"
                    value={recolteForm.date}
                    onChange={(e) => setRecolteForm({ ...recolteForm, date: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="variety">Variété</Label>
                  {varieties.length > 0 ? (
                    <select
                      id="variety"
                      value={recolteForm.variety}
                      onChange={(e) => setRecolteForm({ ...recolteForm, variety: e.target.value })}
                      className="w-full mt-1 pl-3 pr-8 py-2 border rounded-md"
                      required
                    >
                      <option value="">Sélectionnez une variété</option>
                      {varieties.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id="variety"
                      type="text"
                      value={recolteForm.variety}
                      onChange={(e) => setRecolteForm({ ...recolteForm, variety: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      placeholder="ex: clery, manon"
                      required
                    />
                  )}
                </div>
                <div>
                  <Label htmlFor="kg_total">Kg total</Label>
                  <input
                    id="kg_total"
                    type="number"
                    step="0.1"
                    value={recolteForm.kg_total}
                    onChange={(e) => setRecolteForm({ ...recolteForm, kg_total: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="commentaires">Commentaires (optionnel)</Label>
                  <textarea
                    id="commentaires"
                    value={recolteForm.commentaires}
                    onChange={(e) => setRecolteForm({ ...recolteForm, commentaires: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    rows="3"
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    {editingId ? (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Enregistrer
                      </>
                    ) : (
                      <>
                        <Plus className="mr-2 h-4 w-4" />
                        Ajouter la récolte
                      </>
                    )}
                  </Button>
                  {editingId && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleCancelEdit}
                    >
                      <X className="mr-2 h-4 w-4" />
                      Annuler
                    </Button>
                  )}
                </div>
              </form>
            </CardContent>
          </Card>

          {/* Liste */}
          <Card>
            <CardHeader>
              <CardTitle>Historique des récoltes</CardTitle>
              <CardDescription>
                {recoltes.length} récolte{recoltes.length > 1 ? 's' : ''} enregistrée{recoltes.length > 1 ? 's' : ''}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Chargement...</div>
              ) : recoltes.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Aucune récolte enregistrée
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {recoltes.map((recolte) => (
                    <motion.div
                      key={recolte.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-3 border rounded-lg flex items-center justify-between ${
                        editingId === recolte.id ? 'bg-muted' : ''
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{recolte.date}</Badge>
                          <span className="font-medium">{recolte.variety}</span>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {recolte.kg_total} kg
                          {recolte.commentaires && ` • ${recolte.commentaires}`}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditRecolte(recolte)}
                          disabled={editingId !== null && editingId !== recolte.id}
                        >
                          <Edit2 className="h-4 w-4 text-blue-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteRecolte(recolte.id)}
                          disabled={editingId !== null}
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
      )}

      {/* Formulaire et liste des paramètres */}
      {activeTab === 'parametres' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulaire */}
          <Card>
            <CardHeader>
              <CardTitle>Ajouter un paramètre</CardTitle>
              <CardDescription>Configurez une parcelle/variété</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddParametre} className="space-y-4">
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
                <Button type="submit" className="w-full">
                  <Plus className="mr-2 h-4 w-4" />
                  Ajouter le paramètre
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Liste */}
          <Card>
            <CardHeader>
              <CardTitle>Paramètres configurés</CardTitle>
              <CardDescription>Parcelles et variétés</CardDescription>
              <div className="flex gap-2 mt-4">
                <input
                  type="file"
                  accept=".xlsx,.xls"
                  ref={fileInputRef}
                  onChange={handleImportExcel}
                  style={{ display: 'none' }}
                />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={importing}
                >
                  <Upload className="mr-2 h-4 w-4" />
                  {importing ? 'Import...' : 'Importer Excel'}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                  disabled={exporting}
                >
                  <Download className="mr-2 h-4 w-4" />
                  {exporting ? 'Export...' : 'Télécharger template'}
                </Button>
              </div>
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
                      className="p-3 border rounded-lg flex items-center justify-between"
                    >
                      <div>
                        <div className="font-medium">{param.parcelle} / {param.variety}</div>
                        <div className="text-sm text-muted-foreground">
                          {param.nb_rangees} rangées
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteParametre(param.id)}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Formulaire et liste des plants par année */}
      {activeTab === 'plants' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulaire */}
          <Card>
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
                    <select
                      id="variety_plants"
                      value={plantsForm.variety}
                      onChange={(e) => setPlantsForm({ ...plantsForm, variety: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      required
                    >
                      <option value="">Sélectionnez une variété</option>
                      {varieties.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
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

          {/* Liste */}
          <Card>
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
      )}

      {/* Formulaire et liste du jour courant */}
      {activeTab === 'jour-courant' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Formulaire */}
          <Card>
            <CardHeader>
              <CardTitle>
                {editingJourId ? 'Modifier les données du jour' : 'Données du jour courant'}
              </CardTitle>
              <CardDescription>
                {editingJourId ? 'Modifiez les données matinales' : 'Enregistrez les données de récolte matinale'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleAddJourCourant} className="space-y-4">
                <div>
                  <Label htmlFor="date_jour">Date</Label>
                  <input
                    id="date_jour"
                    type="date"
                    value={jourCourantForm.date}
                    onChange={(e) => setJourCourantForm({ ...jourCourantForm, date: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="variety_jour">Variété</Label>
                  {varieties.length > 0 ? (
                    <select
                      id="variety_jour"
                      value={jourCourantForm.variety}
                      onChange={(e) => setJourCourantForm({ ...jourCourantForm, variety: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      required
                    >
                      <option value="">Sélectionnez une variété</option>
                      {varieties.map((v) => (
                        <option key={v} value={v}>
                          {v}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      id="variety_jour"
                      type="text"
                      value={jourCourantForm.variety}
                      onChange={(e) => setJourCourantForm({ ...jourCourantForm, variety: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      placeholder="ex: clery"
                      required
                    />
                  )}
                </div>
                <div>
                  <Label htmlFor="kg_premiere_rangee">Kg première rangée</Label>
                  <input
                    id="kg_premiere_rangee"
                    type="number"
                    step="0.1"
                    value={jourCourantForm.kg_premiere_rangee}
                    onChange={(e) => setJourCourantForm({ ...jourCourantForm, kg_premiere_rangee: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    placeholder="Kg récoltés sur la première rangée"
                  />
                </div>
                <div>
                  <Label htmlFor="commentaires_jour">Commentaires (optionnel)</Label>
                  <textarea
                    id="commentaires_jour"
                    value={jourCourantForm.commentaires}
                    onChange={(e) => setJourCourantForm({ ...jourCourantForm, commentaires: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    rows="3"
                  />
                </div>
                <div className="flex gap-2">
                  <Button type="submit" className="flex-1">
                    {editingJourId ? (
                      <>
                        <Save className="mr-2 h-4 w-4" />
                        Enregistrer
                      </>
                    ) : (
                      <>
                        <Plus className="mr-2 h-4 w-4" />
                        Enregistrer
                      </>
                    )}
                  </Button>
                  {editingJourId && (
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setEditingJourId(null);
                        setJourCourantForm({
                          date: new Date().toISOString().split('T')[0],
                          variety: '',
                          kg_premiere_rangee: '',
                          commentaires: ''
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

          {/* Liste */}
          <Card>
            <CardHeader>
              <CardTitle>Données du jour courant</CardTitle>
              <CardDescription>
                Données matinales de récolte
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-muted-foreground">Chargement...</div>
              ) : jourCourant.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  Aucune donnée enregistrée
                </div>
              ) : (
                <div className="space-y-2 max-h-[600px] overflow-y-auto">
                  {jourCourant.map((jour) => (
                    <motion.div
                      key={jour.id || `${jour.date}_${jour.variety}`}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className={`p-3 border rounded-lg flex items-center justify-between ${
                        editingJourId === (jour.id || `${jour.date}_${jour.variety}`) ? 'bg-muted' : ''
                      }`}
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">{jour.date}</Badge>
                          <span className="font-medium">{jour.variety}</span>
                        </div>
                        <div className="text-sm text-muted-foreground mt-1">
                          {jour.kg_premiere_rangee ? `${jour.kg_premiere_rangee} kg (1ère rangée)` : 'Aucune donnée'}
                          {jour.commentaires && ` • ${jour.commentaires}`}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditJourCourant(jour)}
                          disabled={editingJourId !== null && editingJourId !== (jour.id || `${jour.date}_${jour.variety}`)}
                        >
                          <Edit2 className="h-4 w-4 text-blue-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteJourCourant(jour.date, jour.variety)}
                          disabled={editingJourId !== null}
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
      )}
    </div>
  );
}

export default DataEntry;
