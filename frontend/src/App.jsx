import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './components/ui/button';
import { BarChart3, Home, Zap, Package, Settings } from 'lucide-react';
import ForecastView from './components/ForecastView';
import HomeView from './components/HomeView';
import RecoltesView from './components/RecoltesView';
import SettingsView from './components/SettingsView';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || `${window.location.origin}/api`;

// Animations optimisées - courtes et performantes
const pageTransition = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] }
};


function App() {
  const [currentView, setCurrentView] = useState('home');
  const [status, setStatus] = useState({ lastRuns: {}, scriptRunning: false, scriptMode: null });
  const [loading, setLoading] = useState(false);
  const [appVersion, setAppVersion] = useState(null);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE}/status`);
      const newStatus = response.data;
      setStatus(prevStatus => {
        // Log uniquement si le statut change
        if (JSON.stringify(newStatus) !== JSON.stringify(prevStatus)) {
          console.log('App - Status mis à jour:', newStatus);
        }
        return newStatus;
      });
    } catch (error) {
      console.error('Erreur lors de la récupération du statut:', error);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 2000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Récupérer la version de l'application
  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await axios.get(`${API_BASE}/updates/check`);
        if (response.data.current_version) {
          setAppVersion(response.data.current_version);
        }
      } catch (error) {
        console.error('Erreur lors de la récupération de la version:', error);
      }
    };
    fetchVersion();
  }, []);

  const runScript = async (mode) => {
    console.log('App - Lancement du script:', mode);
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/run`, { mode });
      console.log('App - Réponse du serveur:', response.data);
      fetchStatus();
    } catch (error) {
      console.error('App - Erreur lors du lancement:', error);
      alert(error.response?.data?.error || 'Erreur lors du lancement du script');
      throw error; // Propager l'erreur pour que le catch dans HomeView puisse la gérer
    } finally {
      setLoading(false);
    }
  };

  const handleViewChange = (newView) => {
    setCurrentView(newView);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-background to-muted/30">
      {/* Header moderne et épuré */}
      <motion.header 
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.2 }}
        className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md supports-[backdrop-filter]:bg-background/60"
      >
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Zap className="h-4 w-4 text-primary" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-lg font-semibold tracking-tight">Pépinière Valbray</h1>
                  {appVersion && (
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium border border-primary/20">
                      v{appVersion}
                    </span>
                  )}
                </div>
                <p className="text-xs text-muted-foreground hidden sm:block">Automatisations récolte • Mise à jour automatique • Version stable</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant={currentView === 'home' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleViewChange('home')}
                className="transition-default"
              >
                <Home className="mr-2 h-4 w-4" />
                <span className="hidden sm:inline">Accueil</span>
                <span className="sm:hidden">Accueil</span>
              </Button>
              <Button
                variant={currentView === 'recoltes' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleViewChange('recoltes')}
                className="transition-default"
              >
                <Package className="mr-2 h-4 w-4" />
                Récoltes
              </Button>
              <Button
                variant={currentView === 'forecasts' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleViewChange('forecasts')}
                className="transition-default"
              >
                <BarChart3 className="mr-2 h-4 w-4" />
                Prévisions
              </Button>
              <Button
                variant={currentView === 'settings' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleViewChange('settings')}
                className="transition-default"
              >
                <Settings className="mr-2 h-4 w-4" />
                Paramètres
              </Button>
            </div>
          </div>
        </div>
      </motion.header>

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <AnimatePresence mode="wait">
          {currentView === 'home' ? (
            <motion.div
              key="home"
              {...pageTransition}
            >
              <HomeView 
                onRunScript={runScript}
                status={status}
                loading={loading}
              />
            </motion.div>
          ) : currentView === 'recoltes' ? (
            <motion.div
              key="recoltes"
              {...pageTransition}
            >
              <RecoltesView />
            </motion.div>
          ) : currentView === 'forecasts' ? (
            <motion.div
              key="forecasts"
              {...pageTransition}
            >
              <ForecastView />
            </motion.div>
          ) : (
            <motion.div
              key="settings"
              {...pageTransition}
            >
              <SettingsView />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;
