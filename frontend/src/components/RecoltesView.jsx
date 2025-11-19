import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Plus, Edit2, Trash2, Moon, TrendingUp, Package, Calendar, BarChart3, Filter, X, Download } from 'lucide-react';
import DataEntryModal from './DataEntryModal';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.15 }
};

function RecoltesView() {
  const [recoltes, setRecoltes] = useState([]);
  const [loading, setLoading] = useState(false);
  const [recolteToEdit, setRecolteToEdit] = useState(null);
  const [showDataEntryModal, setShowDataEntryModal] = useState(false);
  
  // Filtres
  const [filterVariety, setFilterVariety] = useState('all');
  const [filterDateStart, setFilterDateStart] = useState('');
  const [filterDateEnd, setFilterDateEnd] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/recoltes`);
      setRecoltes(response.data.data || []);
    } catch (error) {
      console.error('Erreur lors du chargement:', error);
      alert('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleEditRecolte = (recolte) => {
    setRecolteToEdit(recolte);
    setShowDataEntryModal(true);
  };

  const handleCloseModal = () => {
    setShowDataEntryModal(false);
    setRecolteToEdit(null);
    loadData();
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

  const formatDateShort = (dateStr) => {
    if (!dateStr) return '–';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const getMomentFromComment = (comment) => {
    if (!comment) return null;
    if (comment.toLowerCase().includes('matin')) return 'matin';
    if (comment.toLowerCase().includes('soir')) return 'soir';
    return null;
  };

  // Calcul des statistiques et filtrage
  const { filteredRecoltes, statistics, varieties } = useMemo(() => {
    // Extraire les variétés uniques
    const uniqueVarieties = [...new Set(recoltes.map(r => r.variety).filter(Boolean))].sort();
    
    // Filtrer les récoltes
    let filtered = [...recoltes];
    
    if (filterVariety !== 'all') {
      filtered = filtered.filter(r => r.variety === filterVariety);
    }
    
    if (filterDateStart) {
      filtered = filtered.filter(r => new Date(r.date) >= new Date(filterDateStart));
    }
    
    if (filterDateEnd) {
      filtered = filtered.filter(r => new Date(r.date) <= new Date(filterDateEnd));
    }
    
    // Calculer les statistiques
    const totalKg = filtered.reduce((sum, r) => sum + parseFloat(r.kg_total || 0), 0);
    const count = filtered.length;
    const average = count > 0 ? totalKg / count : 0;
    
    // Récoltes du mois
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    const monthRecoltes = filtered.filter(r => new Date(r.date) >= monthStart);
    const monthKg = monthRecoltes.reduce((sum, r) => sum + parseFloat(r.kg_total || 0), 0);
    
    // Récoltes de la semaine
    const weekStart = new Date(now);
    weekStart.setDate(now.getDate() - now.getDay());
    weekStart.setHours(0, 0, 0, 0);
    const weekRecoltes = filtered.filter(r => new Date(r.date) >= weekStart);
    const weekKg = weekRecoltes.reduce((sum, r) => sum + parseFloat(r.kg_total || 0), 0);
    
    // Top variétés
    const varietyStats = {};
    filtered.forEach(r => {
      if (!varietyStats[r.variety]) {
        varietyStats[r.variety] = { count: 0, total: 0 };
      }
      varietyStats[r.variety].count++;
      varietyStats[r.variety].total += parseFloat(r.kg_total || 0);
    });
    const topVarieties = Object.entries(varietyStats)
      .map(([variety, stats]) => ({ variety, ...stats }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 3);
    
    // Moyenne par jour (nombre de jours uniques avec récoltes)
    const uniqueDays = new Set(filtered.map(r => r.date));
    const daysCount = uniqueDays.size;
    const averagePerDay = daysCount > 0 ? totalKg / daysCount : 0;
    
    return {
      filteredRecoltes: filtered,
      statistics: {
        totalKg: totalKg.toFixed(1),
        count,
        average: average.toFixed(1),
        monthKg: monthKg.toFixed(1),
        monthCount: monthRecoltes.length,
        weekKg: weekKg.toFixed(1),
        weekCount: weekRecoltes.length,
        topVarieties,
        averagePerDay: averagePerDay.toFixed(1),
        daysCount
      },
      varieties: uniqueVarieties
    };
  }, [recoltes, filterVariety, filterDateStart, filterDateEnd]);

  const resetFilters = () => {
    setFilterVariety('all');
    setFilterDateStart('');
    setFilterDateEnd('');
  };

  const hasActiveFilters = filterVariety !== 'all' || filterDateStart || filterDateEnd;

  const downloadRecoltes = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/recoltes/download`,
        { responseType: 'blob' }
      );
      // Créer un lien de téléchargement
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'recoltes_export.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Erreur lors du téléchargement:', error);
      alert('Erreur lors du téléchargement des récoltes');
    }
  };

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <motion.div {...fadeIn} className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Récoltes</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Gérez toutes vos récoltes
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={downloadRecoltes} variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Télécharger
          </Button>
          <Button onClick={() => setShowDataEntryModal(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Ajouter une récolte
          </Button>
        </div>
      </motion.div>

      {/* Filtres - Sticky en haut */}
      {!loading && recoltes.length > 0 && (
        <motion.div {...fadeIn} transition={{ delay: 0.05 }} className="sticky top-0 z-10 bg-background pb-2">
          <Card className="border-border/50 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Filter className="h-4 w-4 text-primary" />
                  Filtres
                </CardTitle>
                {hasActiveFilters && (
                  <Button variant="ghost" size="sm" onClick={resetFilters}>
                    <X className="mr-2 h-4 w-4" />
                    Réinitialiser
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Variété</Label>
                  <Select value={filterVariety} onValueChange={setFilterVariety}>
                    <SelectTrigger>
                      <SelectValue placeholder="Toutes les variétés" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Toutes les variétés</SelectItem>
                      {varieties.map(v => (
                        <SelectItem key={v} value={v}>{v}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Date début</Label>
                  <input
                    type="date"
                    value={filterDateStart}
                    onChange={(e) => setFilterDateStart(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-xs">Date fin</Label>
                  <input
                    type="date"
                    value={filterDateEnd}
                    onChange={(e) => setFilterDateEnd(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md text-sm"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Statistiques */}
      {!loading && recoltes.length > 0 && (
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                Statistiques
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2 mb-1">
                    <Package className="h-3.5 w-3.5 text-muted-foreground" />
                    <Label className="text-xs text-muted-foreground">Total</Label>
                  </div>
                  <p className="text-xl font-semibold">{statistics.totalKg} kg</p>
                  <p className="text-xs text-muted-foreground mt-1">{statistics.count} récolte{statistics.count > 1 ? 's' : ''}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                    <Label className="text-xs text-muted-foreground">Moyenne</Label>
                  </div>
                  <p className="text-xl font-semibold">{statistics.average} kg</p>
                  <p className="text-xs text-muted-foreground mt-1">par récolte</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <Label className="text-xs text-muted-foreground">Moyenne / jour</Label>
                  </div>
                  <p className="text-xl font-semibold">{statistics.averagePerDay} kg</p>
                  <p className="text-xs text-muted-foreground mt-1">sur {statistics.daysCount} jour{statistics.daysCount > 1 ? 's' : ''}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <Label className="text-xs text-muted-foreground">Ce mois</Label>
                  </div>
                  <p className="text-xl font-semibold">{statistics.monthKg} kg</p>
                  <p className="text-xs text-muted-foreground mt-1">{statistics.monthCount} récolte{statistics.monthCount > 1 ? 's' : ''}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2 mb-1">
                    <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                    <Label className="text-xs text-muted-foreground">Cette semaine</Label>
                  </div>
                  <p className="text-xl font-semibold">{statistics.weekKg} kg</p>
                  <p className="text-xs text-muted-foreground mt-1">{statistics.weekCount} récolte{statistics.weekCount > 1 ? 's' : ''}</p>
                </div>
                {statistics.topVarieties.length > 0 && (
                  <div className="p-3 rounded-lg bg-muted/50 border border-border/50">
                    <div className="flex items-center gap-2 mb-1">
                      <TrendingUp className="h-3.5 w-3.5 text-muted-foreground" />
                      <Label className="text-xs text-muted-foreground">Top variété</Label>
                    </div>
                    <p className="text-lg font-semibold">{statistics.topVarieties[0]?.variety || '–'}</p>
                    <p className="text-xs text-muted-foreground mt-1">{statistics.topVarieties[0]?.total.toFixed(1) || '0'} kg</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Liste */}
      <motion.div {...fadeIn} transition={{ delay: 0.15 }}>
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle>Historique des récoltes</CardTitle>
            <CardDescription>
              {filteredRecoltes.length} récolte{filteredRecoltes.length > 1 ? 's' : ''} affichée{filteredRecoltes.length > 1 ? 's' : ''}
              {hasActiveFilters && ` (sur ${recoltes.length} total)`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Chargement...</div>
            ) : filteredRecoltes.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                {hasActiveFilters ? 'Aucune récolte ne correspond aux filtres' : 'Aucune récolte enregistrée'}
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto">
                {filteredRecoltes
                  .sort((a, b) => new Date(b.date) - new Date(a.date))
                  .map((recolte) => {
                    const moment = getMomentFromComment(recolte.commentaires);
                    return (
                      <motion.div
                        key={recolte.id}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-3 border rounded-lg flex items-center justify-between gap-3 hover:bg-muted/30 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1">
                          <Badge variant="outline">{formatDateShort(recolte.date)}</Badge>
                          <span className="font-medium">{recolte.variety}</span>
                          {moment === 'soir' && (
                            <Badge variant="secondary" className="text-xs">
                              <Moon className="mr-1 h-3 w-3" />
                              soir
                            </Badge>
                          )}
                          <span className="text-sm font-semibold text-primary">
                            {recolte.kg_total} kg
                          </span>
                          {recolte.commentaires && moment !== 'soir' && (
                            <span className="text-sm text-muted-foreground">
                              • {recolte.commentaires}
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleEditRecolte(recolte)}
                          >
                            <Edit2 className="h-4 w-4 text-blue-500" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteRecolte(recolte.id)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        </div>
                      </motion.div>
                    );
                  })}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Modal pour ajouter/modifier une récolte */}
      {showDataEntryModal && (
        <DataEntryModal
          onClose={handleCloseModal}
          recolteToEdit={recolteToEdit}
        />
      )}
    </div>
  );
}

export default RecoltesView;

