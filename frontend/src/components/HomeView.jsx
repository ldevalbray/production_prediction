import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { Separator } from './ui/separator';
import { Play, Plus, Package, Calendar, TrendingUp, Loader2, AlertCircle, Edit2, Trash2, Thermometer, Droplets, Sun } from 'lucide-react';
import DataEntryModal from './DataEntryModal';
import { UpdateNotification } from './UpdateNotification';

const API_BASE = process.env.REACT_APP_API_URL || `${window.location.origin}/api`;

const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.15 }
};

function HomeView({ onRunScript, status, loading }) {
  const [latestRecoltes, setLatestRecoltes] = useState([]);
  const [forecastSummary, setForecastSummary] = useState(null);
  const [loadingRecoltes, setLoadingRecoltes] = useState(true);
  const [loadingForecast, setLoadingForecast] = useState(true);
  const [showDataEntryModal, setShowDataEntryModal] = useState(false);
  const [isGeneratingForecast, setIsGeneratingForecast] = useState(false);
  const [recolteToEdit, setRecolteToEdit] = useState(null);

  useEffect(() => {
    fetchLatestRecoltes();
    fetchForecastSummary();
  }, []);

  // Timeout de sécurité pour éviter que le loader reste bloqué indéfiniment
  useEffect(() => {
    if (isGeneratingForecast) {
      const timeoutId = setTimeout(() => {
        console.warn('Timeout de sécurité : le loader est actif depuis plus de 10 minutes, réinitialisation...');
        setIsGeneratingForecast(false);
      }, 10 * 60 * 1000); // 10 minutes
      return () => clearTimeout(timeoutId);
    }
  }, [isGeneratingForecast]);

  // Rafraîchir les prévisions quand le script se termine
  useEffect(() => {
    console.log('HomeView useEffect - status:', { scriptRunning: status.scriptRunning, scriptMode: status.scriptMode, isGeneratingForecast });
    
    if (!status.scriptRunning) {
      // Le script n'est plus en cours d'exécution - toujours remettre isGeneratingForecast à false
      console.log('Script terminé, remise à false de isGeneratingForecast');
      setIsGeneratingForecast(false);
      
      // Si c'était une génération de prévisions, rafraîchir les données
      if (status.scriptMode === 'forecast') {
        console.log('Script forecast terminé, rafraîchissement des prévisions dans 2 secondes...');
        setTimeout(() => {
          console.log('Rafraîchissement des prévisions...');
          fetchForecastSummary();
        }, 2000);
      }
    } else if (status.scriptRunning && status.scriptMode === 'forecast') {
      // Le script est en cours et c'est une génération de prévisions
      console.log('Démarrage de la génération de prévisions');
      setIsGeneratingForecast(true);
    }
  }, [status.scriptRunning, status.scriptMode]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchLatestRecoltes = async () => {
    setLoadingRecoltes(true);
    try {
      // Récupérer toutes les récoltes
      const response = await axios.get(`${API_BASE}/recoltes`);
      const allRecoltes = response.data.data || [];
      
      if (allRecoltes.length === 0) {
        setLatestRecoltes([]);
        return;
      }
      
      // Trier par date décroissante pour trouver la date la plus récente
      const sorted = allRecoltes.sort((a, b) => new Date(b.date) - new Date(a.date));
      const mostRecentDate = new Date(sorted[0].date);
      
      // Calculer la date de début (7 jours avant la date la plus récente)
      const sevenDaysBefore = new Date(mostRecentDate);
      sevenDaysBefore.setDate(mostRecentDate.getDate() - 6); // -6 pour avoir 7 jours au total (incluant le jour le plus récent)
      
      // Filtrer les récoltes des 7 derniers jours connus
      const filteredRecoltes = sorted.filter(recolte => {
        const recolteDate = new Date(recolte.date);
        return recolteDate >= sevenDaysBefore && recolteDate <= mostRecentDate;
      });
      
      setLatestRecoltes(filteredRecoltes);
    } catch (error) {
      console.error('Erreur lors du chargement des récoltes:', error);
    } finally {
      setLoadingRecoltes(false);
    }
  };

  const fetchForecastSummary = async () => {
    setLoadingForecast(true);
    try {
      console.log('fetchForecastSummary: Début du chargement...');
      const response = await axios.get(`${API_BASE}/forecasts/latest`);
      const forecast = response.data;
      console.log('fetchForecastSummary: Réponse complète', response);
      console.log('fetchForecastSummary: forecast object', forecast);
      console.log('fetchForecastSummary: forecast.data', forecast?.data);
      console.log('fetchForecastSummary: forecast.data type', typeof forecast?.data);
      console.log('fetchForecastSummary: forecast.data is array?', Array.isArray(forecast?.data));
      console.log('fetchForecastSummary: Réponse reçue', { 
        hasData: !!forecast?.data, 
        dataLength: forecast?.data?.length,
        summary: forecast?.summary,
        keys: forecast ? Object.keys(forecast) : []
      });
      
      if (forecast && forecast.data && forecast.data.length > 0) {
        // Convertir les données numériques en nombres
        const processedData = forecast.data.map(row => ({
          ...row,
          temp_mean: typeof row.temp_mean === 'number' ? row.temp_mean : (row.temp_mean ? parseFloat(row.temp_mean) : null),
          rain_mm: typeof row.rain_mm === 'number' ? row.rain_mm : (row.rain_mm ? parseFloat(row.rain_mm) : null),
          sun_hours: typeof row.sun_hours === 'number' ? row.sun_hours : (row.sun_hours ? parseFloat(row.sun_hours) : null),
          humidity: typeof row.humidity === 'number' ? row.humidity : (row.humidity ? parseFloat(row.humidity) : null),
        }));

        // Filtrer la semaine à venir (7 jours) - prendre toutes les données disponibles
        // Le script génère déjà 7 jours (J0 à J+6)
        const nextWeek = processedData.filter(row => {
          if (!row.date) return false;
          return true; // Afficher toutes les prévisions générées
        });

        // Calculer les totaux par jour
        const dailyTotals = {};
        nextWeek.forEach(row => {
          const date = row.date;
          if (!dailyTotals[date]) {
            dailyTotals[date] = {
              total: 0,
              min: 0,
              max: 0,
              temp_mean: row.temp_mean !== null && row.temp_mean !== undefined ? row.temp_mean : null,
              rain_mm: row.rain_mm !== null && row.rain_mm !== undefined ? row.rain_mm : null,
              sun_hours: row.sun_hours !== null && row.sun_hours !== undefined ? row.sun_hours : null,
              humidity: row.humidity !== null && row.humidity !== undefined ? row.humidity : null
            };
          }
          // Convertir en nombre si nécessaire
          const kgTotal = typeof row.predicted_kg_total === 'number' ? row.predicted_kg_total : parseFloat(row.predicted_kg_total) || 0;
          const kgMin = typeof row.confidence_min_kg_total === 'number' ? row.confidence_min_kg_total : parseFloat(row.confidence_min_kg_total) || 0;
          const kgMax = typeof row.confidence_max_kg_total === 'number' ? row.confidence_max_kg_total : parseFloat(row.confidence_max_kg_total) || 0;
          
          dailyTotals[date].total += kgTotal;
          dailyTotals[date].min += kgMin;
          dailyTotals[date].max += kgMax;
        });

        const summaryData = {
          dailyTotals: Object.entries(dailyTotals).map(([date, totals]) => ({
            date,
            ...totals
          })).sort((a, b) => new Date(a.date) - new Date(b.date)),
          totalDays: Object.keys(dailyTotals).length
        };
        console.log('fetchForecastSummary: Résumé calculé', summaryData);
        console.log('fetchForecastSummary: Premier jour avec météo', summaryData.dailyTotals[0]);
        setForecastSummary(summaryData);
      } else {
        console.log('fetchForecastSummary: Aucune donnée à afficher');
        setForecastSummary(null);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des prévisions:', error);
      // Pas d'erreur si aucune prévision n'existe
      setForecastSummary(null);
    } finally {
      setLoadingForecast(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '–';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric', month: 'short' });
  };

  const formatDateShort = (dateStr) => {
    if (!dateStr) return '–';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '–';
    return typeof num === 'number' ? num.toFixed(1) : num;
  };

  const handleEditRecolte = (recolte) => {
    setRecolteToEdit(recolte);
    setShowDataEntryModal(true);
  };

  const handleDeleteRecolte = async (id) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette récolte ?')) {
      return;
    }
    try {
      await axios.delete(`${API_BASE}/recoltes/${id}`);
      fetchLatestRecoltes();
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      alert('Erreur lors de la suppression de la récolte');
    }
  };

  const handleCloseModal = () => {
    setShowDataEntryModal(false);
    setRecolteToEdit(null);
    fetchLatestRecoltes();
  };

  return (
    <div className="space-y-6">
      {/* Notification de mise à jour */}
      <UpdateNotification />
      
      {/* CTAs principaux */}
      <motion.div {...fadeIn} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Button
          className="h-20 text-lg transition-all duration-300 relative overflow-hidden group
                     hover:shadow-[0_0_20px_rgba(168,85,247,0.5),0_0_40px_rgba(168,85,247,0.3)]
                     hover:scale-[1.02] hover:border-purple-400/50"
          variant="secondary"
          onClick={() => setShowDataEntryModal(true)}
        >
          <span className="absolute inset-0 bg-gradient-to-r from-purple-500/0 via-purple-400/20 to-purple-500/0 
                          translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000" />
          <Plus className="mr-2 h-5 w-5 relative z-10 group-hover:scale-110 group-hover:rotate-90 transition-all duration-300" />
          <span className="relative z-10">Ajouter une récolte</span>
        </Button>
        <Button
          className="!h-20 !text-lg transition-all duration-300 relative overflow-hidden group
                     !bg-gradient-to-r !from-emerald-500 !via-cyan-500 !to-emerald-500
                     hover:!shadow-[0_0_30px_rgba(16,185,129,0.6),0_0_60px_rgba(6,182,212,0.4),0_0_90px_rgba(16,185,129,0.2)]
                     hover:scale-[1.03] !border-2 !border-emerald-400/50
                     disabled:hover:shadow-none disabled:hover:scale-100 disabled:opacity-70
                     !shadow-[0_0_15px_rgba(16,185,129,0.4)]"
          onClick={async () => {
            setIsGeneratingForecast(true);
            try {
              await onRunScript('forecast');
            } catch (error) {
              // En cas d'erreur, remettre l'état à false
              console.error('Erreur lors du lancement du script:', error);
              setIsGeneratingForecast(false);
            }
          }}
          disabled={status.scriptRunning || loading || isGeneratingForecast}
        >
          {/* Effet de brillance animé */}
          <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent 
                          translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000 ease-in-out" />
          
          {/* Effet de glow pulsant subtil */}
          <span className="absolute inset-0 bg-gradient-to-r from-emerald-400/15 via-cyan-400/15 to-emerald-400/15 
                          opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
          
          {/* Bordure néon animée */}
          <span className="absolute inset-0 rounded-md border-2 border-emerald-400/0 group-hover:border-emerald-300/80 
                          transition-all duration-300 shadow-[0_0_20px_rgba(16,185,129,0.5)] group-hover:shadow-[0_0_30px_rgba(16,185,129,0.8)]" />
          
          {(status.scriptRunning && status.scriptMode === 'forecast') || isGeneratingForecast ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin relative z-10 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
          ) : (
            <Play className="mr-2 h-5 w-5 relative z-10 group-hover:scale-125 group-hover:rotate-12 
                           transition-all duration-300 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
          )}
          <span className="relative z-10 font-semibold text-white drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">
            {(status.scriptRunning && status.scriptMode === 'forecast') || isGeneratingForecast 
              ? 'Génération en cours...' 
              : 'Générer les prévisions'}
          </span>
        </Button>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Récoltes des 7 derniers jours */}
        <motion.div {...fadeIn} transition={{ delay: 0.05 }}>
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Package className="h-4 w-4 text-primary" />
                Récoltes des 7 derniers jours
              </CardTitle>
              <CardDescription className="text-xs">
                Toutes les récoltes enregistrées sur la dernière semaine
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingRecoltes ? (
                <div className="space-y-2">
                  {[1, 2, 3].map(i => (
                    <Skeleton key={i} className="h-16" />
                  ))}
                </div>
              ) : latestRecoltes.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="rounded-full bg-muted p-3 mb-3">
                    <Package className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Aucune récolte enregistrée
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  {latestRecoltes.map((recolte, index) => (
                    <motion.div
                      key={recolte.id || index}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-3 border rounded-lg hover:bg-muted/30 transition-colors flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <Badge variant="outline" className="text-xs">
                          {formatDateShort(recolte.date)}
                        </Badge>
                        <span className="font-medium text-sm">{recolte.variety}</span>
                        <span className="text-sm font-semibold text-primary">
                          {recolte.kg_total} kg
                        </span>
                        {recolte.commentaires && (
                          <span className="text-xs text-muted-foreground">
                            • {recolte.commentaires}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditRecolte(recolte)}
                          className="h-8 w-8 p-0"
                        >
                          <Edit2 className="h-4 w-4 text-blue-500" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteRecolte(recolte.id)}
                          className="h-8 w-8 p-0"
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
        </motion.div>

        {/* Résumé des prévisions de la semaine */}
        <motion.div {...fadeIn} transition={{ delay: 0.1 }}>
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                Prévisions de la semaine
              </CardTitle>
              <CardDescription className="text-xs">
                Résumé des prévisions de récolte (7 jours)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingForecast ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4, 5, 6, 7].map(i => (
                    <Skeleton key={i} className="h-16" />
                  ))}
                </div>
              ) : !forecastSummary || !forecastSummary.dailyTotals || forecastSummary.dailyTotals.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <div className="rounded-full bg-muted p-3 mb-3">
                    <AlertCircle className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Aucune prévision disponible
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Générez des prévisions pour voir les données
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {forecastSummary.dailyTotals.map((day, index) => (
                    <motion.div
                      key={day.date}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-4 border rounded-lg bg-card relative"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-primary" />
                          <span className="text-sm font-medium">{formatDate(day.date)}</span>
                        </div>
                        {/* Infos météo */}
                        {(day.temp_mean !== null && day.temp_mean !== undefined) || 
                         (day.rain_mm !== null && day.rain_mm !== undefined) || 
                         (day.sun_hours !== null && day.sun_hours !== undefined) ? (
                          <div className="flex items-center gap-2 text-xs text-muted-foreground">
                            {day.temp_mean !== null && day.temp_mean !== undefined && (
                              <div className="flex items-center gap-1" title={`Température: ${formatNumber(day.temp_mean)}°C`}>
                                <Thermometer className="h-3.5 w-3.5 text-orange-500" />
                                <span className="font-medium">{formatNumber(day.temp_mean)}°</span>
                              </div>
                            )}
                            {day.rain_mm !== null && day.rain_mm !== undefined && day.rain_mm > 0 && (
                              <div className="flex items-center gap-1" title={`Pluie: ${formatNumber(day.rain_mm)} mm`}>
                                <Droplets className="h-3.5 w-3.5 text-blue-500" />
                                <span>{formatNumber(day.rain_mm)}</span>
                              </div>
                            )}
                            {day.sun_hours !== null && day.sun_hours !== undefined && (
                              <div className="flex items-center gap-1" title={`Soleil: ${formatNumber(day.sun_hours)} h`}>
                                <Sun className="h-3.5 w-3.5 text-yellow-500" />
                                <span>{formatNumber(day.sun_hours)}h</span>
                              </div>
                            )}
                          </div>
                        ) : null}
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between items-baseline">
                          <span className="text-xs text-muted-foreground">Total prévu</span>
                          <Badge className="text-sm font-semibold">
                            {formatNumber(day.total)} kg
                          </Badge>
                        </div>
                        <Separator />
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Min</span>
                          <span>{formatNumber(day.min)} kg</span>
                        </div>
                        <div className="flex justify-between text-xs">
                          <span className="text-muted-foreground">Max</span>
                          <span>{formatNumber(day.max)} kg</span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

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

export default HomeView;

