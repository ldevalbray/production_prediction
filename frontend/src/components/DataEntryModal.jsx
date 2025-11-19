import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { X, Plus, Sun, Moon, Save } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Fonction pour déterminer le moment par défaut selon l'heure système
const getDefaultMoment = () => {
  const hour = new Date().getHours();
  // Matin : avant 14h, Soir : à partir de 14h
  return hour < 14 ? 'matin' : 'soir';
};

function DataEntryModal({ onClose, recolteToEdit = null }) {
  const isEditMode = !!recolteToEdit;
  
  // Fonction pour formater la date au format YYYY-MM-DD
  const formatDateForInput = (dateStr) => {
    if (!dateStr) return new Date().toISOString().split('T')[0];
    // Si la date est déjà au format YYYY-MM-DD, la retourner telle quelle
    if (typeof dateStr === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dateStr)) {
      return dateStr;
    }
    // Sinon, convertir avec new Date
    try {
      return new Date(dateStr).toISOString().split('T')[0];
    } catch {
      return new Date().toISOString().split('T')[0];
    }
  };

  const [formData, setFormData] = useState({
    date: formatDateForInput(recolteToEdit?.date),
    variety: recolteToEdit?.variety || '',
    moment: getDefaultMoment(), // 'matin' ou 'soir' selon l'heure système
    kg_total: recolteToEdit?.kg_total || '',
    kg_premiere_rangee: recolteToEdit?.kg_premiere_rangee || '', // Pour le mode matin
    commentaires: recolteToEdit?.commentaires || ''
  });
  const [varieties, setVarieties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingVarieties, setLoadingVarieties] = useState(true);

  useEffect(() => {
    loadVarieties();
  }, []);

  const loadVarieties = async () => {
    setLoadingVarieties(true);
    try {
      const response = await axios.get(`${API_BASE}/parametres`);
      const paramsData = response.data.data || [];
      const uniqueVarieties = [...new Set(paramsData.map(p => p.variety).filter(Boolean))].sort();
      setVarieties(uniqueVarieties);
    } catch (error) {
      console.error('Erreur lors du chargement des variétés:', error);
    } finally {
      setLoadingVarieties(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isEditMode) {
        // Mode édition : mettre à jour la récolte
        await axios.put(`${API_BASE}/recoltes/${recolteToEdit.id}`, {
          date: formData.date,
          variety: formData.variety,
          kg_total: formData.kg_total,
          commentaires: formData.commentaires
        });
      } else {
        // Mode création
        if (formData.moment === 'matin') {
          // En mode matin : enregistrer dans jour_courant
          const kg_premiere_rangee = parseFloat(formData.kg_premiere_rangee) || 0;
          await axios.post(`${API_BASE}/jour-courant`, {
            date: formData.date,
            variety: formData.variety,
            kg_premiere_rangee: kg_premiere_rangee,
            commentaires: formData.commentaires || 'Données matinales'
          });
        } else {
          // En mode soir : enregistrer dans Recoltes
          await axios.post(`${API_BASE}/recoltes`, {
            date: formData.date,
            variety: formData.variety,
            kg_total: formData.kg_total,
            commentaires: formData.commentaires ? `Soir: ${formData.commentaires}` : 'Soir'
          });
        }
      }
      onClose();
    } catch (error) {
      console.error('Erreur:', error);
      alert(`Erreur lors de l'${isEditMode ? 'modification' : formData.moment === 'matin' ? 'enregistrement des données matinales' : 'ajout de la récolte'}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="w-full max-w-md"
        >
          <Card className="border-border/50 shadow-lg">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>{isEditMode ? 'Modifier la récolte' : 'Ajouter une récolte'}</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onClose}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription>
                {isEditMode 
                  ? 'Modifiez les informations de la récolte'
                  : 'Matin : données partielles pour ajuster les prévisions du jour • Soir : récolte complète'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="date">Date</Label>
                  <input
                    id="date"
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    required
                  />
                </div>

                {!isEditMode && (
                  <div>
                    <Label htmlFor="moment">Moment</Label>
                    <div className="flex gap-2 mt-1">
                      <Button
                        type="button"
                        variant={formData.moment === 'matin' ? 'default' : 'outline'}
                        className="flex-1"
                        onClick={() => setFormData({ ...formData, moment: 'matin' })}
                      >
                        <Sun className="mr-2 h-4 w-4" />
                        Matin
                      </Button>
                      <Button
                        type="button"
                        variant={formData.moment === 'soir' ? 'default' : 'outline'}
                        className="flex-1"
                        onClick={() => setFormData({ ...formData, moment: 'soir' })}
                      >
                        <Moon className="mr-2 h-4 w-4" />
                        Soir
                      </Button>
                    </div>
                  </div>
                )}

                <div>
                  <Label htmlFor="variety">Variété</Label>
                  {loadingVarieties ? (
                    <div className="w-full mt-1 px-3 py-2 border rounded-md bg-muted animate-pulse">
                      Chargement...
                    </div>
                  ) : varieties.length > 0 ? (
                    <select
                      id="variety"
                      value={formData.variety}
                      onChange={(e) => setFormData({ ...formData, variety: e.target.value })}
                      className="w-full mt-1 pl-3 pr-12 py-2 border rounded-md select-with-spaced-chevron"
                      style={{ paddingRight: '3rem' }}
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
                      value={formData.variety}
                      onChange={(e) => setFormData({ ...formData, variety: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      placeholder="ex: clery, manon"
                      required
                    />
                  )}
                </div>

                {isEditMode ? (
                  <div>
                    <Label htmlFor="kg_total">Kg total</Label>
                    <input
                      id="kg_total"
                      type="number"
                      step="0.1"
                      value={formData.kg_total}
                      onChange={(e) => setFormData({ ...formData, kg_total: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      required
                    />
                  </div>
                ) : formData.moment === 'matin' ? (
                  <div>
                    <Label htmlFor="kg_premiere_rangee">Kg première rangée</Label>
                    <input
                      id="kg_premiere_rangee"
                      type="number"
                      step="0.1"
                      value={formData.kg_premiere_rangee}
                      onChange={(e) => setFormData({ ...formData, kg_premiere_rangee: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      placeholder="Kg récoltés sur la première rangée"
                      required
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Ces données serviront à ajuster les prévisions du jour même
                    </p>
                  </div>
                ) : (
                  <div>
                    <Label htmlFor="kg_total">Kg total</Label>
                    <input
                      id="kg_total"
                      type="number"
                      step="0.1"
                      value={formData.kg_total}
                      onChange={(e) => setFormData({ ...formData, kg_total: e.target.value })}
                      className="w-full mt-1 px-3 py-2 border rounded-md"
                      required
                    />
                  </div>
                )}

                <div>
                  <Label htmlFor="commentaires">Commentaires (optionnel)</Label>
                  <textarea
                    id="commentaires"
                    value={formData.commentaires}
                    onChange={(e) => setFormData({ ...formData, commentaires: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border rounded-md"
                    rows="3"
                  />
                </div>

                <div className="flex gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={onClose}
                    className="flex-1"
                  >
                    Annuler
                  </Button>
                  <Button
                    type="submit"
                    className="flex-1"
                    disabled={loading}
                  >
                    {loading ? (
                      'Enregistrement...'
                    ) : isEditMode ? (
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
                </div>
              </form>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

export default DataEntryModal;

