import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Skeleton } from './ui/skeleton';
import { Separator } from './ui/separator';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Loader2, Download, Calendar, TrendingUp, Sun, Droplets, Thermometer, BarChart3, AlertCircle, Filter, X, Play } from 'lucide-react';
import { Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, Line } from 'recharts';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const fadeIn = {
  initial: { opacity: 0 },
  animate: { opacity: 1 },
  transition: { duration: 0.15 }
};

function ForecastView() {
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [selectedParcelle, setSelectedParcelle] = useState(null);
  const [selectedVariety, setSelectedVariety] = useState(null);
  const [status, setStatus] = useState({ scriptRunning: false, scriptMode: null });
  const [seasonError, setSeasonError] = useState(null);

  const hasActiveFilters = selectedDate || selectedParcelle || selectedVariety;

  const resetFilters = () => {
    setSelectedDate(null);
    setSelectedParcelle(null);
    setSelectedVariety(null);
  };

  // Vérifier le statut périodiquement pour rafraîchir après génération
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`);
        setStatus(response.data);
      } catch (error) {
        console.error('Erreur lors de la récupération du statut:', error);
      }
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchLatestForecast();
  }, []);

  // Rafraîchir les prévisions quand le script se termine
  useEffect(() => {
    if (!status.scriptRunning && status.scriptMode === 'forecast') {
      // Réinitialiser l'erreur de saison si la génération a réussi
      setSeasonError(null);
      // Attendre un peu pour que le fichier soit créé
      const timeoutId = setTimeout(() => {
        fetchLatestForecast();
      }, 2000);
      return () => clearTimeout(timeoutId);
    }
  }, [status.scriptRunning, status.scriptMode]); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchLatestForecast = async () => {
    setLoading(true);
    setError(null);
    setSeasonError(null); // Réinitialiser l'erreur de saison lors du chargement
    try {
      const response = await axios.get(`${API_BASE}/forecasts/latest`);
      const data = response.data;
      
      // S'assurer que les données numériques sont bien des nombres
      if (data && data.data && Array.isArray(data.data)) {
        data.data = data.data.map(row => ({
          ...row,
          predicted_kg_total: typeof row.predicted_kg_total === 'number' ? row.predicted_kg_total : parseFloat(row.predicted_kg_total) || 0,
          predicted_kg_par_rangee: typeof row.predicted_kg_par_rangee === 'number' ? row.predicted_kg_par_rangee : parseFloat(row.predicted_kg_par_rangee) || 0,
          confidence_min_kg_total: typeof row.confidence_min_kg_total === 'number' ? row.confidence_min_kg_total : parseFloat(row.confidence_min_kg_total) || 0,
          confidence_max_kg_total: typeof row.confidence_max_kg_total === 'number' ? row.confidence_max_kg_total : parseFloat(row.confidence_max_kg_total) || 0,
          temp_mean: typeof row.temp_mean === 'number' ? row.temp_mean : (row.temp_mean ? parseFloat(row.temp_mean) : null),
          temp_min: typeof row.temp_min === 'number' ? row.temp_min : (row.temp_min ? parseFloat(row.temp_min) : null),
          temp_max: typeof row.temp_max === 'number' ? row.temp_max : (row.temp_max ? parseFloat(row.temp_max) : null),
          rain_mm: typeof row.rain_mm === 'number' ? row.rain_mm : (row.rain_mm ? parseFloat(row.rain_mm) : null),
          sun_hours: typeof row.sun_hours === 'number' ? row.sun_hours : (row.sun_hours ? parseFloat(row.sun_hours) : null),
          humidity: typeof row.humidity === 'number' ? row.humidity : (row.humidity ? parseFloat(row.humidity) : null),
        }));
      }
      
      setForecast(data);
      // Initialiser avec "all" pour afficher toutes les données par défaut
      setSelectedDate(null);
      setSelectedParcelle(null);
      setSelectedVariety(null);
    } catch (err) {
      console.error('Erreur lors du chargement des prévisions:', err);
      const errorMessage = err.response?.data?.error || 'Erreur lors du chargement des prévisions';
      setError(errorMessage);
      // Si c'est une erreur 404 (aucune prévision), ne pas définir forecast pour afficher le message approprié
      if (err.response?.status === 404) {
        setForecast(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const downloadForecast = async () => {
    if (forecast?.date) {
      try {
        const response = await axios.get(
          `${API_BASE}/forecasts/${forecast.date}/download`,
          { responseType: 'blob' }
        );
        // Créer un lien de téléchargement
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', forecast.filename || `forecast_${forecast.date}.xlsx`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Erreur lors du téléchargement:', error);
        alert('Erreur lors du téléchargement de la prévision');
      }
    }
  };

  // Vérifier si on est dans une saison de récolte
  const isInHarvestSeason = async () => {
    try {
      const response = await axios.get(`${API_BASE}/parametres`);
      const params = response.data?.data || [];
      
      if (!Array.isArray(params) || params.length === 0) {
        return false;
      }
      
      const currentMonth = new Date().getMonth() + 1; // getMonth() retourne 0-11, donc +1 pour avoir 1-12
      
      // Vérifier si au moins une variété est en saison
      for (const param of params) {
        const saison_debut = param.saison_debut;
        const saison_fin = param.saison_fin;
        
        // Si les valeurs sont manquantes, on ignore cette variété
        if (saison_debut === null || saison_debut === undefined || 
            saison_fin === null || saison_fin === undefined) {
          continue;
        }
        
        try {
          const start = parseInt(saison_debut);
          const end = parseInt(saison_fin);
          
          // Gérer les saisons qui chevauchent l'année (ex: 11-3 pour nov-mars)
          if (start <= end) {
            // Saison normale (ex: 3-9 pour mars-septembre)
            if (start <= currentMonth && currentMonth <= end) {
              return true;
            }
          } else {
            // Saison qui chevauche l'année (ex: 11-3 pour novembre à mars)
            if (currentMonth >= start || currentMonth <= end) {
              return true;
            }
          }
        } catch (e) {
          // Ignorer les erreurs de conversion
          continue;
        }
      }
      
      return false;
    } catch (error) {
      console.error('Erreur lors de la vérification de la saison:', error);
      // En cas d'erreur, on autorise la génération (ne pas bloquer)
      return true;
    }
  };

  const generateForecast = async () => {
    if (status.scriptRunning) {
      return;
    }
    
    // Réinitialiser les erreurs précédentes
    setSeasonError(null);
    setError(null);
    
    // Vérifier si on est dans une saison de récolte
    const inSeason = await isInHarvestSeason();
    if (!inSeason) {
      setSeasonError('Période en dehors des saisons de récoltes');
      return;
    }
    
    try {
      await axios.post(`${API_BASE}/run`, { mode: 'forecast' });
      // Le statut sera mis à jour automatiquement via le useEffect qui surveille status.scriptRunning
    } catch (error) {
      console.error('Erreur lors de la génération des prévisions:', error);
      setError(error.response?.data?.error || 'Erreur lors de la génération des prévisions');
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return '–';
    return typeof num === 'number' ? num.toFixed(2) : num;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '–';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  };

  const formatDateShort = (dateStr) => {
    if (!dateStr) return '–';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  // Filtrer les données selon les sélections
  const filteredData = forecast?.data?.filter(row => {
    if (selectedDate && selectedDate !== 'all' && row.date !== selectedDate) return false;
    if (selectedParcelle && selectedParcelle !== 'all' && row.parcelle !== selectedParcelle) return false;
    if (selectedVariety && selectedVariety !== 'all' && row.variety !== selectedVariety) return false;
    return true;
  }) || [];

  // Calculer les totaux par jour
  const dailyTotals = {};
  filteredData.forEach(row => {
    const date = row.date;
    if (!dailyTotals[date]) {
      dailyTotals[date] = {
        total: 0,
        min: 0,
        max: 0,
        count: 0,
        temp_mean: row.temp_mean || null,
        rain_mm: row.rain_mm || null,
        sun_hours: row.sun_hours || null,
        humidity: row.humidity || null
      };
    }
    if (row.predicted_kg_total) {
      dailyTotals[date].total += row.predicted_kg_total;
      dailyTotals[date].min += (row.confidence_min_kg_total || 0);
      dailyTotals[date].max += (row.confidence_max_kg_total || 0);
      dailyTotals[date].count += 1;
    }
  });

  if (loading) {
    return (
      <div className="space-y-6">
        <Card className="border-border/50">
          <CardHeader>
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-4 w-64 mt-2" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-20" />
              ))}
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <Card className="border-destructive/50">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center text-center space-y-4 py-8">
              <div className="rounded-full bg-destructive/10 p-3">
                <AlertCircle className="h-6 w-6 text-destructive" />
              </div>
              <div>
                <h3 className="font-semibold text-sm mb-1">Erreur de chargement</h3>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
              <Button onClick={fetchLatestForecast} variant="outline" size="sm">
                Réessayer
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  if (!forecast || !forecast.data || forecast.data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        <Card className="border-border/50">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center justify-center text-center space-y-4 py-8">
              <div className="rounded-full bg-muted p-3">
                <BarChart3 className="h-6 w-6 text-muted-foreground" />
              </div>
              <div>
                <h3 className="font-semibold text-sm mb-1">Aucune prévision disponible</h3>
                <p className="text-sm text-muted-foreground max-w-md">
                  {error && error.includes('Aucune prévision trouvée') ? (
                    <>
                      Aucune prévision n'a été générée. Cela peut être dû au fait qu'aucune variété n'est actuellement en saison de plantation.
                      <br />
                      <span className="text-xs mt-2 block">Vérifiez les paramètres de saison (saison_debut / saison_fin) dans vos paramètres.</span>
                    </>
                  ) : (
                    'Générez des prévisions depuis le tableau de bord'
                  )}
                </p>
              </div>
              <div className="flex flex-col items-center gap-3">
                {seasonError && (
                  <motion.div
                    initial={{ opacity: 0, y: -8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex items-center gap-2 px-3 py-2 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm"
                  >
                    <AlertCircle className="h-4 w-4" />
                    <span>{seasonError}</span>
                  </motion.div>
                )}
                <div className="flex gap-2">
                  <Button onClick={fetchLatestForecast} variant="outline" size="sm">
                    Actualiser
                  </Button>
                  <Button 
                    onClick={generateForecast} 
                    disabled={status.scriptRunning} 
                    size="sm"
                    className="transition-default"
                  >
                    {status.scriptRunning && status.scriptMode === 'forecast' ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Génération...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Générer les prévisions
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <motion.div {...fadeIn} className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Prévisions</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Consultez et analysez vos prévisions de récolte
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          {seasonError && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2 px-3 py-2 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm"
            >
              <AlertCircle className="h-4 w-4" />
              <span>{seasonError}</span>
            </motion.div>
          )}
          <div className="flex items-center gap-2">
            {forecast?.filename && (
              <Button onClick={downloadForecast} variant="outline" size="sm" className="transition-default">
                <Download className="mr-2 h-4 w-4" />
                Télécharger
              </Button>
            )}
            <Button 
              onClick={generateForecast} 
              disabled={status.scriptRunning} 
              size="sm" 
              className="transition-default"
            >
              {status.scriptRunning && status.scriptMode === 'forecast' ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Génération...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Générer les prévisions
                </>
              )}
            </Button>
          </div>
        </div>
      </motion.div>

      {/* Filtres - Sticky en haut */}
      {forecast && (
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
                <Label className="text-xs">Date</Label>
                <Select value={selectedDate || 'all'} onValueChange={(value) => setSelectedDate(value === 'all' ? null : value)}>
                  <SelectTrigger className="transition-default">
                    <SelectValue placeholder="Toutes les dates" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les dates</SelectItem>
                    {forecast.summary.dates.map(date => (
                      <SelectItem key={date} value={date}>{formatDate(date)}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Parcelle</Label>
                <Select value={selectedParcelle || 'all'} onValueChange={(value) => setSelectedParcelle(value === 'all' ? null : value)}>
                  <SelectTrigger className="transition-default">
                    <SelectValue placeholder="Toutes les parcelles" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les parcelles</SelectItem>
                    {forecast.summary.parcelles.map(parcelle => (
                      <SelectItem key={parcelle} value={parcelle}>{parcelle}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Variété</Label>
                <Select value={selectedVariety || 'all'} onValueChange={(value) => setSelectedVariety(value === 'all' ? null : value)}>
                  <SelectTrigger className="transition-default">
                    <SelectValue placeholder="Toutes les variétés" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les variétés</SelectItem>
                    {forecast.summary.varieties.map(variety => (
                      <SelectItem key={variety} value={variety}>{variety}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
        </motion.div>
      )}

      {/* Statistiques */}
      {forecast && (
        <motion.div {...fadeIn} transition={{ delay: 0.15 }}>
          <Card className="border-border/50">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-primary" />
                Statistiques
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Total prévisions', value: forecast.summary.total_rows, icon: BarChart3 },
                  { label: 'Dates', value: forecast.summary.dates.length, icon: Calendar },
                  { label: 'Parcelles', value: forecast.summary.parcelles.length, icon: TrendingUp },
                  { label: 'Variétés', value: forecast.summary.varieties.length, icon: TrendingUp },
                ].map((stat, index) => (
                  <motion.div
                    key={stat.label}
                    className="p-3 rounded-lg bg-muted/50 border border-border/50"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05, duration: 0.15 }}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <stat.icon className="h-3.5 w-3.5 text-muted-foreground" />
                      <Label className="text-xs text-muted-foreground">{stat.label}</Label>
                    </div>
                    <p className="text-2xl font-semibold">{stat.value}</p>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Résumé par jour */}
      {Object.keys(dailyTotals).length > 0 && (
        <motion.div {...fadeIn} transition={{ delay: 0.2 }}>
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-primary" />
                Résumé par jour
              </CardTitle>
            </CardHeader>
            <CardContent>
              {/* Graphique */}
              <div className="mb-6">
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart
                    data={Object.entries(dailyTotals)
                      .sort(([a], [b]) => new Date(a) - new Date(b))
                      .map(([date, totals]) => ({
                        date: formatDateShort(date),
                        dateFull: date,
                        total: totals.total,
                        min: totals.min,
                        max: totals.max
                      }))}
                    margin={{ top: 10, right: 10, left: 0, bottom: 5 }}
                  >
                    <defs>
                      <linearGradient id="uncertaintyGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.15} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.05} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      stroke="hsl(var(--border))"
                    />
                    <YAxis 
                      tick={{ fontSize: 12, fill: 'hsl(var(--muted-foreground))' }}
                      stroke="hsl(var(--border))"
                      label={{ value: 'kg', angle: -90, position: 'insideLeft', style: { fill: 'hsl(var(--muted-foreground))' } }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '6px',
                        padding: '8px 12px'
                      }}
                      formatter={(value, name) => {
                        if (name === 'total') return [`${formatNumber(value)} kg`, 'Total prévu'];
                        if (name === 'min') return [`${formatNumber(value)} kg`, 'Min'];
                        if (name === 'max') return [`${formatNumber(value)} kg`, 'Max'];
                        return null;
                      }}
                    />
                    {/* Zone d'incertitude (min-max) */}
                    <Area
                      type="monotone"
                      dataKey="max"
                      stroke="none"
                      fill="url(#uncertaintyGradient)"
                      fillOpacity={0.3}
                      connectNulls
                      hide
                    />
                    <Area
                      type="monotone"
                      dataKey="min"
                      stroke="none"
                      fill="hsl(var(--background))"
                      fillOpacity={1}
                      connectNulls
                      hide
                    />
                    {/* Lignes pointillées pour min et max */}
                    <Line
                      type="monotone"
                      dataKey="max"
                      stroke="hsl(var(--primary))"
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      dot={false}
                      activeDot={{ r: 4 }}
                      isAnimationActive={false}
                    />
                    <Line
                      type="monotone"
                      dataKey="min"
                      stroke="hsl(var(--primary))"
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      dot={false}
                      activeDot={{ r: 4 }}
                      isAnimationActive={false}
                    />
                    {/* Barres pour le total prévu */}
                    <Bar 
                      dataKey="total" 
                      fill="hsl(var(--primary))" 
                      radius={[4, 4, 0, 0]}
                      opacity={0.9}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Tableau détaillé */}
      <motion.div {...fadeIn} transition={{ delay: 0.25 }}>
        <Card className="border-border/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Détails des prévisions</CardTitle>
                <CardDescription className="text-xs mt-1">
                  {filteredData.length} ligne{filteredData.length > 1 ? 's' : ''} affichée{filteredData.length > 1 ? 's' : ''}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="table" className="w-full">
              <TabsList className="mb-4">
                <TabsTrigger value="table" className="text-xs">Tableau</TabsTrigger>
                <TabsTrigger value="summary" className="text-xs">Résumé</TabsTrigger>
              </TabsList>
              <TabsContent value="table" className="mt-0">
                <div className="border rounded-lg overflow-hidden">
                  <div className="overflow-x-auto scrollbar-thin">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b bg-muted/30">
                          <th className="p-3 text-left text-xs font-semibold text-muted-foreground">Date</th>
                          <th className="p-3 text-left text-xs font-semibold text-muted-foreground">Parcelle</th>
                          <th className="p-3 text-left text-xs font-semibold text-muted-foreground">Variété</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Temp. moy. (°C)</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Temp. min (°C)</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Temp. max (°C)</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Pluie (mm)</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Soleil (h)</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">kg/rangée</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">kg total</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Min</th>
                          <th className="p-3 text-right text-xs font-semibold text-muted-foreground">Max</th>
                        </tr>
                      </thead>
                      <tbody>
                        <AnimatePresence>
                          {filteredData.map((row, index) => (
                            <motion.tr
                              key={index}
                              className="border-b transition-colors hover:bg-muted/30"
                              initial={{ opacity: 0 }}
                              animate={{ opacity: 1 }}
                              exit={{ opacity: 0 }}
                              transition={{ duration: 0.1 }}
                            >
                              <td className="p-3 text-xs">{formatDateShort(row.date)}</td>
                              <td className="p-3 text-xs">{row.parcelle || '–'}</td>
                              <td className="p-3 text-xs">
                                <Badge variant="outline" className="text-xs">{row.variety || '–'}</Badge>
                              </td>
                              <td className="p-3 text-xs text-right">
                                {row.temp_mean !== null && row.temp_mean !== undefined ? (
                                  <span className="flex items-center justify-end gap-1">
                                    <Thermometer className="h-3 w-3 text-orange-500" />
                                    {formatNumber(row.temp_mean)}
                                  </span>
                                ) : '–'}
                              </td>
                              <td className="p-3 text-xs text-right">
                                {row.temp_min !== null && row.temp_min !== undefined ? (
                                  <span className="flex items-center justify-end gap-1">
                                    <Thermometer className="h-3 w-3 text-blue-500" />
                                    {formatNumber(row.temp_min)}
                                  </span>
                                ) : '–'}
                              </td>
                              <td className="p-3 text-xs text-right">
                                {row.temp_max !== null && row.temp_max !== undefined ? (
                                  <span className="flex items-center justify-end gap-1">
                                    <Thermometer className="h-3 w-3 text-red-500" />
                                    {formatNumber(row.temp_max)}
                                  </span>
                                ) : '–'}
                              </td>
                              <td className="p-3 text-xs text-right">
                                {row.rain_mm !== null && row.rain_mm !== undefined ? (
                                  <span className="flex items-center justify-end gap-1">
                                    <Droplets className="h-3 w-3 text-blue-500" />
                                    {formatNumber(row.rain_mm)}
                                  </span>
                                ) : '–'}
                              </td>
                              <td className="p-3 text-xs text-right">
                                {row.sun_hours !== null && row.sun_hours !== undefined ? (
                                  <span className="flex items-center justify-end gap-1">
                                    <Sun className="h-3 w-3 text-yellow-500" />
                                    {formatNumber(row.sun_hours)}
                                  </span>
                                ) : '–'}
                              </td>
                              <td className="p-3 text-xs text-right font-medium">
                                {formatNumber(row.predicted_kg_par_rangee)}
                              </td>
                              <td className="p-3 text-xs text-right font-semibold text-primary">
                                {formatNumber(row.predicted_kg_total)}
                              </td>
                              <td className="p-3 text-xs text-right text-muted-foreground">
                                {formatNumber(row.confidence_min_kg_total)}
                              </td>
                              <td className="p-3 text-xs text-right text-muted-foreground">
                                {formatNumber(row.confidence_max_kg_total)}
                              </td>
                            </motion.tr>
                          ))}
                        </AnimatePresence>
                      </tbody>
                    </table>
                  </div>
                </div>
              </TabsContent>
              <TabsContent value="summary" className="mt-0">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  <AnimatePresence mode="popLayout">
                    {Object.entries(dailyTotals)
                      .sort(([a], [b]) => new Date(a) - new Date(b))
                      .map(([date, totals], index) => (
                      <motion.div
                        key={date}
                        className="p-5 rounded-lg border border-border/50 bg-card hover:border-primary/50 transition-colors"
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ delay: index * 0.03, duration: 0.15 }}
                      >
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-primary" />
                            <span className="text-sm font-semibold">{formatDateShort(date)}</span>
                          </div>
                          {/* Infos météo */}
                          {(totals.temp_mean !== null && totals.temp_mean !== undefined) || 
                           (totals.rain_mm !== null && totals.rain_mm !== undefined) || 
                           (totals.sun_hours !== null && totals.sun_hours !== undefined) ? (
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              {totals.temp_mean !== null && totals.temp_mean !== undefined && (
                                <div className="flex items-center gap-1" title={`Température: ${formatNumber(totals.temp_mean)}°C`}>
                                  <Thermometer className="h-3.5 w-3.5 text-orange-500" />
                                  <span className="font-medium">{formatNumber(totals.temp_mean)}°</span>
                                </div>
                              )}
                              {totals.rain_mm !== null && totals.rain_mm !== undefined && totals.rain_mm > 0 && (
                                <div className="flex items-center gap-1" title={`Pluie: ${formatNumber(totals.rain_mm)} mm`}>
                                  <Droplets className="h-3.5 w-3.5 text-blue-500" />
                                  <span>{formatNumber(totals.rain_mm)}</span>
                                </div>
                              )}
                              {totals.sun_hours !== null && totals.sun_hours !== undefined && (
                                <div className="flex items-center gap-1" title={`Soleil: ${formatNumber(totals.sun_hours)} h`}>
                                  <Sun className="h-3.5 w-3.5 text-yellow-500" />
                                  <span>{formatNumber(totals.sun_hours)}h</span>
                                </div>
                              )}
                            </div>
                          ) : null}
                        </div>
                        <div className="space-y-3">
                          <div className="flex justify-between items-baseline">
                            <span className="text-xs text-muted-foreground font-medium">Total prévu</span>
                            <Badge className="text-sm font-semibold bg-primary/10 text-primary border-primary/20">
                              {formatNumber(totals.total)} kg
                            </Badge>
                          </div>
                          <Separator />
                          <div className="space-y-2">
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Min</span>
                              <span className="font-medium">{formatNumber(totals.min)} kg</span>
                            </div>
                            <div className="flex justify-between text-xs">
                              <span className="text-muted-foreground">Max</span>
                              <span className="font-medium">{formatNumber(totals.max)} kg</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

export default ForecastView;
